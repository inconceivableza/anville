# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A sort's results shown in full in a section of their own choosing, as Section 1 shows the Strengths assessment's
right after its link (ticket 57). The calling section stands for Section 1, and the Strengths assessment is its part."""

import re

import pytest

from engine.models import Response, Result
from tests.documents import complete_sort, sort_pathway, with_a_tie_break
from tests.journeys.pages import main_of
from tests.journeys.test_answers import participant  # noqa: F401 (a fixture)
from tests.journeys.test_consent import give_consent
from tests.journeys.test_results import SORT, STRENGTHS, results, submit_sort
from tests.journeys.test_tie_break import (
    CHOSE_PROPHET,
    EVEN,
    GENERALIST,
    TIED_ON_ONE,
    answer_every_pair,
    tie_breaking_pathway,
)

CALLING = "/sections/calling/"


def with_results_in_calling(document):
    """✨ `document` with the Strengths assessment a part of the calling section, which links to it, holding what
    follows, and then shows its results."""
    sections = {section["id"]: section for section in document["content"]["sections"]}
    sections[STRENGTHS]["part_of"] = "calling"
    sections["calling"]["blocks"][:0] = [
        {"id": "to-strengths", "type": "section_signpost", "section": STRENGTHS, "holds_what_follows": True},
        {"id": "strengths-results", "type": "sort_results", "sort": SORT},
    ]
    return document


def sign_in(client, participant, load_pathway, document):  # noqa: F811
    load_pathway(with_results_in_calling(document))
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    return client


@pytest.fixture
def signed_in(client, participant, load_pathway):  # noqa: F811
    """✨ A participant with onboarding complete, on a pathway whose sort can tie one framework alone."""
    return sign_in(client, participant, load_pathway, tie_breaking_pathway())


def drawn_results(page):
    """✨ The results as drawn, from the generalist's hint to "Compare with how others see you →", each form's token
    set aside, since every page is given a fresh one."""
    shown = re.search(r'<div class="own-results">.*?</form>', main_of(page), re.S)
    return re.sub(r'name="csrfmiddlewaretoken" value="[^"]*"', "", shown.group(0)) if shown else None


@pytest.mark.django_db
def test_once_the_tie_break_is_answered_the_section_draws_the_re_weighted_results_as_the_results_page_does(signed_in):
    answer_every_pair(signed_in, CHOSE_PROPHET)

    in_section = drawn_results(signed_in.get(CALLING).content.decode())

    assert in_section is not None and "The top changed" in in_section
    assert in_section == drawn_results(results(signed_in).content.decode())


@pytest.mark.django_db
def test_a_generalist_is_told_so_in_the_section_as_on_the_results_page(client, participant, load_pathway):  # noqa: F811
    generalist = sign_in(client, participant, load_pathway, with_a_tie_break(sort_pathway(), percent=5, cluster=4))
    submit_sort(generalist, EVEN)

    in_section = drawn_results(generalist.get(CALLING).content.decode())

    assert in_section is not None and GENERALIST in in_section
    assert in_section == drawn_results(results(generalist).content.decode())


@pytest.mark.django_db
def test_while_tie_break_pairs_are_left_the_section_shows_no_results_and_stores_nothing(signed_in):
    submit_sort(signed_in, TIED_ON_ONE)

    shown = signed_in.get(CALLING)

    assert shown.status_code == 200
    page = main_of(shown.content.decode())
    assert drawn_results(page) is None
    assert f'href="/sections/{STRENGTHS}/"' in page
    result = Result.objects.get()
    assert (result.tie_break_answers, result.reweighted) == ([], None)


@pytest.mark.django_db
def test_showing_the_results_in_the_section_stores_the_re_weighted_result_the_results_page_would(signed_in):
    """✨ A result whose re-weighting was never stored, as for one answered before ticket 30c, is stored on its first
    showing, the same whichever page shows it first."""
    answer_every_pair(signed_in, CHOSE_PROPHET)
    stored_after_the_last_pair = Result.objects.get().reweighted
    Result.objects.update(reweighted=None)

    signed_in.get(CALLING)

    assert Result.objects.get().reweighted == stored_after_the_last_pair


@pytest.mark.django_db
def test_the_sections_compare_button_records_the_visit_as_the_results_pages_does(signed_in, participant):  # noqa: F811
    submit_sort(signed_in, complete_sort(x1={"bucket": "not-me", "value": 10}))
    page = main_of(signed_in.get(CALLING).content.decode())
    action = re.search(r'<form class="results-next" method="post" action="([^"]*)"', page).group(1)

    signed_in.post(action)

    assert SORT in Response.objects.get(participant=participant).comparisons_visited
