# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The hub's next-step photos (fix-8, fix-12): the panel takes the look of what it shows, so the stylesheet can give
each its own photo: the section that is next, or else the answers it waits on, the coach it waits on, or nothing
waiting. Which photo each look shows, one per subject, is a hand check (docs/manual-checks.md, sprint-3c-r3-fix-8).
Every photo the site shows has a credit line."""

import re

import pytest

from engine.views import SITE_PHOTO_CREDITS
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_whatever_you_do import (
    complete,
    invite_everyone,
    next_step_panel,
    the_pathway,
    through_to_section_3,
    to_section_2,
)


def as_authored(document):
    """✨ The pathway unchanged."""
    return document


def with_section_4_waiting_on_more_than_the_coach(document):
    """✨ Section 4 made to require a section that can never open, so once Section 3 is done nothing is next and
    nothing waits on the coach alone."""
    calling = next(section for section in document["content"]["sections"] if section["id"] == "calling")
    calling["requires"].append("growth")  # ✨ which requires Section 4 in turn
    return document


def waiting_on_answers(client):
    """✨ Section 3 done while Section 2 waits on the people invited, and Section 4 on the coach too."""
    to_section_2(client)
    invite_everyone(client)
    complete(client, "shape")


def section_3_done(client):
    """✨ Sections 1 to 3 done, with the coach's link out and unanswered."""
    through_to_section_3(client)
    complete(client, "shape")


# ✨ Each state of the panel: how the pathway is changed for it, how it is reached, and the look it takes.
STATES = {
    "a section next": (as_authored, through_to_section_3, "look-section-shape"),
    "waiting on answers": (as_authored, waiting_on_answers, "look-answers"),
    "waiting on the coach": (as_authored, section_3_done, "look-coach"),
    "nothing waiting": (with_section_4_waiting_on_more_than_the_coach, section_3_done, "look-rest"),
}


@pytest.mark.django_db
@pytest.mark.parametrize("state", STATES)
def test_the_next_step_takes_the_look_of_its_section_or_else_of_what_it_waits_on(
    signed_in_client, load_pathway, state  # noqa: F811
):
    changed, reach, look = STATES[state]
    load_pathway(changed(the_pathway()))
    reach(signed_in_client)

    panel = next_step_panel(signed_in_client)

    assert re.match(rf'<(section|div) class="panel next {look}">', panel)


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
