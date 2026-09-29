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
from engine.document.blocks import CONTACTS, blocks_of, page_of, pages_of, section_of
from engine.document.coach import (
    candidate_name_from_form,
    checklist_answers,
    checklist_answers_from_form,
    checklist_outcome,
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
from engine.templatetags.section_pages import page_url


@login_required
@consent_required
def hub(request):
    """✨ Where the participant always starts: their track's sections, their status, and the next step."""
    _, version, answers, completed, moved_past = _participant(request.user)
    if version is None:
        return render(request, "engine/hub.html", {})
    sections = track_sections(version.document)
    if not any(section["blocks"] for section in sections):
        return render(request, "engine/hub.html", {})  # ✨ no content is the empty state, never a fallback
    return render(
        request,
        "engine/hub.html",
        {
            "title": text_for(version.document["title"], "participant"),
            "hub": hub_for(sections, answers, completed, moved_past=moved_past),
        },
    )


@login_required
@consent_required
def start(request):
    """✨ Where agreeing to consent leads. A participant with nothing saved goes straight to their first step,
    as the prototype goes from its account screen into onboarding; anyone who has begun goes to the hub."""
    participant_response, version, answers, completed, _ = _participant(request.user)
    if participant_response is not None or version is None:
        return redirect("hub")
    sections = track_sections(version.document)
    next_step = hub_for(sections, answers, completed).next_step
    if next_step is None or not any(section["blocks"] for section in sections):
        return redirect("hub")  # ✨ the hub's empty state says there is nothing to begin
    return redirect("section", next_step.id)


@login_required
@consent_required
def section(request, section_id, page=1):
    """✨ One page of a section's blocks. A locked section, or a page not yet reached, is refused here, whatever the
    participant typed in the bar: a page ahead of the one reached leads back to that one."""
    participant_response, version, answers, completed, moved_past = _participant(request.user)
    section = _section_or_404(version, section_id)
    if is_locked(section, completed):
        return redirect("hub")
    _page_or_404(section, page)
    reached = page_reached(section, moved_past.get(section_id, ()))
    if page > reached:
        return redirect(page_url(section_id, reached))
    shown = _section_page(
        version, section, answers, completed, _fixed(participant_response), moved_past, page, _asked_rows(request.GET)
    )
    return render(request, "engine/section.html", shown)


@login_required
@consent_required
@require_POST
def move_past_page(request, section_id, page):
    """✨ "Continue →" from one page of a section to the next, allowed exactly when the page offers it: once that page's
    clauses pass and nothing on the way to it (an unconfirmed reading, a held link) holds what follows. Re-checked here
    rather than trusted to the page. The last page has no way on but completing the section."""
    participant_response, version, answers, completed, moved_past = _participant(request.user)
    section = _section_or_404(version, section_id)
    if is_locked(section, completed):
        return redirect("hub")
    if _page_or_404(section, page) == len(pages_of(section)):
        raise Http404("The last page of a section is moved past by completing it.")
    reached = page_reached(section, moved_past.get(section_id, ()))
    if page > reached:
        return _see_other(page_url(section_id, reached))
    shown = _section_page(version, section, answers, completed, _fixed(participant_response), moved_past, page)
    if not shown["offers_completion"] or shown["unmet"]:
        return render(request, "engine/section.html", {**shown, "refused": True}, status=400)

    if participant_response is None:
        participant_response, _ = Response.objects.get_or_create(participant=request.user, version=version)
    participant_response.move_past_page(section_id, page)
    return _see_other(page_url(section_id, page + 1))


@login_required
@consent_required
@require_POST
def complete_section(request, section_id):
    """✨ The participant's own act of finishing a section, re-checked here rather than trusted to the page. It is
    done from the section's last page, so a participant who has not reached it is sent to the page they have."""
    participant_response, version, answers, completed, moved_past = _participant(request.user)
    section = _section_or_404(version, section_id)
    if is_locked(section, completed):
        return redirect("hub")
    last = len(pages_of(section))
    reached = page_reached(section, moved_past.get(section_id, ()))
    if reached < last:
        return _see_other(page_url(section_id, reached))
    if unmet(section, answers):
        shown = _section_page(version, section, answers, completed, _fixed(participant_response), moved_past, last)
        return render(request, "engine/section.html", {**shown, "refused": True}, status=400)

    if participant_response is None:
        participant_response, _ = Response.objects.get_or_create(participant=request.user, version=version)
    participant_response.complete_section(section_id, fixed_block_ids=block_ids_fixed_on_completion(section, answers))
    # ✨ On to whatever the hub would now point at, as the prototype moves from screen to screen; the hub once
    # nothing is left.
    sections = track_sections(version.document)
    next_step = hub_for(sections, answers, completed | {section_id}, moved_past=moved_past).next_step
    return _see_other(page_url(next_step.id, next_step.page)) if next_step else _see_other("hub")


@login_required
@consent_required
@require_POST
def reopen_section(request, section_id):
    """✨ The participant taking back their own completion. Their answers stay exactly as they left them."""
    participant_response, version, _, _, _ = _participant(request.user)
    _section_or_404(version, section_id)
    if participant_response is not None:
        participant_response.reopen_section(section_id)
    return _see_other("hub")


@login_required
@consent_required
@require_POST
def save_answer(request, block_id):
    """✨ Autosave: validate and store one block's answer against the participant's pathway version.

    A participant with a response answers its version. A first answer is recorded against the version
    the page was rendered from, so a version published while they were typing never captures it.
    """
    participant_response = Response.in_progress(request.user)
    version = participant_response.version if participant_response else _published_version(request.POST.get("version"))
    if version is None:
        raise Http404("No published pathway version was named.")
    try:
        block = answerable_block(version.document, block_id)
    except UnknownBlock:
        raise Http404("This pathway version has no block by that identifier that takes an answer.")
    # ✨ A block a participant has not reached is as shut as the page that would have shown it, whether a
    # lock or an unconfirmed reading holds it. Otherwise they could fill it in without ever opening it, and
    # both would be decoration again, which is exactly the prototype's mistake.
    section = section_of(version.document, block_id)
    answers = participant_response.answers_with_contacts() if participant_response else {}
    completed = set(participant_response.completed_sections) if participant_response else set()
    moved_past = participant_response.moved_past_by_section() if participant_response else {}
    if not _is_open(section, block, answers, completed, moved_past, version):
        return render(request, "engine/save_status.html", {"refusal": "This is not open yet."}, status=403)
    fixed = _fixed(participant_response)
    if block_id in fixed:
        # ✨ Refused here, not only disabled on the page, so a page left open from before completing cannot change it.
        return _refuse_fixed(request)
    block_type = BLOCK_TYPES[block["type"]]
    try:
        if block_type.captures is CONTACTS:
            value = contacts_from_form(request.POST.getlist("name"), request.POST.getlist("email"))
        else:
            value = answer_from_form(version.document, block, request.POST.get("value"))
    except AnswerRefused as refused:
        context = {"refusal": str(refused), "invalid_row": refused.row, "invalid_field": refused.field}
        return render(request, "engine/save_status.html", context, status=400)

    if participant_response is None:
        participant_response, _ = Response.objects.get_or_create(participant=request.user, version=version)
    if block_type.captures is CONTACTS:
        participant_response.replace_contacts(block_id, value, Contact.Role.CONTACT)
        answers = {**answers, block_id: value}
        return _saved(request, version, section, answers, completed, fixed, moved_past, block_id)
    if block_type.scored:
        try:
            participant_response.submit_sort(block_id, value, score(version.document, value))
        except IntegrityError:
            refusal = "Your results are already in. Retaking the sort is not offered yet."
            return render(request, "engine/save_status.html", {"refusal": refusal}, status=409)
        return _to_results(request, block_id)
    if not participant_response.save_answer(block_id, value):
        return _refuse_fixed(request)  # ✨ a completion fixed it after the check above, and the UPDATE saw that
    # ✨ The row was updated in place, so this object's answers are a step behind what was just stored.
    answers = {**answers, block_id: value}
    return _saved(request, version, section, answers, completed, fixed, moved_past, block_id)


@sensitive_post_parameters()
@login_required
@consent_required
@require_POST
def coach_checklist(request, block_id):
    """✨ One step of choosing a coach: from the intro to the questions, to an outcome, or back to the start.

    Nothing is stored or logged. The candidate's name and the answers so far travel only in the form, screen to
    screen, and the outcome is worked out again from what was posted, never taken from the button pressed. The
    answers are opinions about another person, including their faith (special category data under GDPR), and no
    later step reads them; `sensitive_post_parameters` keeps them out of error reports too.
    """
    participant_response, version, answers, completed, moved_past = _participant(request.user)
    block = _block_of_type(version, block_id, "coach_checklist")
    section = section_of(version.document, block_id)
    if not _is_open(section, block, answers, completed, moved_past, version):
        return render(request, "engine/save_status.html", {"refusal": "This is not open yet."}, status=403)
    if request.POST.get("step") not in CHECKLIST_STEPS:
        return HttpResponseBadRequest("The coach checklist has no such step.")

    state = _checklist_step(block, request.POST["step"], request.POST)
    status = 400 if state.get("refusal") else 200
    page = _section_page(
        version, section, answers, completed, _fixed(participant_response), moved_past, page_of(section, block_id)
    )
    shown = next(shown for shown in page["section"]["blocks"] if shown["id"] == block_id)
    shown["checklist"] = _checklist_screen(shown["text"], **state)
    if request.headers.get("HX-Request") == "true":
        return render(request, shown["template"], {"block": shown, "pathway": page["pathway"]}, status=status)
    # ✨ Never a redirect without JavaScript: the answers would have to go in the address, where they are logged.
    # The page returned is the one the checklist is on.
    return render(request, "engine/section.html", page, status=status)


# ✨ The buttons of the coach checklist: back to the intro keeping what was given, on to the questions, to see how
# it looks, "I'm still confident" past a second thought, and starting again with someone else.
CHECKLIST_STEPS = ("intro", "questions", "outcome", "confident", "restart")


def _checklist_step(block, to, posted):
    """✨ Where a press of the checklist's button leads, from what its form held, as the screen's state."""
    questions = block["questions"]
    if to == "restart":
        return {"screen": "intro"}
    name, given = (posted.get("name") or "").strip(), checklist_answers(questions, posted)
    if to == "intro":
        return {"screen": "intro", "name": name, "answers": given}
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
    if to == "confident" and outcome.verdict == "confirm":
        return {"screen": "proceed", "name": name, "answers": given, "confident": True}
    return {"screen": outcome.verdict, "name": name, "answers": given, "outcome": outcome}


def _checklist_screen(text, screen="intro", name="", answers=None, outcome=None, refusal=None, confident=False):
    """✨ One screen of the coach checklist as its template needs it: the questions with any answers given, and on
    a second thought or a stop, each answer that was not Yes with why that question matters."""
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
    }


def _saved(request, version, section, answers, completed, fixed, moved_past, block_id):
    """✨ What a stored answer sends back: with htmx, the status and its page's gate; without, its page again.

    A contact list's "add another" without JavaScript saves the list and asks for one more row than it showed,
    which the page then shows.
    """
    page = page_of(section, block_id)
    if request.headers.get("HX-Request") == "true":
        shown = _section_page(version, section, answers, completed, fixed, moved_past, page)
        return render(request, "engine/save_result.html", shown)
    rows = _asked_rows(request.POST)
    query = f"?rows={rows}" if rows else ""
    return _see_other(f"{page_url(section['id'], page)}{query}#block-{block_id}")


@login_required
@consent_required
def results(request, block_id):
    """✨ The participant's own stored result for a scored block, never recomputed and never anyone else's.

    Before there is a result, the participant is sent to the block's section, where the sort is. After, the page
    leads back there too, since that is where the section is completed.
    """
    participant_response, version, answers, _, _ = _participant(request.user)
    try:
        block = answerable_block(version.document, block_id) if version else None
    except UnknownBlock:
        block = None
    if block is None or not BLOCK_TYPES[block["type"]].scored:
        raise Http404("This pathway version has no scored block by that identifier.")
    section = section_of(version.document, block_id)
    result = Result.objects.filter(response=participant_response, block_id=block_id).first()
    if result is None:
        return redirect("section", section["id"])
    page = results_page(version.document, result.scores, answers[block_id], request.user.get_username())
    page["section"] = {
        "id": section["id"],
        "title": text_for(section["title"], "participant"),
        "page": page_of(section, block_id),
    }
    return render(request, "engine/results.html", page)


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


def _participant(user):
    """✨ Everything stored for this participant: their response, the version it answers, and its state (answers,
    sections completed, and pages moved past by section).

    A participant without a response yet reads the published version, so what they see is what their
    first answer will be recorded against.
    """
    participant_response = Response.in_progress(user)
    if participant_response is None:
        return None, Publication.current_version(), {}, set(), {}
    return (
        participant_response,
        participant_response.version,
        participant_response.answers_with_contacts(),
        set(participant_response.completed_sections),
        participant_response.moved_past_by_section(),
    )


def _is_open(section, block, answers, completed, moved_past, version):
    """✨ Whether a participant has reached a block: its section is not locked, its page has been reached, and no
    unconfirmed reading or held link above it holds it shut."""
    if is_locked(section, completed):
        return False
    reached = page_reached(section, moved_past.get(section["id"], ()))
    blocks, _ = open_blocks(section, answers, track_sections(version.document), up_to_page=reached)
    return block in blocks


def _page_or_404(section, page):
    if not 1 <= page <= len(pages_of(section)):
        raise Http404("This section has no page by that number.")
    return page


def _refuse_fixed(request):
    refusal = "This answer was fixed when you completed this section."
    return render(request, "engine/save_status.html", {"refusal": refusal}, status=409)


def _fixed(participant_response):
    """✨ The block identifiers whose answers this participant can no longer change."""
    return set(participant_response.fixed_answers) if participant_response else set()


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


def _section_page(version, section, answers, completed, fixed, moved_past, page=1, asked_rows=0):
    """✨ One page of a section as its template needs it. Every page but the last ends in "Continue →", held by that
    page's own clauses; the last ends in the section's completion, held by the whole gate."""
    opened, activity_open = open_blocks(section, answers, track_sections(version.document), up_to_page=page)
    on_page = {block["id"] for block in pages_of(section)[page - 1]}
    blocks = [block for block in opened if block["id"] in on_page]
    is_last = page == len(pages_of(section))
    # ✨ A sort leads only to its results, as in the prototype, so completing is not offered beside it until it
    # is in. The linter makes its section's gate require it, so the server refuses completion before then too.
    sort_pending = any(BLOCK_TYPES[block["type"]].scored and block["id"] not in answers for block in blocks)
    # ✨ A link shows the section it leads to exactly as the hub would: its title, its status and whether it is open.
    hub = hub_for(track_sections(version.document), answers, completed, moved_past=moved_past)
    states = {state.id: state for state in hub.sections}
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
        "is_complete": section["id"] in completed,
        # ✨ Over the whole section, since the ratings it fixed may be on an earlier page than its completion.
        "holds_fixed_answers": any(block["id"] in fixed for block in section["blocks"]),
        # ✨ The way on, "Continue →" or completion. Going on from a page is refused on exactly these and `unmet`.
        "offers_completion": activity_open and not sort_pending,
        "unmet": unmet(section, answers) if is_last else unmet(section, answers, page=page),
        "checklist": checklist(section, answers, page=page),
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
        # ✨ A coach checklist always opens on its intro, empty: nothing from an earlier visit was kept.
        "checklist": _checklist_screen(text) if block["type"] == "coach_checklist" else None,
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


def _contact_rows(block, answers, asked_rows):
    """✨ A contact list's rows: every saved person in order, then empty rows up to the number to show."""
    contacts = answers.get(block["id"]) or []
    empty = {"name": "", "email": ""}
    return [*contacts, *[empty] * (rows_to_show(block, contacts, asked_rows) - len(contacts))]
