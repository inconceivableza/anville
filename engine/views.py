from typing import NamedTuple

from django.contrib.auth.decorators import login_required
from django.contrib.humanize.templatetags.humanize import apnumber
from django.db import IntegrityError
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
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
from engine.document.blocks import CONTACTS, blocks_of, page_count, page_of, pages_of, section_of
from engine.document.coach import (
    candidate_name_from_form,
    checklist_answers,
    checklist_answers_from_form,
    checklist_outcome,
    coach_details_as_typed,
    coach_from_form,
)
from engine.document.contacts import MAX_CONTACTS, contacts_from_form, rows_to_show
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
from engine.models import Contact, PathwayVersion, Publication, Response, Result
from engine.results import results_page


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
            value = contacts_from_form(request.POST.getlist("name"), request.POST.getlist("email"))
        else:
            value = answer_from_form(state.version.document, block, request.POST.get("value"))
    except AnswerRefused as refused:
        context = {"refusal": str(refused), "invalid_row": refused.row, "invalid_field": refused.field}
        return render(request, "engine/save_status.html", context, status=400)

    participant_response = state.stored_response(request.user)
    # ✨ The row is updated in place, so the answers read before are a step behind what is about to be stored.
    saved = state._replace(answers={**state.answers, block_id: value})
    if block_type.captures is CONTACTS:
        participant_response.replace_contacts(block_id, value, Contact.Role.CONTACT)
        return _saved(request, saved, section, block_id)
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

    screen = _checklist_step(block, to, request.POST)
    if screen["screen"] == "chosen":
        state.stored_response(request.user).replace_contacts(block_id, [screen["coach"]], Contact.Role.COACH)
    elif to == "remove" and state.response is not None:
        state.response.replace_contacts(block_id, [], Contact.Role.COACH)
    # ✨ A save the outcome does not allow is refused, though its screen (a stop, say) has nothing to add.
    refused = screen.get("refusal") or (to == "save" and screen["screen"] != "chosen")
    status = 400 if refused else 200
    page = page_of(section, block_id)
    is_htmx = request.headers.get("HX-Request") == "true"
    if not is_htmx and status == 200 and to in ("save", "remove"):
        # ✨ Once stored, the checklist is behind: the page shows only the coach kept, so it is safe to go back to.
        return _see_other(f"{page_url(section['id'], page)}#block-{block_id}")
    shown = _section_page(state, section, page)
    checklist_block = next(on_page for on_page in shown["section"]["blocks"] if on_page["id"] == block_id)
    checklist_block["checklist"] = _checklist_screen(checklist_block["text"], **screen)
    if is_htmx:
        context = {"block": checklist_block, "pathway": shown["pathway"]}
        return render(request, checklist_block["template"], context, status=status)
    # ✨ Never a redirect without JavaScript while choosing: the answers would have to go in the address, where they
    # are logged. The page returned is the one the checklist is on.
    return render(request, "engine/section.html", shown, status=status)


# ✨ The buttons of the coach checklist: back to the intro keeping what was given, on to the questions, to see how
# it looks, "I'm still confident" past a second thought, starting again with someone else, saving the coach chosen,
# and removing them.
CHECKLIST_STEPS = ("intro", "questions", "outcome", "confident", "restart", "save", "remove")


def _checklist_step(block, to, posted):
    """✨ Where a press of the checklist's button leads, from what its form held, as the screen's state. A coach
    saved is "chosen", with the coach to keep."""
    questions = block["questions"]
    if to in ("restart", "remove"):
        return {"screen": "intro"}
    name, given = (posted.get("name") or "").strip(), checklist_answers(questions, posted)
    if to == "intro":
        return {"screen": "intro", "name": name, "answers": given}
    if to != "save":  # ✨ on the coach's details, the name is checked with their email, where it can be put right
        try:
            name = candidate_name_from_form(posted)
        except AnswerRefused as refused:
            return {"screen": "intro", "name": name, "answers": given, "refusal": str(refused)}
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
):
    """✨ One screen of the coach checklist as its template needs it: the questions with any answers given, and on
    a second thought or a stop, each answer that was not Yes with why that question matters. On going ahead, the
    coach's details as typed, and which of them a refusal is about; once chosen, the coach kept."""
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
    }


def _saved(request, state, section, block_id):
    """✨ What a stored answer sends back: with htmx, the status and its page's gate; without, its page again.

    A contact list's "add another" without JavaScript saves the list and asks for one more row than it showed,
    which the page then shows.
    """
    page = page_of(section, block_id)
    if request.headers.get("HX-Request") == "true":
        shown = _section_page(state, section, page)
        return render(request, "engine/save_result.html", shown)
    rows = _asked_rows(request.POST)
    query = f"?rows={rows}" if rows else ""
    return _see_other(f"{page_url(section['id'], page)}{query}#block-{block_id}")


@login_required
@consent_required
def results(request, block_id):
    """✨ The participant's own stored result for a scored block, never recomputed and never anyone else's.

    Before there is a result, the participant is sent to the page of the block's section the sort is on. After, the
    page leads back there too, since that is where the section is completed.
    """
    state = _participant(request.user)
    try:
        block = answerable_block(state.version.document, block_id) if state.version else None
    except UnknownBlock:
        block = None
    if block is None or not BLOCK_TYPES[block["type"]].scored:
        raise Http404("This pathway version has no scored block by that identifier.")
    section = section_of(state.version.document, block_id)
    result = Result.objects.filter(response=state.response, block_id=block_id).first()
    if result is None:
        return redirect(page_url(section["id"], page_of(section, block_id)))
    shown = results_page(state.version.document, result.scores, state.answers[block_id], request.user.get_username())
    shown["section"] = {
        "id": section["id"],
        "title": text_for(section["title"], "participant"),
        "page": page_of(section, block_id),
    }
    return render(request, "engine/results.html", shown)


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
    """✨ A scored answer's next page is its result. htmx is told to go there rather than swap anything in."""
    where = reverse("results", args=[block_id])
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
        answers=participant_response.answers_with_contacts(),
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
        "page": {"number": page, "is_last": is_last},
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
        "checklist": _opening_checklist(text, answers.get(block["id"])) if block["type"] == "coach_checklist" else None,
        "id": block["id"],
        "type": block["type"],
        "template": f"engine/blocks/{block['type']}.html",
        "variant": block.get("variant", "plain"),
        "text": text,
        "answer": answers.get(block["id"]),
        "is_fixed": block["id"] in fixed,
        "widget": widget(document, "participant") if widget else None,
        "link": states.get(block["section"]) if block["type"] == "section_link" else None,
    }


def _opening_checklist(text, kept):
    """✨ A coach checklist as a page opens it: the coach kept, if one was chosen, and otherwise its intro, empty,
    since nothing from an earlier visit to the checklist itself was kept."""
    if kept:
        return _checklist_screen(text, screen="chosen", coach=kept[0])
    return _checklist_screen(text)


def _contact_rows(block, answers, asked_rows):
    """✨ A contact list's rows: every saved person in order, then empty rows up to the number to show."""
    contacts = answers.get(block["id"]) or []
    empty = {"name": "", "email": ""}
    return [*contacts, *[empty] * (rows_to_show(block, contacts, asked_rows) - len(contacts))]
