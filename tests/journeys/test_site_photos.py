# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Photos and the new video (ticket 101): the hero's video and poster, the wizard's photo for each page, the hub's
next step's photo and the courtesy credits for them. How each looks is a hand check (docs/manual-checks.md)."""

import json
import re

import pytest
from django.templatetags.static import static
from django.utils.html import escape

from engine.hub import HERO_VIDEO_CREDIT, WIZARD_PHOTOS, WizardStep
from engine.views import SITE_PHOTO_CREDITS
from tests.journeys.test_credits import linked, links
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_onboarding_wizard import (  # noqa: F401  (participant is a fixture, used by name)
    DOCUMENT,
    RATINGS,
    RATINGS_PAGE,
    WELCOME,
    WIZARD,
    answer,
    participant,
    through_the_first_page,
    through_the_wizard,
)


def _photo_of(page):
    """✨ The photo a wizard page's panel shows, read from the document."""
    return re.search(r'<aside class="ob-photo"[^>]*>\s*<img src="([^"]+)"', page).group(1)


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
    assert set(photos) <= set(WIZARD_PHOTOS)


@pytest.mark.django_db
def test_the_hub_next_step_has_the_stylesheets_photo_and_the_side_cards_none(
    signed_in_client, load_pathway  # noqa: F811
):
    load_pathway(json.loads(DOCUMENT.read_text(encoding="utf-8")))
    through_the_wizard(signed_in_client)

    page = signed_in_client.get("/hub/").content.decode()

    # ✨ The next step's photo is the stylesheet's behind `.next` (fix-5), so it holds in every state; the side cards
    # have none.
    assert re.search(r'<(section|div) class="panel next[ "]', page)
    assert "side-photo" not in page


@pytest.mark.django_db
def test_the_credits_page_links_each_credits_author_photo_page_and_licence_listing_each_photo_once(
    client, load_pathway
):
    """✨ sprint-3d-r1-fix-5: the video's, the pathway's own and the site's, each linked as traced to its page, but for
    one whose source was never found, listed as written; and the grass, which the pathway and the wizard both show,
    listed once."""
    document = json.loads(DOCUMENT.read_text(encoding="utf-8"))
    load_pathway(document)

    page = client.get("/credits/").content.decode()

    pathways = [photo["credit"] for photo in document["photos"].values()]
    for credit in [*pathways, HERO_VIDEO_CREDIT, *SITE_PHOTO_CREDITS, *(photo.credit for photo in WIZARD_PHOTOS)]:
        if links(credit):
            assert len(links(credit)) >= 3, credit  # ✨ its author, its page and its licence
            assert all(linked(link, page) for link in links(credit)), credit
        else:
            assert escape(credit.text) in page, credit
    for credit in pathways:
        assert page.count(f'href="{credit["author"]["url"]}"') == 1


@pytest.mark.django_db
def test_the_ratings_step_draws_the_commons_photo_and_a_fifth_step_the_homepage_videos_still(
    signed_in_client, load_pathway  # noqa: F811
):
    """✨ sprint-3d-r1-fix-5. *Whatever You Do*'s welcome is its fourth step, so here its ratings take two pages, making
    the welcome the fifth, whose photo had been credited as a still of the video though it is not one."""
    document = json.loads(DOCUMENT.read_text(encoding="utf-8"))
    before_we_begin = document["content"]["sections"][0]
    before_we_begin["blocks"].insert(5, {"id": "to-more-ratings", "type": "page_break"})
    before_we_begin["wizard_steps"].append(before_we_begin["wizard_steps"][-1])
    load_pathway(document)
    through_the_first_page(signed_in_client)

    assert _photo_of(signed_in_client.get(RATINGS_PAGE).content.decode()) == static("musicians-in-wheat.jpg")

    for rating in RATINGS[:2]:
        answer(signed_in_client, rating, "7")
    signed_in_client.post("/sections/onboarding/pages/2/continue/")
    for rating in RATINGS[2:]:
        answer(signed_in_client, rating, "7")
    signed_in_client.post("/sections/onboarding/complete/")
    welcome = signed_in_client.get(WELCOME).content.decode()
    video = re.search(r'<video id="heroVid"[^>]* poster="([^"]+)"', signed_in_client.get("/").content.decode())
    assert _photo_of(welcome) == video.group(1)
