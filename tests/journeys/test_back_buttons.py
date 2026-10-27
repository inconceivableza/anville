# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ One way back at the top of every participant page past the wizard, leading to the page's parent (ticket 96): the
hub, for a section or a hub side card; a part's own section, for the part; and for the results and the comparison,
the section holding their signpost, named by its title. Its look, a button rather than a quiet link, is a hand
check."""

import re
from html import unescape

import pytest

from tests.journeys.pages import main_of
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_whatever_you_do import (
    TITLES,
    answer_onboarding,
    participant,  # noqa: F401  (a fixture, used by name)
    people_answer,
    through_section_1,
)
from tests.journeys.test_whatever_you_do_faithful_port import complete, submit_the_sort

RESULTS = "/results/strengths-sort/"
COMPARISON = f"{RESULTS}comparison/"


def links_of(page):
    """✨ Every link in the page's own content, in order, as (its class, its address, its words)."""
    found = re.findall(r'<a ([^>]*)>\s*(.*?)\s*</a>', main_of(page), re.S)
    shown = []
    for attributes, words in found:
        css = re.search(r'class="([^"]*)"', attributes)
        href = re.search(r'href="([^"]*)"', attributes)
        shown.append((css.group(1) if css else "", href.group(1) if href else None, unescape(words)))
    return shown


def the_way_back(client, address):
    """✨ The page's one way back, as (its address, its words), checked to be its first link and its only back button."""
    links = links_of(client.get(address).content.decode())
    backs = [link for link in links if "back-button" in link[0].split()]
    assert len(backs) == 1, backs
    assert links[0] == backs[0], links[:2]
    return backs[0][1:]


def leads_elsewhere_to(client, address, href):
    """✨ The links other than the way back on the page at `address` that lead to `href`."""
    links = links_of(client.get(address).content.decode())
    return [link for link in links[1:] if link[1] == href]


@pytest.mark.django_db
def test_the_comparisons_one_way_back_leads_to_the_section_holding_its_signpost(participant):  # noqa: F811
    client = through_section_1(participant)

    href, words = the_way_back(client, COMPARISON)

    assert href == "/sections/others/"
    assert TITLES["others"] in words
    assert leads_elsewhere_to(client, COMPARISON, RESULTS) == []
    assert leads_elsewhere_to(client, COMPARISON, "/sections/designed/") == []


@pytest.mark.django_db
def test_while_that_section_is_locked_the_comparison_leads_back_as_its_results_do(participant):  # noqa: F811
    """✨ Section 2 waits on Section 1, but the comparison is open to anyone with a result."""
    answer_onboarding(participant)
    complete(participant, "onboarding")
    submit_the_sort(participant)

    assert the_way_back(participant, COMPARISON) == the_way_back(participant, RESULTS)
    assert the_way_back(participant, COMPARISON)[0] == "/sections/designed/"


@pytest.mark.django_db
def test_the_results_pages_one_way_back_leads_to_the_section_holding_its_signpost(participant):  # noqa: F811
    """✨ Once Section 1 is finished, its "Back to the hub" at the foot gives way to it."""
    client = through_section_1(participant)

    href, words = the_way_back(client, RESULTS)

    assert href == "/sections/designed/"
    assert TITLES["designed"] in words
    assert leads_elsewhere_to(client, RESULTS, "/hub/") == []


@pytest.mark.django_db
def test_a_comparison_that_shows_ends_on_to_the_reflection_with_the_top_button_kept(participant):  # noqa: F811
    """✨ Fix-18: the second exception to one way back per page. Section 2 open, the end leads on to its reflection, at
    the field's anchor, and the top back button stays."""
    client = through_section_1(participant)
    people_answer(client)

    page = client.get(COMPARISON).content.decode()

    assert the_way_back(client, COMPARISON)[0] == "/sections/others/"
    assert '<a class="pill" href="/sections/others/#block-gifts-summary">On to your reflection →</a>' in page


@pytest.mark.django_db
def test_while_section_2_is_locked_the_comparisons_end_leads_where_its_top_button_does(participant):  # noqa: F811
    answer_onboarding(participant)
    complete(participant, "onboarding")
    submit_the_sort(participant)
    people_answer(participant)

    page = participant.get(COMPARISON).content.decode()
    backs = re.findall(r'<a class="pill ghost back-button" href="[^"]*">[^<]*</a>', page)

    assert len(backs) == 2 and backs[0] == backs[1]
    assert "On to your reflection" not in page


# ✨ Each page by its address, with where its way back leads and the words that must name it.
SECTION_PAGES = {
    "a section": ("/sections/designed/", "/hub/", "the hub"),
    "the part": ("/sections/strengths/", "/sections/designed/", TITLES["designed"]),
    "Walk with a coach": ("/sections/walk-with-a-coach/", "/hub/", "the hub"),
    "Five trusted voices": ("/sections/trusted-voices/", "/hub/", "the hub"),
}


@pytest.mark.django_db
@pytest.mark.parametrize("page", SECTION_PAGES)
def test_a_section_the_part_and_each_side_card_lead_back_to_their_parent(participant, page):  # noqa: F811
    address, parent, title = SECTION_PAGES[page]
    answer_onboarding(participant)
    complete(participant, "onboarding")

    href, words = the_way_back(participant, address)

    assert href == parent
    assert title in words
