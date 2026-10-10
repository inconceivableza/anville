# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

import json
from typing import NamedTuple

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.humanize.templatetags.humanize import apnumber
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST

from access.consent import consent_required
from access.models import Account, name_shown_for
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
from engine.document.blocks import (
    CONTACTS,
    blocks_of,
    break_after,
    coach_brief,
    landing_of,
    page_count,
    page_of,
    pages_of,
    section_of,
    translation_shown,
)
from engine.document.coach import (
    candidate_name_from_form,
    checklist_answers,
    checklist_answers_from_form,
    checklist_outcome,
    coach_answer_from_form,
    coach_details_as_typed,
    coach_from_form,
    commitments,
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
from engine.document.gates import clauses_of, has_content
from engine.document.scoring import score
from engine.hub import (
    block_ids_fixed_on_completion,
    complete_sections,
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
        if is_locked(section, self.completed, self.answers, self.sections, self.moved_past):
            return None
        return page_reached(section, self.moved_past, self.answers, self.sections)

    def with_answers(self, answers):
        """✨ This state with `answers` in place of its own, and what is complete worked out again from them, since a part
        of a section is complete once its gate passes."""
        stored = self.response.completed_sections if self.response is not None else ()
        return self._replace(answers=answers, completed=complete_sections(self.sections, answers, stored))

    def stored_response(self, user):
        """✨ Their response, begun now if this is the first thing they store."""
        if self.response is not None:
            return self.response
        return Response.objects.get_or_create(participant=user, version=self.version)[0]


def home(request):
    """✨ The public homepage (ticket 32a), the same for everyone; "Begin" leads to sign-up, or to the hub once
    signed in."""
    begin = reverse("hub") if request.user.is_authenticated else reverse("account_signup")
    return render(request, "engine/home.html", {"begin": begin})


def credits_page(request):
    """✨ The copyright notice of each translation the published pathway quotes, open to anyone, since the public
    homepage quotes scripture too. The publishers ask for their notices on the work's copyright page (ticket 39)."""
    version = Publication.current_version()
    translations = version.document.get("translations", {}) if version else {}
    return render(request, "engine/credits.html", {"translations": translations.values()})


@login_required
@consent_required
def hub(request):
    """✨ Where the participant always starts: their track's sections, their status, and the next step."""
    state = _participant(request.user)
    if state.version is None:
        return render(request, "engine/hub.html", {})
    if not any(section["blocks"] for section in state.sections):
        return render(request, "engine/hub.html", {})  # ✨ no content is the empty state, never a fallback
    account = getattr(request.user, "account", None)
    if account is not None and not account.onboarding_completed and _onboarding_content(state.version.document):
        return redirect("onboarding")
    hub = hub_for(state.sections, state.answers, state.completed, moved_past=state.moved_past)
    return render(
        request,
        "engine/hub.html",
        {
            "title": text_for(state.version.document["title"], "participant"),
            "hub": hub,
            "coach": _coach_of(state.response),
            "coach_page": _coach_page_of(state.version.document, hub),
            "voices": _hub_voices(state.response),
            "baseline": _hub_baseline(state.version.document, state),
            "name": name_shown_for(state.response.participant) if state.response else None,
        },
    )


def _coach_page_of(document, hub):
    """✨ The address of the page of the document's coach checklist, at the checklist, or None for a document without
    one, whose hub then says nothing of a coach. None too while the participant's `hub` has its section locked, as a
    locked section's pages are never linked."""
    for block in blocks_of(document):
        if block["type"] == "coach_checklist":
            section = section_of(document, block["id"])
            if any(state.id == section["id"] and state.is_locked for state in hub.sections):
                return None
            return _block_address(document, block["id"])
    return None


def _block_address(document, block_id):
    """✨ The address of the page a block is on, at the block."""
    section = section_of(document, block_id)
    return f"{page_url(section['id'], page_of(section, block_id))}#block-{block_id}"


def participant_nav(request):
    """✨ The header and sidebar of every participant page (ticket 41a), as `engine/participant_header.html` needs them:
    the pathway's name, and unless the site switches it off, the sidebar. The sidebar's sections are the hub's own, so
    their statuses and locks are the hub's; a locked section carries no address, and neither does a page within it,
    such as the coach page. Results and the comparison are listed once there is a result, since before then they lead
    only back to the sort. `current` is the section whose page this is, if any."""
    state = _participant(request.user)
    if state.version is None:
        return {"title": None, "sidebar": None}
    document = state.version.document
    title = text_for(document["title"], "participant")
    if not settings.ANVILLE_SIDEBAR or not any(section["blocks"] for section in state.sections):
        return {"title": title, "sidebar": None}
    hub = hub_for(state.sections, state.answers, state.completed, moved_past=state.moved_past)
    links = []
    scored = _scored_block(document)
    if scored and Result.objects.filter(response=state.response, block_id=scored["id"]).exists():
        links += [
            ("Your results", reverse("results", args=[scored["id"]])),
            ("How others experience you", reverse("comparison", args=[scored["id"]])),
        ]
    links.append(("Invite others to assess you", reverse("invitations")))
    coach_page = _coach_page_of(document, hub)
    if coach_page:
        links.append(("Your coach", coach_page))
    return {
        "title": title,
        "sidebar": {
            "outline": hub.outline(),
            "current": _current_section(request, document),
            "links": [{"label": label, "href": href, "is_current": href == request.path} for label, href in links],
        },
    }


def _current_section(request, document):
    """✨ The identifier of the section whose page this is, or None. Every address naming a section is that section's,
    a refused "Continue →" or completion included; a coach checklist's step, without JavaScript, shows the page of the
    checklist's section."""
    match = request.resolver_match
    if match is None:
        return None
    if match.url_name == "coach_checklist":
        return section_of(document, match.kwargs["block_id"])["id"]
    return match.kwargs.get("section_id")


@login_required
@consent_required
def start(request):
    """✨ Where agreeing to consent leads. A participant with nothing saved goes straight to their first step,
    as the prototype goes from its account screen into onboarding; anyone who has begun goes to the hub."""
    state = _participant(request.user)
    account = getattr(request.user, "account", None)
    if account is not None and not account.onboarding_completed and state.version and _onboarding_content(state.version.document):
        return redirect("onboarding")
    if state.response is not None or state.version is None:
        return redirect("hub")
    next_step = hub_for(state.sections, state.answers, state.completed).next_step
    if next_step is None or not any(section["blocks"] for section in state.sections):
        return redirect("hub")  # ✨ the hub's empty state says there is nothing to begin
    return redirect("section", next_step.id)


@login_required
@consent_required
def onboarding(request):
    """✨ The new participant's four presentational steps, with reason and baseline saved as pathway answers."""
    account = getattr(request.user, "account", None)
    if account is None or account.onboarding_completed:
        return redirect("hub")

    state = _participant(request.user)
    if state.version is None:
        return redirect("hub")

    onboarding_content = _onboarding_content(state.version.document)
    if onboarding_content is None:
        return redirect("hub")
    onboarding_section, reason_block, baseline_blocks = onboarding_content

    reason_text = authored_text(reason_block, "participant")
    reason_text["answer"] = state.answers.get(reason_block["id"])
    baseline = [
        {
            "id": block["id"],
            "text": authored_text(block, "participant"),
            "value": state.answers.get(block["id"]),
        }
        for block in baseline_blocks
    ]
    step = _onboarding_step(account, baseline)
    requested_step = request.POST.get("step") if request.method == "POST" else request.GET.get("step")
    try:
        requested_step = int(requested_step) if requested_step is not None else step
    except (TypeError, ValueError):
        requested_step = step
    requested_step = max(0, min(requested_step, step))

    error = None
    status = 200
    if request.method == "POST" and request.POST.get("action") == "back":
        return _see_other(f"{reverse('onboarding')}?step={max(0, requested_step - 1)}")
    if request.method == "POST" and request.POST.get("action") == "continue":
        if requested_step == 0:
            try:
                answer = answer_from_form(state.version.document, reason_block, request.POST.get(reason_block["id"]))
                if not _is_open(state, onboarding_section, reason_block):
                    raise AnswerRefused("This step is not open yet.")
                with transaction.atomic():
                    response = state.stored_response(request.user)
                    if not response.save_answer(reason_block["id"], answer):
                        raise AnswerRefused("This answer is fixed and can no longer be changed.")
                    account.reason = answer
                    account.save(update_fields=["reason"])
                return _see_other(f"{reverse('onboarding')}?step=1")
            except AnswerRefused as refused:
                error = str(refused)
                status = 400
        elif requested_step == 1:
            try:
                answers = []
                for block in baseline_blocks:
                    if not _is_open(state, onboarding_section, block):
                        raise AnswerRefused("This step is not open yet.")
                    if block["id"] in state.fixed:
                        raise AnswerRefused("A baseline answer is fixed and can no longer be changed.")
                    answers.append(
                        (block["id"], answer_from_form(state.version.document, block, request.POST.get(block["id"])))
                    )
                with transaction.atomic():
                    response = state.stored_response(request.user)
                    if not all(response.save_answer(block_id, value) for block_id, value in answers):
                        raise AnswerRefused("A baseline answer is fixed and can no longer be changed.")
                return _see_other(f"{reverse('onboarding')}?step=2")
            except AnswerRefused as refused:
                error = str(refused)
                status = 400
        elif requested_step == 2:
            selected_path = request.POST.get("path")
            if selected_path not in {choice[0] for choice in Account._meta.get_field("path").choices}:
                error = "Choose how you'd like to work."
                status = 400
            else:
                account.path = selected_path
                account.save(update_fields=["path"])
                return _see_other(f"{reverse('onboarding')}?step=3")
        elif requested_step == 3:
            account.remind = request.POST.get("remind") == "on"
            account.onboarding_completed = True
            account.save(update_fields=["remind", "onboarding_completed"])
            return _see_other("hub")

    if request.method == "POST" and status == 400:
        if requested_step == 0:
            reason_text["answer"] = request.POST.get(reason_block["id"], "")
        elif requested_step == 1:
            for question in baseline:
                question["value"] = request.POST.get(question["id"], "")

    return render(
        request,
        "engine/onboarding.html",
        {
            "step": requested_step,
            "reason": reason_text,
            "baseline": baseline,
            "selected_path": request.POST.get("path", account.path),
            "remind": request.POST.get("remind") == "on" if request.method == "POST" else account.remind,
            "display_name": account.display_name,
            "email": request.user.email,
            "error": error,
        },
        status=status,
    )


def _onboarding_step(account, baseline):
    """✨ The furthest onboarding step whose prerequisites have been saved."""
    if not account.reason:
        return 0
    if any(question["value"] is None for question in baseline):
        return 1
    if not account.path:
        return 2
    return 3


def _onboarding_content(document):
    """✨ The authored reason and baseline blocks that make this pathway eligible for the four-step introduction."""
    for section in document["content"]["sections"]:
        reason = next(
            (block for block in section["blocks"] if block["id"] == "reason" and block["type"] == "single_select"),
            None,
        )
        scales = [block for block in section["blocks"] if block["type"] == "agreement_scale"]
        if reason and scales:
            return section, reason, scales
    return None


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
    # ✨ A coach's link just issued from the coach page, shown this once, as on the invitations page. Read only on a page
    # holding a coach checklist, whose address is the path the cookie was set for, so deleting it here reaches it; the
    # section's later pages sit under that path too when the checklist is on its first.
    holds_checklist = any(block["type"] == "coach_checklist" for block in pages_of(section)[page - 1])
    issued = _issued_link(request) if holds_checklist else None
    shown = render(
        request, "engine/section.html", _section_page(state, section, page, _asked_rows(request.GET), issued=issued)
    )
    if issued is not None:
        shown["Cache-Control"] = "no-store"
        shown.delete_cookie(ISSUED_COOKIE, path=request.path)
    return shown


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
    done from the section's last page, so a participant who has not reached it is sent to the page they have. A part of
    a section has no completion of its own: it is complete once its gate passes."""
    state = _participant(request.user)
    section = _section_or_404(state.version, section_id)
    if "part_of" in section:
        raise Http404("A part of a section is complete once its gate passes, with no completion of its own.")
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
    # ✨ Back to the hub, which points at the next step, as the prototype's `completePillar` goes (ticket 41b).
    return _see_other("hub")


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
    saved = state.with_answers({**state.answers, block_id: value})
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
        # ✨ Always a new contact, so the previous coach's link stops, with any answer given through it.
        [coach] = state.stored_response(request.user).replace_contacts(block_id, [screen["coach"]], Contact.Role.COACH)
        screen["coach"] = {**screen["coach"], "id": coach.pk}
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
    shown = _section_page(state.with_answers(kept), section, page)
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
    issued=None,
):
    """✨ One screen of the coach checklist as its template needs it: the questions with any answers given, and on
    a second thought or a stop, each answer that was not Yes with why that question matters. On going ahead, the
    coach's details as typed, and which of them a refusal is about; once chosen, the coach kept, with their link
    (`issued` is a link just issued, shown this once). On the intro while choosing again, `kept` is the coach who
    stays until another is saved."""
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
        "link": _coach_link_state(coach["id"], issued) if screen == "chosen" and coach and "id" in coach else None,
    }


def _coach_kept(answers, block_id):
    """✨ The coach kept for a coach checklist, as {"name", "email", "id"}, or None: its answer is the one coach kept."""
    kept = answers.get(block_id)
    return kept[0] if kept else None


def _coach_link_state(contact_id, issued=None):
    """✨ The coach's link as the coach page shows it: the contact it is for, its invitation while it works, the coach's
    answer ("waiting" while a working link is unanswered, None with no link at all), and the link itself if it was
    just issued. An answer outlasts the link's expiry, but not its revoking: it belongs to the link it came through."""
    invitation = Invitation.objects.filter(contact_id=contact_id).first()
    live = invitation if invitation is not None and invitation.works() else None
    answer = invitation.coach_answer if invitation is not None else None
    return {
        "contact_id": contact_id,
        "invitation": live,
        "answer": answer or ("waiting" if live else None),
        "issued": issued["link"] if issued and issued["contact"] == contact_id else None,
    }


def _coach_declined(contact_id):
    """✨ Whether the coach kept declined, through the link they still have an answer on."""
    return Invitation.objects.filter(contact_id=contact_id, coach_answer=Invitation.CoachAnswer.DECLINED).exists()


def _saved(request, state, section, block_id, contact_ids=None):
    """✨ What a stored answer sends back: with htmx, the status and its page's gate; without, its page again.

    A contact list's "add another" without JavaScript saves the list and asks for one more row than it showed,
    which the page then shows. A block that opens what follows (a reading) lands at its confirmation, with what it
    opened beneath, rather than back at its top above what was just read (ticket 41e).
    """
    page = page_of(section, block_id)
    if request.headers.get("HX-Request") == "true":
        shown = _section_page(state, section, page)
        return render(request, "engine/save_result.html", {**shown, "contact_ids": contact_ids})
    block = next(block for block in section["blocks"] if block["id"] == block_id)
    return _see_other(f"{page_url(section['id'], page)}{_rows_query(request.POST)}#{landing_of(block)}")


def _rows_query(posted):
    """✨ The address's query for the rows "add another" asked for without JavaScript, or nothing."""
    rows = _asked_rows(posted)
    return f"?rows={rows}" if rows else ""


@login_required
@consent_required
def results(request, block_id):
    """✨ The participant's own stored result for a scored block, never recomputed and never anyone else's.

    Before there is a result, the participant is sent to the page of the block's section the sort is on. After, the
    page leads back to the section that one is a part of (ticket 41b), or else to the sort's own section, where it is
    completed.
    """
    state, result, section = _own_result(request.user, block_id)
    if result is None:
        return redirect(page_url(section["id"], section["page"]))
    shown = results_page(state.version.document, result.scores, state.answers[block_id], name_shown_for(request.user))
    return render(request, "engine/results.html", {"results": shown, "section": section, "block_id": block_id})


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
    shown = _comparison_of(state.response, result.scores, state.answers[block_id])
    sort = next(block for block in blocks_of(state.response.version.document) if block["id"] == block_id)
    context = {
        "comparison": shown,
        "block_id": block_id,
        "coach": _coach_sharing(state.response, block_id),
        "brief": coach_brief(sort),
        "back": section["back"],
    }
    return render(request, "engine/comparison.html", context)


@login_required
@consent_required
@require_POST
def share_with_coach(request, block_id):
    """✨ The comparison's "Give my coach access to my results and this comparison", ticked or not (ticket 27). Ticking is refused until the
    participant has visited their comparison and their coach has accepted through a link that still works; the consent
    is then kept on that link, so it goes with it (ADR 0011). Unticking withdraws it at once, whatever else holds.

    The box saves as it changes: with htmx, "Saved" and the line under it for the new state; without, the comparison
    again, at the box."""
    state, result, _ = _own_result(request.user, block_id)
    if request.POST.get("share") != "on":
        Invitation.withdraw_results_from_coach(request.user)
    else:
        visited = result is not None and block_id in state.response.comparisons_visited
        if not (visited and Invitation.share_results_with_coach(state.response)):
            refusal = "Your coach can see this only once they have accepted and you have seen your comparison."
            return render(request, "engine/save_status.html", {"refusal": refusal}, status=403)
    if request.headers.get("HX-Request") == "true":
        return render(request, "engine/coach_share_saved.html", {"coach": _coach_sharing(state.response, block_id)})
    return _see_other(f"{reverse('comparison', args=[block_id])}#coach-share")


def _comparison_of(response, scores, sort):
    """✨ The comparison of one participant's result with their observers, as both they and their coach see it."""
    document = response.version.document
    assessments = ObserverResponse.assessments_for(response)
    shown = comparison_page(document, scores, sort, aggregate(document, assessments.assessments))
    # ✨ Below the minimum there is no comparison on the page to call illustrative.
    shown["illustrative"] = assessments.all_test_data and shown["frameworks"] is not None
    return shown


def _coach_sharing(response, block_id):
    """✨ The participant's coach as the comparison's consent needs them, or None when there is nothing to say: with
    `offer` "tick" once they accepted through a working link and the comparison was visited by its button; "expired"
    when they accepted but the link no longer works; "awaiting" while they have not answered or have no link yet. A
    coach who declined is offered nothing here: the coach page already says so."""
    coach = _coach_of(response)
    if coach is None:
        return None
    if coach["can_see"]:
        offer = "tick" if block_id in response.comparisons_visited else None
    elif coach["answer"] == Invitation.CoachAnswer.ACCEPTED:
        offer = "expired"
    elif coach["answer"] in ("waiting", None):
        offer = "awaiting"
    else:
        offer = None
    return {**coach, "offer": offer} if offer else None


def _coach_of(response):
    """✨ The coach kept, as the hub and the comparison read them, or None: their name, the coach page, their answer as
    the coach page tells it, whether they can be shown the results (accepted through a working link) and whether they
    are."""
    coach = response.contacts.filter(role=Contact.Role.COACH).first() if response is not None else None
    if coach is None:
        return None
    accepted = Invitation.accepted_coach_of(response)
    return {
        "name": coach.name,
        "coach_page": _listed_at(coach),
        "answer": _coach_link_state(coach.pk)["answer"],
        "can_see": accepted is not None,
        "shared": accepted is not None and accepted.results_shared_at is not None,
    }


def _hub_voices(response):
    """✨ The trusted-voices card on the hub: how many people the participant has invited, how many have replied,
    their names, and the most they can invite."""
    if response is None:
        return {"invited": 0, "replied": 0, "names": [], "max": MAX_CONTACTS}
    contacts = response.contacts.filter(role=Contact.Role.CONTACT).select_related("invitation").order_by("position")
    names = [contact.name for contact in contacts]
    replied = sum(1 for contact in contacts if contact.live_invitation() and contact.live_invitation().claimed_at)
    return {"invited": len(names), "replied": replied, "names": names, "max": MAX_CONTACTS}


def _hub_baseline(document, state):
    """✨ The "Where you started" card on the hub: the participant's own scores on the sort, the top constructs by
    percent, or None before they have a result."""
    scored = _scored_block(document)
    if scored is None:
        return None
    result = Result.objects.filter(response=state.response, block_id=scored["id"]).first()
    if result is None:
        return None
    shown = results_page(document, result.scores, state.answers.get(scored["id"], {}), name_shown_for(state.response.participant))
    bars = [bar for framework in shown["frameworks"] for bar in framework["bars"]]
    bars.sort(key=lambda bar: bar["percent"], reverse=True)
    return [{"label": bar["label"], "percent": bar["percent"]} for bar in bars[:4]]


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
    return _see_other("comparison", block_id)


def _own_result(user, block_id):
    """✨ The participant's state, their stored result for a scored block (None before they have one), and the section
    the sort is on with its page, and `back`, where the results and the comparison lead back to: the section that one
    is a part of, if it is one (ticket 41b), or else that section itself. A block that is not scored is a 404."""
    state = _participant(user)
    try:
        block = answerable_block(state.version.document, block_id) if state.version else None
    except UnknownBlock:
        block = None
    if block is None or not BLOCK_TYPES[block["type"]].scored:
        raise Http404("This pathway version has no scored block by that identifier.")
    section = section_of(state.version.document, block_id)
    result = Result.objects.filter(response=state.response, block_id=block_id).first()
    title, page = text_for(section["title"], "participant"), page_of(section, block_id)
    back = _section_this_is_part_of(state, section) or {"title": title, "href": page_url(section["id"], page)}
    return state, result, {"id": section["id"], "title": title, "page": page, "back": back}


@login_required
@consent_required
def download(request, block_id):
    """✨ A download block's file, served only to a participant who has reached the block, as a section's content is
    (ticket 40). The schema keeps the file's name to letters, digits and hyphens, so it cannot leave the folder."""
    state = _participant(request.user)
    block = _block_of_type(state.version, block_id, "download")
    if not _is_open(state, section_of(state.version.document, block_id), block):
        return HttpResponseForbidden("This file opens once you reach it.")
    path = settings.PATHWAY_FILES_DIR / block["file"]
    if not path.is_file():
        raise Http404("This pathway's file is not here.")
    return FileResponse(path.open("rb"), content_type="application/pdf", filename=block["file"])


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
    """✨ Issue, or reissue, one contact's link, then go back to where that person is listed, which shows it this once:
    only its hash is kept. An observer is listed on the invitations page; the coach on the coach page, and their link
    leads to the coach's own page rather than an observer's.

    A redirect, so a reload of the page that follows never issues again. The link travels to that page in a short-lived
    signed cookie of the participant's own, not in the address (where the history would keep it) or the session (where
    the database would).
    """
    contact = _own_contact_or_404(request.user, contact_id)
    token = Invitation.issue(contact, link_lifetime(contact.response.version.document))
    link_to = "coaching" if contact.role == Contact.Role.COACH else "observe"
    link = request.build_absolute_uri(reverse(link_to, args=[token]))
    listed_at = _listed_at(contact)
    back = _see_other(listed_at)
    back.set_signed_cookie(
        ISSUED_COOKIE,
        json.dumps({"contact": contact.pk, "link": link}),
        salt=ISSUED_COOKIE,
        max_age=ISSUED_COOKIE_SECONDS,
        path=listed_at.partition("#")[0],  # ✨ that page alone reads it
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
    """✨ Stop one contact's link, and with a coach's, the answer given through it. Revoking one that is already gone
    does nothing. The page comes back at that person."""
    contact = _own_contact_or_404(request.user, contact_id)
    Invitation.objects.filter(contact=contact).delete()
    return _see_other(_listed_at(contact))


def _listed_at(contact):
    """✨ The address of the page a contact is listed on, at their place in it: the invitations page for an observer,
    the page of the coach checklist that chose them for a coach."""
    if contact.role != Contact.Role.COACH:
        return f"{reverse('invitations')}#person-{contact.pk}"
    return _block_address(contact.response.version.document, contact.block_id)


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


def coaching(request, token):
    """✨ Where the coach's link leads: who asked them, and the commitments to accept or decline; once answered, their
    answer. A wrong, expired or revoked link, or an observer's, gets the observers' one refusal, naming nobody.

    The coach has no account and claims nothing (spec, Coach): nothing here reads or writes the signed-in user.
    """
    invitation = Invitation.live(token, role=Contact.Role.COACH)
    if invitation is None:
        return _refuse_link(request)
    return _coach_page(request, invitation, token)


@sensitive_post_parameters()
@require_POST
def answer_coaching(request, token):
    """✨ The coach accepting or declining, once per link. Accepting needs every commitment ticked; declining is always
    open. Only the answer is kept, never which boxes were ticked: one affirms the coach's own faith, special category
    data about them, and `sensitive_post_parameters` keeps the boxes out of error reports too."""
    invitation = Invitation.live(token, role=Contact.Role.COACH)
    if invitation is None:
        return _refuse_link(request)
    if invitation.coach_answer is not None:
        return _coach_page(request, invitation, token, refusal=ANSWERED_ALREADY, status=409)
    block = _coach_block(invitation)
    try:
        answer = coach_answer_from_form(block["questions"], request.POST)
    except AnswerRefused as refused:
        ticked = set(request.POST.getlist("commitment"))
        return _coach_page(request, invitation, token, refusal=str(refused), ticked=ticked, status=400)
    if not Invitation.answer_as_coach(token, answer):
        # ✨ Answered, revoked or expired since it was read above: read again, so the page says which.
        invitation = Invitation.live(token, role=Contact.Role.COACH)
        if invitation is None:
            return _refuse_link(request)
        return _coach_page(request, invitation, token, refusal=ANSWERED_ALREADY, status=409)
    messages.add_message(request, messages.INFO, "answered", extra_tags=JUST_ANSWERED)
    return _see_other("coaching", token)


ANSWERED_ALREADY = "You've already answered."

# ✨ Marks the page a coach's answer leads to, so its thanks is said once and not on every later visit (ticket 25a).
JUST_ANSWERED = "coach-just-answered"


def _just_answered(request):
    """✨ Whether this page is the one the coach's answer led to. Reading the flash messages uses them all up, so any
    other is put back for the page it was meant for."""
    others = []
    found = False
    for message in messages.get_messages(request):
        if message.extra_tags == JUST_ANSWERED:
            found = True
        else:
            others.append(message)
    for message in others:
        messages.add_message(request, message.level, message.message, extra_tags=message.extra_tags)
    return found


def _coach_page(request, invitation, token, refusal=None, ticked=(), status=200):
    """✨ The coach's page for a live coach's link: the participant's name, the authored invitation, each commitment
    with its note as a box (`ticked` as last sent, on a refusal), or once answered, what follows the answer: thanks
    only on the page their accepting led to, and while the participant shares their results, the sort's brief with them
    (ticket 25a). Never cached, since it is reached by a secret."""
    document, name = _asked_by(invitation)
    shared = _shared_with_coach(invitation, name)
    scored = _scored_block(document)
    text = authored_text(_coach_block(invitation), "participant")
    named = {field: text.get(field, "").replace("{name}", name) for field in COACH_TEXT_FIELDS}
    promises = [
        {"id": question["id"], "commitment": question["commitment"], "note": question.get("coach_note", "")}
        for question in commitments(text["questions"])
    ]
    context = {
        "name": name,
        "text": named,
        "commitments": promises,
        "count": apnumber(len(promises)),
        "ticked": ticked,
        "answer": invitation.coach_answer,
        "refusal": refusal,
        "token": token,
        "shared": shared,
        "brief": coach_brief(scored) if shared and scored else None,
        "briefed": bool(scored and coach_brief(scored)),  # ✨ so "What happens next" promises a guide only if one comes
        "just_accepted": _just_answered(request),
    }
    shown = render(request, "engine/coach_link.html", context, status=status)
    shown["Cache-Control"] = "no-store"
    return shown


# ✨ The authored passages of the coach's page, each naming the participant as {name}.
COACH_TEXT_FIELDS = ("coach_invitation", "coach_accepted", "coach_declined")


def _shared_with_coach(invitation, name):
    """✨ The participant's results and comparison, as they see them, for a coach who accepted through this link and
    whom they are happy to show; otherwise None. Read afresh on every visit, so a withdrawal shows at once (ticket 27).
    Nothing else of the participant's is read: only the stored result, the sort it was scored from and the observers'
    assessments, through the same suppression as the participant's own comparison."""
    if invitation.coach_answer != Invitation.CoachAnswer.ACCEPTED or invitation.results_shared_at is None:
        return None
    participant_response = invitation.contact.response
    document = participant_response.version.document
    scored = _scored_block(document)
    result = Result.objects.filter(response=participant_response, block_id=scored["id"]).first() if scored else None
    if result is None:
        return None
    sort = participant_response.answers[scored["id"]]
    return {
        "results": results_page(document, result.scores, sort, name),
        "comparison": _comparison_of(participant_response, result.scores, sort),
    }


def _coach_block(invitation):
    """✨ The coach checklist that chose the coach a link is for, in the participant's pathway version."""
    document = invitation.contact.response.version.document
    return next(block for block in blocks_of(document) if block["id"] == invitation.contact.block_id)


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
    """✨ The pathway document an invitation belongs to, and the display name of the participant who asked."""
    participant_response = invitation.contact.response
    return participant_response.version.document, name_shown_for(participant_response.participant)


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
    people = [{"contact": contact, "invitation": contact.live_invitation()} for contact in contacts]
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


def _own_contact_or_404(user, contact_id):
    """✨ One of this participant's own contacts, their coach included, or a 404 that says nothing about whether anyone
    else has a contact by that number."""
    contact = Contact.objects.select_related("response__version").filter(pk=contact_id, response__participant=user).first()
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
        return ParticipantState(None, version, sections, {}, complete_sections(sections, {}, ()), {}, set())
    sections = track_sections(participant_response.version.document)
    answers = participant_response.answers_with_contacts_and_visits()
    return ParticipantState(
        response=participant_response,
        version=participant_response.version,
        sections=sections,
        answers=answers,
        # ✨ A part of a section is complete once its gate passes, so locks and the hub count it without a completion.
        completed=complete_sections(sections, answers, participant_response.completed_sections),
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


def _section_page(state, section, page=1, asked_rows=0, issued=None):
    """✨ One page of a section as its template needs it. Every page but the last ends in "Continue →", held by that
    page's own clauses; the last ends in the section's completion, held by the whole gate. `issued` is a coach's link
    just issued, which a coach checklist on the page shows this once."""
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
    links = _requirement_links(state, section)
    gate_checklist = [(message, met, links.get(message)) for message, met in checklist(section, answers, page=page)]
    states = {other.id: other for other in hub.sections}
    return {
        # ✨ Where "← Back" at the top leads: the section this is a part of, or else the hub.
        "back": _section_this_is_part_of(state, section),
        "page": {
            "number": page,
            "count": page_count(section),
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
            "is_part": "part_of" in section,
            "blocks": [
                _block_for_participant(version.document, block, answers, fixed, states, asked_rows, issued)
                for block in blocks
            ],
        },
        "is_complete": section["id"] in state.completed,
        # ✨ Over the whole section, since the ratings it fixed may be on an earlier page than its completion.
        "holds_fixed_answers": any(block["id"] in fixed for block in section["blocks"]),
        # ✨ The way on, "Continue →" or completion. Going on from a page is refused on exactly these and `unmet`.
        "offers_way_on": activity_open and not sort_pending,
        # ✨ What the checklist marks unmet: on the last page, where completing checks it, the whole gate.
        "unmet": [message for message, met, _ in gate_checklist if not met],
        "checklist": gate_checklist,
    }


def _section_this_is_part_of(state, section):
    """✨ The section a part of a section belongs to, as its ways back name it: {"title", "href"}, at the page of it the
    participant has reached. None for a section that is not a part, or whose section is outside the track or locked."""
    parent_section = section_by_id(state.version.document, section["part_of"]) if "part_of" in section else None
    reached = state.reached(parent_section) if parent_section else None
    if reached is None:
        return None
    return {"title": text_for(parent_section["title"], "participant"), "href": page_url(parent_section["id"], reached)}


def _requirement_links(state, section):
    """✨ Where each of a section's requirements met on another page is met, by its message (ticket 41b): a coach's link
    on the coach page, people's links on the invitations page. One whose page is not open yet is left out."""
    document = state.version.document
    links = {}
    for clause in clauses_of(section):
        if clause["type"] != "links_issued":
            continue
        block = next(block for block in blocks_of(document) if block["id"] == clause["block"])
        if not _is_open(state, section_of(document, block["id"]), block):
            continue
        is_coach = block["type"] == "coach_checklist"
        links[text_for(clause["message"], "participant")] = (
            _block_address(document, block["id"]) if is_coach else reverse("invitations")
        )
    return links


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
    checklist's own "Continue →" just above, so the page's way on names the coach it goes on with, to read apart. A
    coach who declined is not gone on with, so the way on is "Continue without a coach →"."""
    for block in pages_of(section)[page - 1]:
        coach = _coach_kept(answers, block["id"]) if block["type"] == "coach_checklist" else None
        if coach and "id" in coach and _coach_declined(coach["id"]):
            return "Continue without a coach →"
        if coach:
            return f"Continue with {coach['name']} →"
    return "Continue →"


def _published_version(posted):
    """✨ The pathway version a form names, provided it has been published; otherwise None."""
    if not (posted or "").isdigit():
        return None
    return PathwayVersion.objects.filter(pk=int(posted), publications__isnull=False).distinct().first()


def _block_for_participant(document, block, answers, fixed, states, asked_rows=0, issued=None):
    """✨ One block as its template needs it. `states` are the track's sections as the hub sees them, keyed by
    identifier; a link to a section outside the participant's track has no state and shows nothing. `issued` is a
    coach's link just issued."""
    widget = BLOCK_TYPES[block["type"]].widget
    text = authored_text(block, "participant")
    if block["type"] == "scripture_reading":
        for passage, shown in zip(block["passages"], text["passages"]):
            shown["translation"] = translation_shown(document, passage)
    is_checklist = block["type"] == "coach_checklist"
    return {
        "rows": _contact_rows(block, answers, asked_rows) if block["type"] == "contact_list" else None,
        "checklist": _opening_checklist(text, _coach_kept(answers, block["id"]), issued) if is_checklist else None,
        "id": block["id"],
        "landing": landing_of(block),  # ✨ where saving it without JavaScript comes back to
        "type": block["type"],
        "template": f"engine/blocks/{block['type']}.html",
        "variant": block.get("variant", "plain"),
        "text": text,
        "answer": answers.get(block["id"]),
        "is_fixed": block["id"] in fixed,
        "widget": widget(document, "participant", "") if widget else None,  # ✨ the participant's wording names no one
        "link": states.get(block["section"]) if block["type"] == "section_link" else None,
    }


def _opening_checklist(text, kept, issued=None):
    """✨ A coach checklist as a page opens it: the coach kept, if one was chosen, with their link, and otherwise its
    intro, empty, since nothing from an earlier visit to the checklist itself was kept."""
    if kept:
        return _checklist_screen(text, screen="chosen", coach=kept, issued=issued)
    return _checklist_screen(text)


def _contact_rows(block, answers, asked_rows):
    """✨ A contact list's rows: every saved person in order, then empty rows up to the number to show."""
    contacts = answers.get(block["id"]) or []
    empty = {"name": "", "email": ""}
    return [*contacts, *[empty] * (rows_to_show(block, contacts, asked_rows) - len(contacts))]
