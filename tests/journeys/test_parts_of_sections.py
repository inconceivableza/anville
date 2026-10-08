"""✨ A section that is a part of another, as the Strengths assessment is a part of Section 1 (ticket 41b).

As in the original prototype, where the assessment sits inside Section 1: it is listed under that section, has no
completion of its own, and everything leaving it leads back to that section. The calling section stands for Section 1.
"""

import re

import pytest

from tests.documents import complete_sort, sort_pathway
from tests.journeys.pages import main_of
from tests.journeys.test_answers import participant  # noqa: F401 (a fixture)
from tests.journeys.test_consent import give_consent
from tests.journeys.test_results import SORT, STRENGTHS, results, submit_sort

CALLING = "/sections/calling/"
CALLING_TITLE = "Putting your calling into words"


@pytest.fixture
def signed_in(client, participant, load_pathway):  # noqa: F811
    """✨ A participant with onboarding complete, so the calling section and its part, the Strengths assessment, are
    open."""
    document = sort_pathway()
    next(section for section in document["content"]["sections"] if section["id"] == STRENGTHS)["part_of"] = "calling"
    load_pathway(document)
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    return client


def listed_under_calling(page):
    """✨ What is linked from the list nested in the calling section's entry: from its title to the end of that list."""
    entry = re.search(rf'-title" href="{CALLING}".*?</ol>', page, re.S)
    return re.findall(r'<ol[^>]*>.*?href="/sections/([\w-]+)/"', entry.group(0), re.S) if entry else []


@pytest.mark.django_db
def test_a_part_offers_no_completion_of_its_own_even_once_its_gate_passes(signed_in):
    submit_sort(signed_in, complete_sort())

    page = signed_in.get(f"/sections/{STRENGTHS}/").content.decode()

    assert f"/sections/{STRENGTHS}/complete/" not in page
    assert signed_in.post(f"/sections/{STRENGTHS}/complete/").status_code == 404


@pytest.mark.django_db
def test_the_hub_and_the_sidebar_list_a_part_within_its_sections_entry(signed_in):
    page = signed_in.get("/hub/").content.decode()
    sidebar = re.search(r'<nav class="pathway-nav".*?</nav>', page, re.S).group(0)

    assert listed_under_calling(main_of(page)) == [STRENGTHS]
    assert listed_under_calling(sidebar) == [STRENGTHS]
    assert main_of(page).count(f'href="/sections/{STRENGTHS}/"') == 1


@pytest.mark.django_db
def test_a_parts_page_and_its_results_lead_back_to_the_section_it_is_a_part_of(signed_in):
    """✨ This replaces ticket 09's call that the results page leads back to the Strengths assessment."""
    back = f'<a href="{CALLING}">← Back to {CALLING_TITLE}</a>'
    submit_sort(signed_in, complete_sort())

    part = main_of(signed_in.get(f"/sections/{STRENGTHS}/").content.decode())
    shown = main_of(results(signed_in).content.decode())

    assert back in part
    assert "← Back to the hub" not in part
    assert back in shown


@pytest.mark.django_db
def test_the_comparison_ends_with_a_way_back_to_the_section_its_sort_is_a_part_of(signed_in):
    """✨ The prototype's "Return to workbook →", naming the section, since "the Workbook" is now a section of its own.
    Its wording and arrow are a hand check."""
    submit_sort(signed_in, complete_sort())

    page = main_of(signed_in.get(f"/results/{SORT}/comparison/").content.decode())

    links = re.findall(r'<a [^>]*href="([^"]*)"[^>]*>\s*(.*?)\s*</a>', page, re.S)
    href, label = links[-1]
    assert href == CALLING
    assert CALLING_TITLE in label
