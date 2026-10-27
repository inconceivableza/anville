# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Finishing a section from the end of its part (ticket 88): the strengths evaluation is the last thing in *Whatever
You Do*'s Section 1, so its results page finishes Section 1, and beside that sends a participant without enough
answers to invite people rather than to a comparison they cannot see yet. Wording and layout are hand checks."""

import re

import pytest
from django.test import Client
from django.utils.html import escape

from engine.hub import section_by_id
from engine.models import Response
from tests.documents import complete_sort, sort_pathway
from tests.journeys.pages import main_of
from tests.journeys.test_hub import signed_in_client  # noqa: F401 (a fixture)
from tests.journeys.test_invitations import issue_link
from tests.journeys.test_observer_assessment import send
from tests.journeys.test_observer_landing import claim
from tests.journeys.test_results import STRENGTHS, submit_sort
from tests.journeys.test_whatever_you_do import answer_onboarding, people_answer, the_pathway
from tests.journeys.test_whatever_you_do_faithful_port import a_whole_sort, complete, submit_the_sort

RESULTS = "/results/strengths-sort/"
FINISH_SECTION_1 = 'action="/sections/designed/complete/'  # ✨ its refusal's place after it (fix-2)


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    """✨ A participant of *Whatever You Do* with Before we begin done and the strengths evaluation in."""
    load_pathway(the_pathway())
    answer_onboarding(signed_in_client)
    complete(signed_in_client, "onboarding")
    submit_the_sort(signed_in_client)
    return signed_in_client


def results_page(client):
    return main_of(client.get(RESULTS).content.decode())


def section_1_label():
    section = next(section for section in the_pathway()["content"]["sections"] if section["id"] == "designed")
    return section["complete_label"]


@pytest.mark.django_db
def test_until_section_1_is_complete_its_results_finish_it_and_land_on_the_hub(participant):
    page = results_page(participant)
    assert FINISH_SECTION_1 in page
    assert escape(section_1_label()) in page

    finished = participant.post("/sections/designed/complete/")

    assert (finished.status_code, finished.url) == (303, "/hub/")
    assert "designed" in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_with_javascript_a_refused_finish_comes_back_into_a_place_beneath_it_on_the_results_page(participant):
    """✨ fix-2: htmx swaps a refusal into the element the form names, which must be on this page."""
    page = results_page(participant)
    form = re.search(r'<form [^>]*action="/sections/designed/complete/[^"]*"[^>]*>', page).group(0)

    target = re.search(r'hx-target="#([^"]+)"', form).group(1)

    assert f'id="{target}"' in page


@pytest.mark.django_db
def test_once_section_1_is_complete_its_results_offer_no_finish_and_no_second_way_back(participant):
    """✨ Ticket 88's "Back to the hub" in the finish's place gave way to the page's one way back, at its top (ticket
    96)."""
    assert FINISH_SECTION_1 in results_page(participant)

    complete(participant, "designed")

    page = results_page(participant)
    assert FINISH_SECTION_1 not in page
    assert 'href="/hub/"' not in page


def a_part_of_calling(signed_in_client, load_pathway, last):  # noqa: F811
    """✨ The test pathway's calling section linking to the Strengths assessment as its part, the link its last block
    if `last`, or else followed by its statement; onboarding done and the sort in."""
    document = sort_pathway()
    calling, strengths = (section_by_id(document, section_id) for section_id in ("calling", STRENGTHS))
    strengths["part_of"] = "calling"
    link = {"id": "to-strengths", "type": "section_signpost", "section": STRENGTHS}
    calling["blocks"].insert(len(calling["blocks"]) if last else 0, link)
    load_pathway(document)
    signed_in_client.post("/sections/onboarding/complete/")
    submit_sort(signed_in_client, complete_sort())
    return signed_in_client


@pytest.mark.django_db
def test_in_any_pathway_a_part_ending_its_section_offers_that_sections_finish_refused_by_its_gate(
    signed_in_client, load_pathway  # noqa: F811
):
    client = a_part_of_calling(signed_in_client, load_pathway, last=True)
    assert 'action="/sections/calling/complete/"' in results_page(client)

    refused = client.post("/sections/calling/complete/")  # ✨ its statement is not yet written

    assert refused.status_code == 400
    assert "calling" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_a_part_with_more_of_its_section_after_it_offers_no_finish_as_in_the_faithful_port(
    signed_in_client, load_pathway  # noqa: F811
):
    client = a_part_of_calling(signed_in_client, load_pathway, last=False)

    page = results_page(client)

    assert "/complete/" not in page
    assert 'action="/results/strengths-sort/comparison/visit/"' in page


def sections_and_comparison(page):
    """✨ Where the results page's outline button leads: Five trusted voices' page, or the press on to the comparison."""
    return ("/sections/trusted-voices/" in page, 'action="/results/strengths-sort/comparison/visit/"' in page)


@pytest.mark.django_db
def test_below_the_minimum_the_results_lead_to_invite_people_and_from_it_to_the_comparison(participant):
    people_answer(participant, count=2)
    assert sections_and_comparison(results_page(participant)) == (True, False)

    third = Client()  # ✨ the third person on the list answers, from their own browser
    claim(third, issue_link(participant, "Person 2"))
    assert send(third, a_whole_sort()).status_code == 303

    assert sections_and_comparison(results_page(participant)) == (False, True)
