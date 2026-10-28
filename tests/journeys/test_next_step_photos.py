# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The hub's next-step photos (fix-8): each state and each step its own photo, none used twice. How each looks is a
hand check (docs/manual-checks.md)."""

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from engine.views import SITE_PHOTO_CREDITS, next_look
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_onboarding_wizard import DOCUMENT, through_the_wizard

ROOT = Path(__file__).resolve().parents[2]
STYLESHEET = (ROOT / "frontend/src/styles.css").read_text(encoding="utf-8")
PATHWAY = json.loads((ROOT / "pathways/whatever-you-do.json").read_text(encoding="utf-8"))


def _hub(next_id=None, waiting=None):
    return SimpleNamespace(next_step=SimpleNamespace(id=next_id) if next_id else None, waiting_on_answers=waiting)


def _photos_by_look():
    """✨ The photo the stylesheet gives each `.next.look-*` class, read from its source."""
    rule = r'\.next\.(look-[\w-]+)\s*\{\s*background-image: url\("\.\./img/([\w-]+\.jpg)"\)'
    return dict(re.findall(rule, STYLESHEET))


def test_the_next_step_takes_the_look_of_its_section_or_else_of_what_it_waits_on():
    assert next_look(_hub("calling"), coach_wait=None) == "look-section-calling"
    assert next_look(_hub(waiting=object()), coach_wait=object()) == "look-answers"
    assert next_look(_hub(), coach_wait=object()) == "look-coach"
    assert next_look(_hub(), coach_wait=None) == "look-rest"


def test_the_coach_takes_the_coach_cards_old_photo_and_waiting_on_answers_the_voices_cards():
    photos = _photos_by_look()

    assert photos["look-coach"] == "mentor.jpg"
    assert photos["look-answers"] == "friends.jpg"


def test_every_section_of_the_pathway_and_every_state_has_a_photo_and_no_photo_stands_twice():
    photos = _photos_by_look()
    sections = [s["id"] for s in PATHWAY["content"]["sections"] if "side_card" not in s and s["id"] != "onboarding"]

    for look in [f"look-section-{section}" for section in sections] + ["look-coach", "look-answers", "look-rest"]:
        assert look in photos, look
    assert len(set(photos.values())) == len(photos)


@pytest.mark.django_db
def test_the_hub_panel_carries_its_look_in_its_class(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(json.loads(DOCUMENT.read_text(encoding="utf-8")))
    through_the_wizard(signed_in_client)

    page = signed_in_client.get("/hub/").content.decode()

    assert re.search(r'<(section|div) class="panel next look-[\w-]+"', page)


def test_every_photo_the_next_step_can_show_has_a_credit_line():
    # ✨ By a word of each credit's subject, as the lines are the content owner's to reword.
    credits = " ".join(SITE_PHOTO_CREDITS)

    for subject in ("clay", "carpenter", "Bible", "two friends talking", "row of friends", "misty hills", "notebook"):
        assert subject in credits, subject
