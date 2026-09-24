from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

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
from engine.hub import hub_for, is_locked, open_blocks, section_by_id, track_sections
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
    return _see_other("hub")


@login_required
@require_POST
def reopen_section(request, section_id):
    """✨ The participant taking back their own completion. Their answers stay exactly as they left them."""
    participant_response, version, _, _ = _participant(request.user)
    _section_or_404(version, section_id)
    if participant_response is not None:
        participant_response.reopen_section(section_id)
    return _see_other("hub")


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
    # ✨ A block a participant has not reached is as shut as the page that would have shown it, whether a
    # lock or an unconfirmed reading holds it. Otherwise they could fill it in without ever opening it, and
    # both would be decoration again, which is exactly the prototype's mistake.
    section = section_of(version.document, block_id)
    answers = participant_response.answers if participant_response else {}
    completed = set(participant_response.completed_sections) if participant_response else set()
    reached, _ = open_blocks(section, answers)
    if is_locked(section, completed) or block not in reached:
        return render(request, "engine/save_status.html", {"refusal": "This is not open yet."}, status=403)
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
    else:
        participant_response.save_answer(block_id, value)
    # ✨ The row was updated in place, so this object's answers are a step behind what was just stored.
    answers = {**answers, block_id: value}

    if request.headers.get("HX-Request") == "true":
        return render(request, "engine/save_result.html", _section_page(version, section, answers, completed))
    return _see_other(f"{reverse('section', args=[section['id']])}#block-{block_id}")


def _see_other(where, *args):
    """✨ After a POST, the browser should GET the page it lands on rather than repeat the POST."""
    response = redirect(where, *args)
    response.status_code = 303
    return response


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
    blocks, activity_open = open_blocks(section, answers)
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
        "activity_open": activity_open,
        "unmet": unmet(section, answers),
    }


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
