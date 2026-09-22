from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from engine.document import LONG_TEXT_MAX_LENGTH, SCALE_POINTS, AnswerRefused, UnknownBlock, answer_from_form, answerable_block, text_for
from engine.models import PathwayVersion, Publication, Response

# ✨ The authored text fields each block type shows, resolved to the participant's wording.
_TEXT_FIELDS = {
    "rich_text": ("label", "body"),
    "long_text": ("prompt",),
    "agreement_scale": ("prompt", "min_label", "max_label"),
}


@login_required
def hub(request):
    participant_response = Response.in_progress(request.user)
    version = participant_response.version if participant_response else Publication.current_version()
    answers = participant_response.answers if participant_response else {}
    pathway = _for_participant(version, answers) if version else None
    return render(request, "engine/hub.html", {"pathway": pathway})


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
    try:
        value = answer_from_form(block, request.POST.get("value"))
    except AnswerRefused as refused:
        return render(request, "engine/save_status.html", {"refusal": str(refused)}, status=400)

    if participant_response is None:
        participant_response, _ = Response.objects.get_or_create(participant=request.user, version=version)
    participant_response.save_answer(block_id, value)

    if request.headers.get("HX-Request") == "true":
        return render(request, "engine/save_status.html")
    see_other = redirect(f"{reverse('hub')}#block-{block_id}")
    see_other.status_code = 303  # ✨ after a POST, the browser should GET the pathway page
    return see_other


def _published_version(posted):
    """✨ The pathway version a form names, provided it has been published; otherwise None."""
    if not (posted or "").isdigit():
        return None
    return PathwayVersion.objects.filter(pk=int(posted), publications__isnull=False).distinct().first()


def _for_participant(version, answers):
    document = version.document
    sections = [
        {
            "title": text_for(section["title"], "participant"),
            "blocks": [_block_for_participant(block, answers) for block in section["blocks"]],
        }
        for section in document["content"]["sections"]
    ]
    if not any(section["blocks"] for section in sections):
        return None  # ✨ sections with no content render as the empty state, never a hidden fallback
    return {
        "title": text_for(document["title"], "participant"),
        "version_id": version.pk,
        "scale_points": SCALE_POINTS,
        "long_text_max_length": LONG_TEXT_MAX_LENGTH,
        "sections": sections,
    }


def _block_for_participant(block, answers):
    return {
        "id": block["id"],
        "type": block["type"],
        "template": f"engine/blocks/{block['type']}.html",
        "variant": block.get("variant", "plain"),
        "text": {
            field: text_for(block[field], "participant") for field in _TEXT_FIELDS[block["type"]] if field in block
        },
        "answer": answers.get(block["id"]),
    }
