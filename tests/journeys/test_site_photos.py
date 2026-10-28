# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Photos and the new video (ticket 101): the hero's video and poster, the wizard's photo for each page, the hub's
next step's photo and the courtesy credits for them. How each looks is a hand check (docs/manual-checks.md)."""

import json
import re

import pytest
from django.templatetags.static import static

from engine.hub import WizardStep
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_onboarding_wizard import (  # noqa: F401  (participant is a fixture, used by name)
    DOCUMENT,
    RATINGS_PAGE,
    WIZARD,
    participant,
    through_the_first_page,
    through_the_wizard,
)


def _photo_of(page):
    """✨ The photo's number a wizard page's panel names, read from the document."""
    return re.search(r'class="ob-photo ob-photo-(\d+)"', page).group(1)


@pytest.mark.django_db
def test_the_hero_plays_the_new_video_over_its_poster(client):
    page = client.get("/").content.decode()

    assert f'src="{static("hero-landscape.mp4")}"' in page
    assert f'poster="{static("hero-landscape-poster.jpg")}"' in page


@pytest.mark.django_db
def test_each_wizard_page_names_a_different_photo(participant):  # noqa: F811
    first = _photo_of(participant.get(WIZARD).content.decode())
    through_the_first_page(participant)
    second = _photo_of(participant.get(RATINGS_PAGE).content.decode())

    assert first != second


def test_the_steps_photos_differ_one_after_another_and_wrap_within_the_photos_there_are():
    photos = [WizardStep(number, 12).photo for number in range(1, 13)]

    assert all(a != b for a, b in zip(photos, photos[1:]))
    assert set(photos) <= set(range(1, WizardStep.PHOTOS + 1))


@pytest.mark.django_db
def test_the_hub_next_step_has_the_stylesheets_photo_and_the_side_cards_none(
    signed_in_client, load_pathway  # noqa: F811
):
    load_pathway(json.loads(DOCUMENT.read_text(encoding="utf-8")))
    through_the_wizard(signed_in_client)

    page = signed_in_client.get("/hub/").content.decode()

    # ✨ The next step's photo is the stylesheet's behind `.next` (fix-5), so it holds in every state; the side cards
    # have none.
    assert re.search(r'<(section|div) class="panel next"', page)
    assert "side-photo" not in page


@pytest.mark.django_db
def test_the_credits_page_lists_the_video_and_the_churches_photo_as_courtesies(client, load_pathway):
    load_pathway(json.loads(DOCUMENT.read_text(encoding="utf-8")))

    page = client.get("/credits/").content.decode()

    assert "Video by Marian Croitoru from" in page
    assert 'href="https://www.pexels.com/video/healthy-light-landscape-nature-4524595/"' in page
    assert "Photograph of a church gathering with Bibles open, by Sincerely Media on Unsplash." in page
    assert page.count("Photograph of grass from Unsplash.") == 1
