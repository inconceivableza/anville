from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from engine.document import (
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
from engine.hub import hub_for, is_locked, section_by_id, track_sections
from engine.models import PathwayVersion, Publication, Response


@login_required
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
def section(request, section_id):
    """✨ One section's blocks. A locked section is refused here, whatever the participant typed in the bar."""
    _, version, answers, completed = _participant(request.user)
    section = _section_or_404(version, section_id)
    if is_locked(section, completed):
        return redirect("hub")
    return render(request, "engine/section.html", _section_page(version, section, answers, completed))


@login_required
@require_POST
def complete_section(request, section_id):
    """✨ The participant's own act of finishing a section, re-checked here rather than trusted to the page."""
    participant_response, version, answers, completed = _participant(request.user)
    section = _section_or_404(version, section_id)
    if is_locked(section, completed):
        return redirect("hub")
    if unmet(section, answers):
        page = _section_page(version, section, answers, completed)
        return render(request, "engine/section.html", {**page, "refused": True}, status=400)

    if participant_response is None:
        participant_response, _ = Response.objects.get_or_create(participant=request.user, version=version)
    participant_response.complete_section(section_id)
    see_other = redirect("hub")
    see_other.status_code = 303  # ✨ after a POST, the browser should GET the hub
    return see_other


@login_required
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
    # ✨ A block in a locked section is as shut as the section page: otherwise a participant could fill a
    # section in without ever opening it, and the lock would be decoration again.
    completed = set(participant_response.completed_sections) if participant_response else set()
    if is_locked(section_of(version.document, block_id), completed):
        return render(request, "engine/save_status.html", {"refusal": "This section is not open yet."}, status=403)
    try:
        value = answer_from_form(block, request.POST.get("value"))
    except AnswerRefused as refused:
        return render(request, "engine/save_status.html", {"refusal": str(refused)}, status=400)

    if participant_response is None:
        participant_response, _ = Response.objects.get_or_create(participant=request.user, version=version)
    participant_response.save_answer(block_id, value)

    if request.headers.get("HX-Request") == "true":
        return render(request, "engine/save_status.html")
    where = reverse("section", args=[section_of(version.document, block_id)["id"]])
    see_other = redirect(f"{where}#block-{block_id}")
    see_other.status_code = 303  # ✨ after a POST, the browser should GET the section again
    return see_other


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


def _section_or_404(version, section_id):
    section = section_by_id(version.document, section_id) if version else None
    if section is None:
        raise Http404("This pathway version has no section by that identifier.")
    return section


def _section_page(version, section, answers, completed):
    blocks, everything_open = _blocks_so_far(section, answers)
    return {
        "pathway": {
            "version_id": version.pk,
            "scale_points": SCALE_POINTS,
            "long_text_max_length": LONG_TEXT_MAX_LENGTH,
        },
        "section": {
            "id": section["id"],
            "title": text_for(section["title"], "participant"),
            "blocks": [_block_for_participant(block, answers) for block in blocks],
        },
        "is_complete": section["id"] in completed,
        "everything_open": everything_open,
        "unmet": unmet(section, answers),
    }


def _blocks_so_far(section, answers):
    """✨ The blocks up to and including the first scripture reading the participant has not confirmed.

    The confirmation opens what is beneath it, and the server decides that on every request: an activity
    a participant has not opened is not in the page at all, so no amount of reading the markup reveals it.
    """
    blocks = []
    for block in section["blocks"]:
        blocks.append(block)
        if block["type"] == "scripture_reading" and not answers.get(block["id"]):
            return blocks, False
    return blocks, True


def _published_version(posted):
    """✨ The pathway version a form names, provided it has been published; otherwise None."""
    if not (posted or "").isdigit():
        return None
    return PathwayVersion.objects.filter(pk=int(posted), publications__isnull=False).distinct().first()


def _block_for_participant(block, answers):
    return {
        "id": block["id"],
        "type": block["type"],
        "template": f"engine/blocks/{block['type']}.html",
        "variant": block.get("variant", "plain"),
        "text": authored_text(block, "participant"),
        "answer": answers.get(block["id"]),
    }
