import json
from typing import NamedTuple

from django.contrib.auth.decorators import login_required
from django.contrib.humanize.templatetags.humanize import apnumber
from django.db import IntegrityError
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST

from access.consent import consent_required
from engine.document import (
    BLOCK_TYPES,
    LONG_TEXT_MAX_LENGTH,
    SCALE_POINTS,
    AnswerRefused,
    UnknownBlock,
    answer_from_form,
    answerable_block,
    authored_text,
    checklist,
    text_for,
    unmet,
)
from engine.document.blocks import CONTACTS, blocks_of, break_after, page_count, page_of, pages_of, section_of
from engine.document.coach import (
    candidate_name_from_form,
    checklist_answers,
    checklist_answers_from_form,
    checklist_outcome,
    coach_details_as_typed,
    coach_from_form,
)
from engine.document.contacts import (
    MAX_CONTACTS,
    contact_id_per_row,
    contacts_from_form,
    rows_as_typed,
    rows_posted,
    rows_to_show,
)
from engine.document.aggregation import aggregate
from engine.document.gates import has_content
from engine.document.scoring import score
from engine.hub import (
    block_ids_fixed_on_completion,
    hub_for,
    is_locked,
    open_blocks,
    page_reached,
    section_by_id,
    track_sections,
)
from engine.document.observers import link_lifetime, privacy_notice
from engine.models import Contact, Invitation, ObserverResponse, PathwayVersion, Publication, Response, Result
from engine.results import comparison_page, results_page


class ParticipantState(NamedTuple):
    """✨ Everything stored for one participant: their response (None before their first answer), the pathway version
    it answers and that version's track sections, and its state: answers, sections completed, pages moved past by
    section, and the blocks whose answers are fixed."""

    response: Response | None
    version: PathwayVersion | None
    sections: list
    answers: dict
    completed: set
    moved_past: dict
    fixed: set

    def reached(self, section):
        """✨ The page of a section this participant has reached, or None while the section is locked. Every way into
        a section (its address, "Continue →", completion, an answer or a checklist step) is guarded by this."""
        if is_locked(section, self.completed):
            return None
        return page_reached(section, self.moved_past, self.answers, self.sections)

    def stored_response(self, user):
        """✨ Their response, begun now if this is the first thing they store."""
        if self.response is not None:
            return self.response
        return Response.objects.get_or_create(participant=user, version=self.version)[0]


@login_required
@consent_required
def hub(request):
    """✨ Where the participant always starts: their track's sections, their status, and the next step."""
    state = _participant(request.user)
    if state.version is None:
        return render(request, "engine/hub.html", {})
    if not any(section["blocks"] for section in state.sections):
        return render(request, "engine/hub.html", {})  # ✨ no content is the empty state, never a fallback
    return render(
        request,
        "engine/hub.html",
        {
            "title": text_for(state.version.document["title"], "participant"),
            "hub": hub_for(state.sections, state.answers, state.completed, moved_past=state.moved_past),
        },
    )


@login_required
@consent_required
def start(request):
    """✨ Where agreeing to consent leads. A participant with nothing saved goes straight to their first step,
    as the prototype goes from its account screen into onboarding; anyone who has begun goes to the hub."""
    state = _participant(request.user)
    if state.response is not None or state.version is None:
        return redirect("hub")
    next_step = hub_for(state.sections, state.answers, state.completed).next_step
    if next_step is None or not any(section["blocks"] for section in state.sections):
        return redirect("hub")  # ✨ the hub's empty state says there is nothing to begin
    return redirect("section", next_step.id)


@login_required
@consent_required
def section(request, section_id, page=1):
    """✨ One page of a section's blocks. A locked section, or a page not yet reached, is refused here, whatever the
    participant typed in the bar: a page ahead of the one reached leads back to that one."""
    state = _participant(request.user)
    section = _section_or_404(state.version, section_id)
    reached = state.reached(section)
    if reached is None:
        return redirect("hub")
    _page_or_404(section, page)
    if page > reached:
        return redirect(page_url(section_id, reached))
    return render(request, "engine/section.html", _section_page(state, section, page, _asked_rows(request.GET)))


@login_required
@consent_required
@require_POST
def move_past_page(request, section_id, page):
    """✨ "Continue →" from one page of a section to the next, allowed exactly when the page offers it: once that page's
    clauses pass and nothing on the way to it (an unconfirmed reading, a held link) holds what follows. Re-checked here
    rather than trusted to the page. The last page has no way on but completing the section."""
    state = _participant(request.user)
    section = _section_or_404(state.version, section_id)
    reached = state.reached(section)
    if reached is None:
        return redirect("hub")
    if _page_or_404(section, page) == page_count(section):
        raise Http404("The last page of a section is moved past by completing it.")
    if page > reached:
        return _see_other(page_url(section_id, reached))
    shown = _section_page(state, section, page)
    if not shown["offers_way_on"] or shown["unmet"]:
        return render(request, "engine/section.html", {**shown, "refused": True}, status=400)

    state.stored_response(request.user).move_past_page(section_id, page)
    return _see_other(page_url(section_id, page + 1))


@login_required
@consent_required
@require_POST
def complete_section(request, section_id):
    """✨ The participant's own act of finishing a section, re-checked here rather than trusted to the page. It is
    done from the section's last page, so a participant who has not reached it is sent to the page they have."""
    state = _participant(request.user)
    section = _section_or_404(state.version, section_id)
    reached = state.reached(section)
    if reached is None:
        return redirect("hub")
    last = page_count(section)
    if reached < last:
        return _see_other(page_url(section_id, reached))
    if unmet(section, state.answers):
        shown = _section_page(state, section, last)
        return render(request, "engine/section.html", {**shown, "refused": True}, status=400)

    fixed_block_ids = block_ids_fixed_on_completion(section, state.answers)
    state.stored_response(request.user).complete_section(section_id, fixed_block_ids=fixed_block_ids)
    # ✨ On to whatever the hub would now point at, as the prototype moves from screen to screen; the hub once
    # nothing is left.
    completed = state.completed | {section_id}
    next_step = hub_for(state.sections, state.answers, completed, moved_past=state.moved_past).next_step
    return _see_other(page_url(next_step.id, next_step.page)) if next_step else _see_other("hub")


@login_required
@consent_required
@require_POST
def reopen_section(request, section_id):
    """✨ The participant taking back their own completion. Their answers stay exactly as they left them."""
    state = _participant(request.user)
    _section_or_404(state.version, section_id)
    if state.response is not None:
        state.response.reopen_section(section_id)
    return _see_other("hub")


@login_required
@consent_required
@require_POST
def save_answer(request, block_id):
    """✨ Autosave: validate and store one block's answer against the participant's pathway version.

    A participant with a response answers its version. A first answer is recorded against the version
    the page was rendered from, so a version published while they were typing never captures it.
    """
    state = _participant(request.user, first_version=lambda: _published_version(request.POST.get("version")))
    if state.version is None:
        raise Http404("No published pathway version was named.")
    try:
        block = answerable_block(state.version.document, block_id)
    except UnknownBlock:
        raise Http404("This pathway version has no block by that identifier that takes an answer.")
    # ✨ A block a participant has not reached is as shut as the page that would have shown it, whether a
    # lock or an unconfirmed reading holds it. Otherwise they could fill it in without ever opening it, and
    # both would be decoration again, which is exactly the prototype's mistake.
    section = section_of(state.version.document, block_id)
    if not _is_open(state, section, block):
        return render(request, "engine/save_status.html", {"refusal": "This is not open yet."}, status=403)
    if block_id in state.fixed:
        # ✨ Refused here, not only disabled on the page, so a page left open from before completing cannot change it.
        return _refuse_fixed(request)
    block_type = BLOCK_TYPES[block["type"]]
    try:
        if block_type.captures is CONTACTS:
            names, emails = request.POST.getlist("name"), request.POST.getlist("email")
            value = contacts_from_form(names, emails, request.POST.getlist("contact"))
        else:
            value = answer_from_form(state.version.document, block, request.POST.get("value"))
    except AnswerRefused as refused:
        context = {"refusal": str(refused), "invalid_row": refused.row, "invalid_field": refused.field}
        if block_type.captures is CONTACTS and request.POST.get("next") == "invitations":
            # ✨ That list is not autosaved, so there is no status line to put this in: the page comes back instead,
            # with the list as typed.
            typed = {"rows": rows_as_typed(names, emails, request.POST.getlist("contact")), **context}
            return _invitations_page(request, refused={block_id: typed}, status=400)
        return render(request, "engine/save_status.html", context, status=400)

    participant_response = state.stored_response(request.user)
    # ✨ The row is updated in place, so the answers read before are a step behind what is about to be stored.
    saved = state._replace(answers={**state.answers, block_id: value})
    if block_type.captures is CONTACTS:
        saved_contacts = participant_response.replace_contacts(block_id, value, Contact.Role.CONTACT)
        if request.POST.get("next") == "invitations":
            return _see_other(f"{reverse('invitations')}{_rows_query(request.POST)}")
        # ✨ main.js puts these back into the rows, so the next autosave from the same page edits the people this one
        # kept rather than adding them again.
        saved_ids = [contact.pk for contact in saved_contacts]
        contact_ids = contact_id_per_row(value, saved_ids, rows_posted(names, emails))
        return _saved(request, saved, section, block_id, contact_ids)
    if block_type.scored:
        try:
            participant_response.submit_sort(block_id, value, score(state.version.document, value))
        except IntegrityError:
            refusal = "Your results are already in. Retaking the sort is not offered yet."
            return render(request, "engine/save_status.html", {"refusal": refusal}, status=409)
        return _to_results(request, block_id)
    if not participant_response.save_answer(block_id, value):
        return _refuse_fixed(request)  # ✨ a completion fixed it after the check above, and the UPDATE saw that
    return _saved(request, saved, section, block_id)


@sensitive_post_parameters()
@login_required
@consent_required
@require_POST
def coach_checklist(request, block_id):
    """✨ One step of choosing a coach: from the intro to the questions, to an outcome, or back to the start; and
    saving the coach chosen, or removing them.

    Nothing from the checklist is stored or logged. The candidate's name and the answers so far travel only in the
    form, screen to screen, and the outcome is worked out again from what was posted, never taken from the button
    pressed. The answers are opinions about another person, including their faith (special category data under
    GDPR), and no later step reads them; `sensitive_post_parameters` keeps them out of error reports too. Saving
    keeps only the chosen coach's name and email address, as a contact, and only once the outcome allows it.
    """
    state = _participant(request.user)
    block = _block_of_type(state.version, block_id, "coach_checklist")
    section = section_of(state.version.document, block_id)
    if not _is_open(state, section, block):
        return render(request, "engine/save_status.html", {"refusal": "This is not open yet."}, status=403)
    to = request.POST.get("step")
    if to not in CHECKLIST_STEPS:
        return HttpResponseBadRequest("The coach checklist has no such step.")

    screen = _checklist_step(block, to, request.POST, _coach_kept(state.answers, block_id))
    kept = state.answers
    if to == "save" and screen["screen"] == "chosen":
        state.stored_response(request.user).replace_contacts(block_id, [screen["coach"]], Contact.Role.COACH)
        kept = {**kept, block_id: [screen["coach"]]}
    elif to == "remove" and state.response is not None:
        state.response.replace_contacts(block_id, [], Contact.Role.COACH)
        kept = {key: value for key, value in kept.items() if key != block_id}
    # ✨ A save the outcome does not allow is refused, though its screen (a stop, say) has nothing to add.
    refused = screen.get("refusal") or (to == "save" and screen["screen"] != "chosen")
    status = 400 if refused else 200
    stored = status == 200 and to in ("save", "remove")
    page = page_of(section, block_id)
    is_htmx = request.headers.get("HX-Request") == "true"
    if not is_htmx and stored:
        # ✨ Once stored, the checklist is behind: the page shows only the coach kept, so it is safe to go back to.
        return _see_other(f"{page_url(section['id'], page)}#block-{block_id}")
    shown = _section_page(state._replace(answers=kept), section, page)
    checklist_block = next(on_page for on_page in shown["section"]["blocks"] if on_page["id"] == block_id)
    checklist_block["checklist"] = _checklist_screen(checklist_block["text"], **screen)
    if is_htmx:
        # ✨ Keeping or removing a coach can change the page's way on (a skip label), so it comes too, as after an
        # autosave; stepping through the checklist changes nothing stored, so the way on stays as it was.
        context = {**shown, "block": checklist_block, "stored": stored}
        return render(request, "engine/coach_checklist_result.html", context, status=status)
    # ✨ Never a redirect without JavaScript while choosing: the answers would have to go in the address, where they
    # are logged. The page returned is the one the checklist is on.
    return render(request, "engine/section.html", shown, status=status)


# ✨ The buttons of the coach checklist: back to the intro keeping what was given, on to the questions, to see how
# it looks, "I'm still confident" past a second thought, starting again with someone else, saving the coach chosen,
# removing them, and keeping the coach already chosen after all.
CHECKLIST_STEPS = ("intro", "questions", "outcome", "confident", "restart", "save", "remove", "keep")


def _checklist_step(block, to, posted, coach_kept=None):
    """✨ Where a press of the checklist's button leads, from what its form held and the coach already kept (if any),
    as the screen's state. A coach saved, or kept after all, is "chosen", with the coach; an intro while a coach is
    kept says so."""
    questions = block["questions"]
    if to == "keep" and coach_kept:
        return {"screen": "chosen", "coach": coach_kept}
    if to == "remove":
        return {"screen": "intro"}
    if to in ("restart", "keep"):
        return {"screen": "intro", "kept": coach_kept}
    name, given = (posted.get("name") or "").strip(), checklist_answers(questions, posted)
    if to == "intro":
        return {"screen": "intro", "name": name, "answers": given, "kept": coach_kept}
    if to != "save":  # ✨ on the coach's details, the name is checked with their email, where it can be put right
        try:
            name = candidate_name_from_form(posted)
        except AnswerRefused as refused:
            return {"screen": "intro", "name": name, "answers": given, "refusal": str(refused), "kept": coach_kept}
    if to == "questions":
        return {"screen": "questions", "name": name, "answers": given}
    try:
        given = checklist_answers_from_form(questions, posted)
    except AnswerRefused as refused:
        return {"screen": "questions", "name": name, "answers": given, "refusal": str(refused)}
    outcome = checklist_outcome(questions, given)
    if outcome.verdict == "stop" or (outcome.verdict == "confirm" and to == "outcome"):
        return {"screen": outcome.verdict, "name": name, "answers": given, "outcome": outcome}
    # ✨ Going ahead: all Yes, or "I'm still confident" past a second thought.
    going_ahead = {"screen": "proceed", "name": name, "answers": given, "confident": bool(outcome.flagged)}
    if to != "save":
        return going_ahead
    try:
        return {"screen": "chosen", "coach": coach_from_form(posted)}
    except AnswerRefused as refused:
        return {**going_ahead, **coach_details_as_typed(posted), "refusal": str(refused), "invalid": refused.field}


def _checklist_screen(
    text,
    screen="intro",
    name="",
    answers=None,
    outcome=None,
    refusal=None,
    confident=False,
    coach=None,
    email="",
    confirmed=False,
    invalid=None,
    kept=None,
):
    """✨ One screen of the coach checklist as its template needs it: the questions with any answers given, and on
    a second thought or a stop, each answer that was not Yes with why that question matters. On going ahead, the
    coach's details as typed, and which of them a refusal is about; once chosen, the coach kept. On the intro while
    choosing again, `kept` is the coach who stays until another is saved."""
    answers = answers or {}
    questions = [{**question, "answer": answers.get(question["id"])} for question in text["questions"]]
    flagged = set(outcome.flagged) if outcome else set()
    return {
        "screen": screen,
        "name": name,
        "answers": answers,
        "questions": questions,
        "count": apnumber(len(questions)),
        "flags": [question for question in questions if question["id"] in flagged],
        "critical_no": bool(outcome and outcome.critical_no),
        "confident": confident,
        "refusal": refusal,
        "coach": coach,
        "email": email,
        "confirmed": confirmed,
        "invalid": invalid,
        "kept": kept,
    }


def _coach_kept(answers, block_id):
    """✨ The coach kept for a coach checklist, as {"name", "email"}, or None: its answer is the one coach kept."""
    kept = answers.get(block_id)
    return kept[0] if kept else None


def _saved(request, state, section, block_id, contact_ids=None):
    """✨ What a stored answer sends back: with htmx, the status and its page's gate; without, its page again.

    A contact list's "add another" without JavaScript saves the list and asks for one more row than it showed,
    which the page then shows.
    """
    page = page_of(section, block_id)
    if request.headers.get("HX-Request") == "true":
        shown = _section_page(state, section, page)
        return render(request, "engine/save_result.html", {**shown, "contact_ids": contact_ids})
    return _see_other(f"{page_url(section['id'], page)}{_rows_query(request.POST)}#block-{block_id}")


def _rows_query(posted):
    """✨ The address's query for the rows "add another" asked for without JavaScript, or nothing."""
    rows = _asked_rows(posted)
    return f"?rows={rows}" if rows else ""


@login_required
@consent_required
def results(request, block_id):
    """✨ The participant's own stored result for a scored block, never recomputed and never anyone else's.

    Before there is a result, the participant is sent to the page of the block's section the sort is on. After, the
    page leads back there too, since that is where the section is completed.
    """
    state, result, section = _own_result(request.user, block_id)
    if result is None:
        return redirect(page_url(section["id"], section["page"]))
    shown = results_page(state.version.document, result.scores, state.answers[block_id], request.user.get_username())
    shown["section"] = section
    shown["block_id"] = block_id
    _prototype_bars(request, state.version.document, shown)
    return render(request, "engine/results.html", shown)


def _prototype_bars(request, document, shown):
    """✨ PROTOTYPE, throwaway (branch prototype/result-bars): the `?variant=` drawings, while DEBUG is on."""
    from django.conf import settings

    from engine import prototype_bars

    variant = prototype_bars.variant_from(request, settings.DEBUG)
    if variant is None:
        return
    shown["variant"] = variant
    shown["switcher"] = prototype_bars.switcher(variant, request.path)
    if shown.get("frameworks"):
        prototype_bars.draw(document, shown["frameworks"])


@login_required
@consent_required
def comparison(request, block_id):
    """✨ The participant's self-result beside the observer average (ADR 0005), reached from the results page and, like
    it, open to anyone with a result, whatever sections they have done. Below the minimum it shows how many have
    answered and no numbers; it never shows which person has answered, and single observers' percents only in the
    distribution strip, in ascending order."""
    state, result, section = _own_result(request.user, block_id)
    if result is None:
        return redirect(page_url(section["id"], section["page"]))
    document = state.version.document
    assessments = ObserverResponse.assessments_for(state.response)
    observer_average = aggregate(document, assessments.assessments)
    shown = comparison_page(document, result.scores, state.answers[block_id], observer_average)
    # ✨ Below the minimum there is no comparison on the page to call illustrative.
    shown["illustrative"] = assessments.all_test_data and shown["frameworks"] is not None
    shown["block_id"] = block_id
    _prototype_bars(request, document, shown)
    return render(request, "engine/comparison.html", shown)


@login_required
@consent_required
@require_POST
def visit_comparison(request, block_id):
    """✨ The results page's "Compare with how others see you →": record the visit Section 1's gate waits on, then go to
    the comparison. Recorded whatever the comparison will show, since the explanation below the minimum counts too
    (ticket 16c). Only this press counts, never loading the comparison's address, which a browser may do ahead of
    time (Chrome preloads from the address bar) without the participant ever seeing it."""
    state, result, section = _own_result(request.user, block_id)
    if result is None:
        return _see_other(page_url(section["id"], section["page"]))
    state.response.visit_comparison(block_id)
    # ✨ PROTOTYPE, throwaway (branch prototype/result-bars): keep the `?variant=` drawing on the way through.
    variant = request.GET.get("variant", "")
    query = f"?variant={variant}" if variant.isalnum() else ""
    return _see_other(f"{reverse('comparison', args=[block_id])}{query}")


def _own_result(user, block_id):
    """✨ The participant's state, their stored result for a scored block (None before they have one), and the section
    the sort is on with its page. A block that is not scored is a 404."""
    state = _participant(user)
    try:
        block = answerable_block(state.version.document, block_id) if state.version else None
    except UnknownBlock:
        block = None
    if block is None or not BLOCK_TYPES[block["type"]].scored:
        raise Http404("This pathway version has no scored block by that identifier.")
    section = section_of(state.version.document, block_id)
    result = Result.objects.filter(response=state.response, block_id=block_id).first()
    shown_section = {
        "id": section["id"],
        "title": text_for(section["title"], "participant"),
        "page": page_of(section, block_id),
    }
    return state, result, shown_section


@login_required
@consent_required
def invitations(request):
    """✨ The people on the participant's contact list, each with a link to act as an observer (ADR 0005). A link just
    issued is shown this once, from the cookie issuing left, which goes as it is read; a reload shows none."""
    issued = _issued_link(request)
    shown = _invitations_page(request, issued=issued)
    shown["Cache-Control"] = "no-store"
    if issued is not None:
        shown.delete_cookie(ISSUED_COOKIE, path=reverse("invitations"))
    return shown


@login_required
@consent_required
@require_POST
def issue_invitation(request, contact_id):
    """✨ Issue, or reissue, one contact's link, then go back to the invitations page at that person, which shows it
    this once: only its hash is kept.

    A redirect, so a reload of the page that follows never issues again. The link travels to that page in a short-lived
    signed cookie of the participant's own, not in the address (where the history would keep it) or the session (where
    the database would).
    """
    contact = _own_contact_or_404(request.user, contact_id)
    token = Invitation.issue(contact, link_lifetime(contact.response.version.document))
    link = request.build_absolute_uri(reverse("observe", args=[token]))
    back = _see_other(f"{reverse('invitations')}#person-{contact.pk}")
    back.set_signed_cookie(
        ISSUED_COOKIE,
        json.dumps({"contact": contact.pk, "link": link}),
        salt=ISSUED_COOKIE,
        max_age=ISSUED_COOKIE_SECONDS,
        path=reverse("invitations"),
        secure=request.is_secure(),
        httponly=True,
        samesite="Lax",
    )
    return back


# ✨ Where a link just issued waits for the page that shows it, and for how long at most.
ISSUED_COOKIE = "issued_link"
ISSUED_COOKIE_SECONDS = 60


def _issued_link(request):
    """✨ The link just issued, as {"contact", "link"}, or None: none was, or its cookie is stale or not ours."""
    signed = request.get_signed_cookie(ISSUED_COOKIE, default=None, salt=ISSUED_COOKIE, max_age=ISSUED_COOKIE_SECONDS)
    return json.loads(signed) if signed else None


@login_required
@consent_required
@require_POST
def revoke_invitation(request, contact_id):
    """✨ Stop one contact's link. Revoking one that is already gone does nothing. The page comes back at that person."""
    contact = _own_contact_or_404(request.user, contact_id)
    Invitation.objects.filter(contact=contact).delete()
    return _see_other(f"{reverse('invitations')}#person-{contact.pk}")


def observe(request, token):
    """✨ Where an observer's link leads: before it is claimed, the privacy notice and the way to start; after, word
    that it has been used. Opening it claims nothing. The observer's own link, claimed from it, leads to their page.
    A wrong, expired or revoked link gets one refusal, the same for all three, naming nobody.

    Observers have no account: nothing here reads or writes the signed-in user, if there is one.
    """
    invitation = Invitation.live(token)
    if invitation is None:
        return _observers_page(request, token, came_by_link=True)  # ✨ an observer's own link, or the refusal
    if invitation.claimed_at is not None:
        return render(request, "engine/link_used.html", status=410)
    document, name = _asked_by(invitation)
    shown = render(
        request,
        "engine/observer_landing.html",
        {"notice": privacy_notice(document, name), "name": name, "token": token},
    )
    shown["Cache-Control"] = "no-store"
    return shown


@require_POST
def start_observing(request, token):
    """✨ The observer's "I'm answering for Sam": the claim. Their own link is shown this once, straight back rather
    than by redirect so it never sits in the history, and kept in a cookie so they need not follow it; the
    participant's copy is used up. A second claim is told the link has been used, so whoever claimed first is
    noticed, not hidden.

    Only the claim sets the cookie, never a plain visit: this is a POST that carries a CSRF token, so no other site
    can put someone else's claim in an observer's browser by sending it to a link.
    """
    secret = Invitation.claim(token)
    if secret is None:
        if Invitation.live(token) is not None:
            return render(request, "engine/link_used.html", status=410)
        return _refuse_link(request)
    invitation = Invitation.claimed_by(secret)
    own_link = request.build_absolute_uri(reverse("observe", args=[secret]))
    shown = _observers_page(request, secret, own_link=own_link)
    if invitation is not None:
        shown.set_cookie(
            OBSERVER_COOKIE,
            secret,
            expires=invitation.expires_at,
            path=reverse("observer"),
            secure=request.is_secure(),
            httponly=True,
            samesite="Lax",
        )
    return shown


def observer(request):
    """✨ The observer's own page, reached by the cookie their claim left."""
    return _observers_page(request, request.COOKIES.get(OBSERVER_COOKIE))


@require_POST
def send_assessment(request, token=None):
    """✨ The observer sending their observer assessment, once, with the secret they claimed: from their own link
    (`token`), or else from the cookie. It counts at once, and nothing of it is ever shown back. The participant's copy
    of the link is not a secret, so it is refused here as any wrong link is. Then back to the page it was sent from,
    which now says thank you.

    A second send from the same secret is refused, and the first stands. A reissued link is a new claim, so its observer
    may send one too, and both count (ADR 0007).
    """
    if token is None:
        secret, back = request.COOKIES.get(OBSERVER_COOKIE), reverse("observer")
    else:
        secret, back = token, reverse("observe", args=[token])
    invitation = Invitation.claimed_by(secret)
    if invitation is None:
        return _refuse_link(request)
    document, _ = _asked_by(invitation)
    scored = _scored_block(document)
    if scored is None:
        raise Http404("This pathway has no assessment for observers.")
    try:
        assessment = answer_from_form(document, scored, request.POST.get("value"))
    except AnswerRefused as refused:
        return render(request, "engine/save_status.html", {"refusal": str(refused)}, status=400)
    try:
        ObserverResponse.send(invitation.contact.response, secret, assessment)
    except IntegrityError:
        refusal = "Your assessment has already been sent."
        return render(request, "engine/save_status.html", {"refusal": refusal}, status=409)
    return _go_to(request, back)


# ✨ Where an observer's own secret is kept, so the observer's pages know them without a link or an account. It
# holds one claim: claiming a second link, for someone else, replaces the first, whose own link still works.
OBSERVER_COOKIE = "observer"


def _observers_page(request, secret, own_link=None, came_by_link=False):
    """✨ The observer's page for the invitation a secret claimed, or the refusal if there is none: the observer
    assessment until it is sent, then thanks. `own_link` is their link, shown only as they claim it. An observer who
    `came_by_link` rather than by the cookie sends the assessment through that link. Never cached, since it is reached
    by a secret."""
    invitation = Invitation.claimed_by(secret)
    if invitation is None:
        return _refuse_link(request)
    document, name = _asked_by(invitation)
    scored = _scored_block(document)
    sent = ObserverResponse.sent_with(secret)
    assessment = None
    if scored and not sent:
        assessment = {
            "id": scored["id"],
            "widget": BLOCK_TYPES[scored["type"]].widget(document, "observer", name),
            "action": reverse("send_assessment_by_link", args=[secret]) if came_by_link else reverse("send_assessment"),
        }
    context = {"name": name, "own_link": own_link, "assessment": assessment, "sent": sent}
    shown = render(request, "engine/observer.html", context)
    shown["Cache-Control"] = "no-store"
    return shown


def _scored_block(document):
    """✨ The document's scored block, whose assessment observers make about the participant so it can be set beside
    the participant's own, or None for a document without one."""
    return next((block for block in blocks_of(document) if BLOCK_TYPES[block["type"]].scored), None)


def _refuse_link(request):
    """✨ The one refusal for a wrong, expired or revoked link, or an observer's own link or cookie that no longer
    works: the same for all, naming nobody."""
    return render(request, "engine/link_refused.html", status=404)


def _asked_by(invitation):
    """✨ The pathway document an invitation belongs to, and the name of the participant who asked. Accounts hold no
    name yet, so it is their username, as on the results page."""
    participant_response = invitation.contact.response
    return participant_response.version.document, participant_response.participant.get_username()


def _invitations_page(request, issued=None, refused=None, status=200):
    """✨ The invitations page. `issued` is a link just issued, shown this once; `refused` is a contact list whose
    save was refused, keyed by block, with its rows as typed and why, shown in place of what is stored."""
    state = _participant(request.user)
    contacts = Contact.objects.none()
    if state.response is not None:
        contacts = (
            state.response.contacts.filter(role=Contact.Role.CONTACT)
            .select_related("invitation")
            .order_by("block_id", "position")
        )
    people = [{"contact": contact, "invitation": _live_invitation(contact)} for contact in contacts]
    contact_lists = _contact_lists_to_edit(state, request.GET, refused or {})
    shown = {"people": people, "issued": issued, "contact_lists": contact_lists}
    if state.version is not None:
        shown["pathway"] = {"version_id": state.version.pk, "max_contacts": MAX_CONTACTS}
    return render(request, "engine/invitations.html", shown, status=status)


def _contact_lists_to_edit(state, query, refused):
    """✨ The pathway's contact lists the participant can change here, as their template needs them: those they have
    reached, so one skipped in onboarding can be filled in now, and not fixed by a completion. A list whose save was
    refused shows as typed, with why."""
    if state.version is None:
        return []
    document = state.version.document
    return [
        {
            **_block_for_participant(document, block, state.answers, state.fixed, {}, _asked_rows(query)),
            **refused.get(block["id"], {}),
        }
        for block in blocks_of(document)
        if block["type"] == "contact_list"
        and block["id"] not in state.fixed
        and _is_open(state, section_of(document, block["id"]), block)
    ]


def _live_invitation(contact):
    """✨ The contact's invitation while its link still works, or None."""
    try:
        invitation = contact.invitation
    except Invitation.DoesNotExist:
        return None
    return invitation if invitation.expires_at > timezone.now() else None


def _own_contact_or_404(user, contact_id):
    """✨ One of this participant's own contacts (not their coach, whose link is ticket 13c's), or a 404 that says
    nothing about whether anyone else has a contact by that number."""
    contact = (
        Contact.objects.select_related("response__version")
        .filter(pk=contact_id, response__participant=user, role=Contact.Role.CONTACT)
        .first()
    )
    if contact is None:
        raise Http404("You have no contact by that number.")
    return contact


def page_url(section_id, page=1):
    """✨ The address of one page of a section. The first is the section's own address, as before it had pages.
    Templates reach it as the `page_url` tag (`engine/templatetags/section_pages.py`)."""
    if page == 1:
        return reverse("section", args=[section_id])
    return reverse("section_page", args=[section_id, page])


def _see_other(where, *args):
    """✨ After a POST, the browser should GET the page it lands on rather than repeat the POST."""
    response = redirect(where, *args)
    response.status_code = 303
    return response


def _to_results(request, block_id):
    """✨ A scored answer's next page is its result."""
    return _go_to(request, reverse("results", args=[block_id]))


def _go_to(request, where):
    """✨ After an assessment is sent, the page it leads to. htmx is told to go there rather than swap anything in."""
    if request.headers.get("HX-Request") == "true":
        return HttpResponse(headers={"HX-Redirect": where})
    return _see_other(where)


def _participant(user, first_version=Publication.current_version):
    """✨ Everything stored for this participant, as a `ParticipantState`.

    A participant without a response yet reads `first_version()`: by default the published version, so what they
    see is what their first answer will be recorded against.
    """
    participant_response = Response.in_progress(user)
    if participant_response is None:
        version = first_version()
        sections = track_sections(version.document) if version else []
        return ParticipantState(None, version, sections, {}, set(), {}, set())
    return ParticipantState(
        response=participant_response,
        version=participant_response.version,
        sections=track_sections(participant_response.version.document),
        answers=participant_response.answers_with_contacts_and_visits(),
        completed=set(participant_response.completed_sections),
        moved_past=participant_response.moved_past_by_section(),
        fixed=set(participant_response.fixed_answers),
    )


def _is_open(state, section, block):
    """✨ Whether a participant has reached a block: its section is not locked, its page has been reached, and no
    unconfirmed reading or held link above it holds it shut."""
    reached = state.reached(section)
    if reached is None:
        return False
    blocks, _ = open_blocks(section, state.answers, state.sections, up_to_page=reached)
    return block in blocks


def _page_or_404(section, page):
    if not 1 <= page <= page_count(section):
        raise Http404("This section has no page by that number.")
    return page


def _refuse_fixed(request):
    refusal = "This answer was fixed when you completed this section."
    return render(request, "engine/save_status.html", {"refusal": refusal}, status=409)


def _block_of_type(version, block_id, block_type):
    """✨ The version's block by that identifier, provided it is of that type; otherwise a 404."""
    for block in blocks_of(version.document) if version else ():
        if block["id"] == block_id and block["type"] == block_type:
            return block
    raise Http404(f"This pathway version has no {block_type} by that identifier.")


def _section_or_404(version, section_id):
    section = section_by_id(version.document, section_id) if version else None
    if section is None:
        raise Http404("This pathway version has no section by that identifier.")
    return section


def _asked_rows(query):
    """✨ How many rows a contact list's "add another" asked for without JavaScript, or 0. Capped when shown."""
    asked = query.get("rows", "")
    return min(int(asked), MAX_CONTACTS) if asked.isdigit() else 0


def _section_page(state, section, page=1, asked_rows=0):
    """✨ One page of a section as its template needs it. Every page but the last ends in "Continue →", held by that
    page's own clauses; the last ends in the section's completion, held by the whole gate."""
    version, answers, fixed = state.version, state.answers, state.fixed
    opened, activity_open = open_blocks(section, answers, state.sections, up_to_page=page)
    on_page = {block["id"] for block in pages_of(section)[page - 1]}
    blocks = [block for block in opened if block["id"] in on_page]
    is_last = page == page_count(section)
    # ✨ A sort leads only to its results, as in the prototype, so completing is not offered beside it until it
    # is in. The linter makes its section's gate require it, so the server refuses completion before then too.
    sort_pending = any(BLOCK_TYPES[block["type"]].scored and block["id"] not in answers for block in blocks)
    # ✨ A link shows the section it leads to exactly as the hub would: its title, its status and whether it is open.
    hub = hub_for(state.sections, answers, state.completed, moved_past=state.moved_past)
    gate_checklist = checklist(section, answers, page=page)
    states = {other.id: other for other in hub.sections}
    return {
        "page": {
            "number": page,
            "is_last": is_last,
            "skip_label": _skip_label(section, page, answers),
            "continue_label": _continue_label(section, page, answers),
        },
        "pathway": {
            "version_id": version.pk,
            "scale_points": SCALE_POINTS,
            "long_text_max_length": LONG_TEXT_MAX_LENGTH,
            "max_contacts": MAX_CONTACTS,
        },
        "section": {
            "id": section["id"],
            "title": text_for(section["title"], "participant"),
            "estimate": states[section["id"]].estimate,
            "complete_label": text_for(section.get("complete_label", "Mark complete"), "participant"),
            "blocks": [
                _block_for_participant(version.document, block, answers, fixed, states, asked_rows) for block in blocks
            ],
        },
        "is_complete": section["id"] in state.completed,
        # ✨ Over the whole section, since the ratings it fixed may be on an earlier page than its completion.
        "holds_fixed_answers": any(block["id"] in fixed for block in section["blocks"]),
        # ✨ The way on, "Continue →" or completion. Going on from a page is refused on exactly these and `unmet`.
        "offers_way_on": activity_open and not sort_pending,
        # ✨ What the checklist marks unmet: on the last page, where completing checks it, the whole gate.
        "unmet": [message for message, met in gate_checklist if not met],
        "checklist": gate_checklist,
    }


def _skip_label(section, page, answers):
    """✨ The way on from a page as its break words it for passing by, such as the original prototype's "I'll sort this
    later →", while nothing on the page holds an answer; otherwise None, and the way on is "Continue →". A coach
    checklist's answer is the coach kept, so choosing one turns the skip into "Continue →"."""
    ends_in = break_after(section, page)
    if ends_in is None or "skip_label" not in ends_in:
        return None
    if any(has_content(answers.get(block["id"])) for block in pages_of(section)[page - 1]):
        return None
    return text_for(ends_in["skip_label"], "participant")


def _continue_label(section, page, answers):
    """✨ "Continue →", or on a page holding a coach kept, "Continue with Sam →". Choosing someone else shows the
    checklist's own "Continue →" just above, so the page's way on names the coach it goes on with, to read apart."""
    for block in pages_of(section)[page - 1]:
        coach = _coach_kept(answers, block["id"]) if block["type"] == "coach_checklist" else None
        if coach:
            return f"Continue with {coach['name']} →"
    return "Continue →"


def _published_version(posted):
    """✨ The pathway version a form names, provided it has been published; otherwise None."""
    if not (posted or "").isdigit():
        return None
    return PathwayVersion.objects.filter(pk=int(posted), publications__isnull=False).distinct().first()


def _block_for_participant(document, block, answers, fixed, states, asked_rows=0):
    """✨ One block as its template needs it. `states` are the track's sections as the hub sees them, keyed by
    identifier; a link to a section outside the participant's track has no state and shows nothing."""
    widget = BLOCK_TYPES[block["type"]].widget
    text = authored_text(block, "participant")
    return {
        "rows": _contact_rows(block, answers, asked_rows) if block["type"] == "contact_list" else None,
        "checklist": (
            _opening_checklist(text, _coach_kept(answers, block["id"])) if block["type"] == "coach_checklist" else None
        ),
        "id": block["id"],
        "type": block["type"],
        "template": f"engine/blocks/{block['type']}.html",
        "variant": block.get("variant", "plain"),
        "text": text,
        "answer": answers.get(block["id"]),
        "is_fixed": block["id"] in fixed,
        "widget": widget(document, "participant", "") if widget else None,  # ✨ the participant's wording names no one
        "link": states.get(block["section"]) if block["type"] == "section_link" else None,
    }


def _opening_checklist(text, kept):
    """✨ A coach checklist as a page opens it: the coach kept, if one was chosen, and otherwise its intro, empty,
    since nothing from an earlier visit to the checklist itself was kept."""
    if kept:
        return _checklist_screen(text, screen="chosen", coach=kept)
    return _checklist_screen(text)


def _contact_rows(block, answers, asked_rows):
    """✨ A contact list's rows: every saved person in order, then empty rows up to the number to show."""
    contacts = answers.get(block["id"]) or []
    empty = {"name": "", "email": ""}
    return [*contacts, *[empty] * (rows_to_show(block, contacts, asked_rows) - len(contacts))]
