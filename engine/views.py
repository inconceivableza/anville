from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from engine.document import text_for
from engine.models import Publication

# ✨ The text each block type shows. Later tickets replace this with real block rendering.
_BLOCK_TEXT = {"rich_text": "body", "long_text": "prompt"}


@login_required
def hub(request):
    version = Publication.current_version()
    pathway = _for_participant(version.document) if version else None
    return render(request, "engine/hub.html", {"pathway": pathway})


def _for_participant(document):
    sections = [
        {
            "title": text_for(section["title"], "participant"),
            "blocks": [text_for(block[_BLOCK_TEXT[block["type"]]], "participant") for block in section["blocks"]],
        }
        for section in document["content"]["sections"]
    ]
    if not any(section["blocks"] for section in sections):
        return None  # ✨ sections with no content render as the empty state, never a hidden fallback
    return {"title": text_for(document["title"], "participant"), "sections": sections}
