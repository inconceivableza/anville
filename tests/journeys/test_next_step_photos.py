# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The hub's next-step photos (fix-8, fix-12): one photo per subject. The coach, as the next step or in its
wait, has one; the trusted voices, as the next step or waiting on answers, another; every other step and nothing
waiting its own. How each looks is a hand check (docs/manual-checks.md)."""

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
    rule = r'((?:\.next\.look-[\w-]+,?\s*)+)\{\s*background-image: url\("\.\./img/([\w-]+\.jpg)"\)'
    found = re.findall(rule, STYLESHEET)
    return {look: photo for selectors, photo in found for look in re.findall(r"look-[\w-]+", selectors)}


def test_the_next_step_takes_the_look_of_its_section_or_else_of_what_it_waits_on():
    assert next_look(_hub("calling"), coach_wait=None) == "look-section-calling"
    assert next_look(_hub(waiting=object()), coach_wait=object()) == "look-answers"
    assert next_look(_hub(), coach_wait=object()) == "look-coach"
    assert next_look(_hub(), coach_wait=None) == "look-rest"


def test_the_coach_and_the_trusted_voices_each_take_one_photo_as_a_step_and_as_a_wait():
    photos = _photos_by_look()

    assert photos["look-coach"] == photos["look-section-walk-with-a-coach"] == "mentor.jpg"
    assert photos["look-answers"] == photos["look-section-trusted-voices"] == "churches.jpg"
    assert "friends.jpg" not in photos.values()


def test_every_section_of_the_pathway_and_every_state_has_a_photo_and_no_subject_shares_one():
    photos = _photos_by_look()
    sections = [s["id"] for s in PATHWAY["content"]["sections"] if s["id"] != "onboarding"]
    pairs = [
        {"look-coach", "look-section-walk-with-a-coach"},
        {"look-answers", "look-section-trusted-voices"},
    ]

    for look in [f"look-section-{section}" for section in sections] + ["look-coach", "look-answers", "look-rest"]:
        assert look in photos, look
    # ✨ One photo per subject: only the two pairs share a photo, so a photo seen twice is a pair or a mistake.
    by_photo = {}
    for look, photo in photos.items():
        by_photo.setdefault(photo, set()).add(look)
    for photo, looks in by_photo.items():
        assert len(looks) == 1 or looks in pairs, photo


def test_a_card_with_its_own_photo_draws_no_stylesheet_photo_under_it():
    # ✨ The first section's card showed the potter's hands until its own photo loaded (fix-12).
    assert re.search(r"\.next\.next:has\(> img\)\s*\{\s*background-image: none;", STYLESHEET)


@pytest.mark.django_db
def test_the_hub_panel_carries_its_look_in_its_class(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(json.loads(DOCUMENT.read_text(encoding="utf-8")))
    through_the_wizard(signed_in_client)

    page = signed_in_client.get("/hub/").content.decode()

    assert re.search(r'<(section|div) class="panel next look-[\w-]+"', page)


def test_every_photo_the_next_step_can_show_has_a_credit_line():
    # ✨ By a word of each credit's subject, as the lines are the content owner's to reword.
    credits = " ".join(SITE_PHOTO_CREDITS)

    for subject in ("clay", "carpenter", "Bible", "two friends talking", "misty hills", "notebook"):
        assert subject in credits, subject


def test_every_photo_the_stylesheet_shows_has_a_credit_line():
    """✨ The hero's photo, by a word of its credit's subject."""
    credits = " ".join(SITE_PHOTO_CREDITS)

    assert "sunhat" in credits


def test_every_calling_in_the_homepages_marquee_has_a_credit_line_and_no_photo_it_dropped_does():
    """✨ v3's callings (29 Oct), by a word of each credit's subject and its photographer, as traced in the photo
    sources. The parent, pastor, student and graduate are in no band of v3's, so their photos are shown nowhere now."""
    credits = " ".join(SITE_PHOTO_CREDITS)

    assert "teacher" in credits
    for dropped in ("baby", "pastor", "headphones", "graduate"):
        assert dropped not in credits, dropped
    credits = " ".join(SITE_PHOTO_CREDITS)

    for subject, by in (
        ("rice paddy", "Nandhu Kumar on Pexels"),
        ("chef", "Pylyp Sukhenko"),
        ("plant", "OPPO Find X5 Pro"),
        ("mechanic", "Kato Blackmore"),
        ("doctor", "Bruno Rodrigues"),
        ("builder", "Josh Olalde"),
        ("grandmother", "CDC"),
        ("artist", "Vitaly Gariev"),
        ("laptop", "Andrew Neel"),
        ("scientist", "National Cancer Institute"),
        ("fisherman", "Willian Justen de Vasconcellos"),
        ("carer", "Age Cymru"),
    ):
        assert re.search(rf"Photograph of [^.]*\b{subject}\b[^.]*, by {by}", credits), subject
