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
from tests.journeys.test_tie_break import CHOSE_PROPHET, TIED_ON_ONE, answer_every_pair, tie_breaking_pathway

CALLING = "/sections/calling/"


def with_results_in_calling(document):
    """✨ `document` with the Strengths assessment a part of the calling section, which links to it, holding what
    follows, and then shows its results."""
    sections = {section["id"]: section for section in document["content"]["sections"]}
    sections[STRENGTHS]["part_of"] = "calling"
    sections["calling"]["blocks"][:0] = [
        {"id": "to-strengths", "type": "section_link", "section": STRENGTHS, "holds_what_follows": True},
        {"id": "strengths-results", "type": "sort_results", "sort": SORT},
    ]
    return document


@pytest.fixture
def signed_in(client, participant, load_pathway):  # noqa: F811
    """✨ A participant with onboarding complete, on a pathway whose sort can tie one framework alone."""
    load_pathway(with_results_in_calling(tie_breaking_pathway()))
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    return client


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
