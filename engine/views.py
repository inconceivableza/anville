from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
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
    text_for,
    unmet,
)
from engine.document.blocks import section_of
from engine.document.scoring import score
from engine.hub import block_ids_fixed_on_completion, hub_for, is_locked, open_blocks, section_by_id, track_sections
from engine.models import PathwayVersion, Publication, Response, Result
from engine.results import results_page


@login_required
@consent_required
def hub(request):
    """✨ Where the participant always starts: their track's sections, their status, and the next step."""
    _, version, answers, completed = _participant(request.user)
    if version is None:
        return render(request, "engine/hub.html", {})
    sections = track_sections(version.document)
    if not any(section["blocks"] for section in sections):
        return render(request, "engine/hub.html", {})  # ✨ no content is the empty state, never a fallback
    return render(
        request,
        "engine/hub.html",
        {"title": text_for(version.document["title"], "participant"), "hub": hub_for(sections, answers, completed)},
    )


@login_required
@consent_required
def section(request, section_id):
    """✨ One section's blocks. A locked section is refused here, whatever the participant typed in the bar."""
    participant_response, version, answers, completed = _participant(request.user)
    section = _section_or_404(version, section_id)
    if is_locked(section, completed):
        return redirect("hub")
    page = _section_page(version, section, answers, completed, _fixed(participant_response))
    return render(request, "engine/section.html", page)


@login_required
@consent_required
@require_POST
def complete_section(request, section_id):
    """✨ The participant's own act of finishing a section, re-checked here rather than trusted to the page."""
    participant_response, version, answers, completed = _participant(request.user)
    section = _section_or_404(version, section_id)
    if is_locked(section, completed):
        return redirect("hub")
    if unmet(section, answers):
        page = _section_page(version, section, answers, completed, _fixed(participant_response))
        return render(request, "engine/section.html", {**page, "refused": True}, status=400)

    if participant_response is None:
        participant_response, _ = Response.objects.get_or_create(participant=request.user, version=version)
    participant_response.complete_section(section_id, fixed_block_ids=block_ids_fixed_on_completion(section, answers))
    return _see_other("hub")


@login_required
@consent_required
@require_POST
def reopen_section(request, section_id):
    """✨ The participant taking back their own completion. Their answers stay exactly as they left them."""
    participant_response, version, _, _ = _participant(request.user)
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
    answers = participant_response.answers if participant_response else {}
    completed = set(participant_response.completed_sections) if participant_response else set()
    reached, _ = open_blocks(section, answers, track_sections(version.document))
    if is_locked(section, completed) or block not in reached:
        return render(request, "engine/save_status.html", {"refusal": "This is not open yet."}, status=403)
    fixed = _fixed(participant_response)
    if block_id in fixed:
        # ✨ Refused here, not only disabled on the page, so a page left open from before completing cannot change it.
        return _refuse_fixed(request)
    try:
        value = answer_from_form(version.document, block, request.POST.get("value"))
    except AnswerRefused as refused:
        return render(request, "engine/save_status.html", {"refusal": str(refused)}, status=400)

    if participant_response is None:
        participant_response, _ = Response.objects.get_or_create(participant=request.user, version=version)
    if BLOCK_TYPES[block["type"]].scored:
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

    if request.headers.get("HX-Request") == "true":
        return render(request, "engine/save_result.html", _section_page(version, section, answers, completed, fixed))
    return _see_other(f"{reverse('section', args=[section['id']])}#block-{block_id}")


@login_required
@consent_required
def results(request, block_id):
    """✨ The participant's own stored result for a scored block, never recomputed and never anyone else's.

    Before there is a result, the participant is sent to the block's section, where the sort is. After, the page
    leads back there too, since that is where the section is completed.
    """
    participant_response, version, answers, _ = _participant(request.user)
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
    page["section"] = {"id": section["id"], "title": text_for(section["title"], "participant")}
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
    """✨ Everything stored for this participant: their response, the version it answers, and its state.

    A participant without a response yet reads the published version, so what they see is what their
    first answer will be recorded against.
    """
    participant_response = Response.in_progress(user)
    if participant_response is None:
        return None, Publication.current_version(), {}, set()
    return (
        participant_response,
        participant_response.version,
        participant_response.answers,
        set(participant_response.completed_sections),
    )


def _refuse_fixed(request):
    refusal = "This answer was fixed when you completed this section."
    return render(request, "engine/save_status.html", {"refusal": refusal}, status=409)


def _fixed(participant_response):
    """✨ The block identifiers whose answers this participant can no longer change."""
    return set(participant_response.fixed_answers) if participant_response else set()


def _section_or_404(version, section_id):
    section = section_by_id(version.document, section_id) if version else None
    if section is None:
        raise Http404("This pathway version has no section by that identifier.")
    return section


def _section_page(version, section, answers, completed, fixed):
    blocks, activity_open = open_blocks(section, answers, track_sections(version.document))
    # ✨ A sort leads only to its results, as in the prototype, so completing is not offered beside it until it
    # is in. The linter makes its section's gate require it, so the server refuses completion before then too.
    sort_pending = any(BLOCK_TYPES[block["type"]].scored and block["id"] not in answers for block in blocks)
    # ✨ A link shows the section it leads to exactly as the hub would: its title, its status and whether it is open.
    hub = hub_for(track_sections(version.document), answers, completed)
    states = {state.id: state for state in hub.sections}
    return {
        "pathway": {
            "version_id": version.pk,
            "scale_points": SCALE_POINTS,
            "long_text_max_length": LONG_TEXT_MAX_LENGTH,
        },
        "section": {
            "id": section["id"],
            "title": text_for(section["title"], "participant"),
            "estimate": states[section["id"]].estimate,
            "blocks": [_block_for_participant(version.document, block, answers, fixed, states) for block in blocks],
        },
        "is_complete": section["id"] in completed,
        "holds_fixed_answers": any(block["id"] in fixed for block in blocks),
        "offers_completion": activity_open and not sort_pending,
        "unmet": unmet(section, answers),
    }


def _published_version(posted):
    """✨ The pathway version a form names, provided it has been published; otherwise None."""
    if not (posted or "").isdigit():
        return None
    return PathwayVersion.objects.filter(pk=int(posted), publications__isnull=False).distinct().first()


def _block_for_participant(document, block, answers, fixed, states):
    """✨ One block as its template needs it. `states` are the track's sections as the hub sees them, keyed by
    identifier; a link to a section outside the participant's track has no state and shows nothing."""
    widget = BLOCK_TYPES[block["type"]].widget
    return {
        "id": block["id"],
        "type": block["type"],
        "template": f"engine/blocks/{block['type']}.html",
        "variant": block.get("variant", "plain"),
        "text": authored_text(block, "participant"),
        "answer": answers.get(block["id"]),
        "is_fixed": block["id"] in fixed,
        "widget": widget(document, "participant") if widget else None,
        "link": states.get(block["section"]) if block["type"] == "section_link" else None,
    }
