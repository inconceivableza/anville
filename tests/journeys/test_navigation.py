# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The header on every participant page, and the pathway sidebar it opens (ticket 41a).

The header leads to the hub and lets the participant sign out; the sidebar lists the hub's own sections, from the same
derivation as the hub, so its statuses and locks are the hub's by construction. Observers and the coach have no
account, so their pages have neither. Opening and closing the sidebar without JavaScript is a hand check.
"""

import json
import re

import pytest

from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_answers import answer
from tests.journeys.test_coach_checklist import choose, the_coach_checklist
from tests.journeys.test_coach_link import issue_coach_link, with_a_coach_and_contacts
from tests.journeys.test_contact_list import JO, PRIYA, save_contacts
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import issue_link
from tests.journeys.test_observer_landing import claim

SORT, STRENGTHS, CALLING = "strengths-sort", "strengths", "calling"


def with_a_coach_in_section_1():
    """✨ The test pathway with the sort's section, and Whatever You Do's coach checklist in the calling section, which
    stands for Section 1 here: locked until onboarding is complete, like the coach page it holds."""
    document = sort_pathway()
    calling = next(section for section in document["content"]["sections"] if section["id"] == CALLING)
    calling["blocks"].append(the_coach_checklist())
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(with_a_coach_in_section_1())
    return signed_in_client


@pytest.fixture
def under_way(participant):
    """✨ A participant past onboarding with the sort in, so every page the sidebar leads to has something on it."""
    participant.post("/sections/onboarding/complete/")
    answer(participant, SORT, json.dumps(complete_sort()), section=STRENGTHS)
    return participant


def header_of(page):
    """✨ The participant header, or None on a page without one."""
    found = re.search(r'<header class="site-header".*?</header>', page, re.S)
    return found.group(0) if found else None


def the_header(page):
    """✨ The participant header, which the page must have."""
    header = header_of(page)
    assert header is not None, "no header on the page"
    return header


def sidebar_of(page):
    """✨ The pathway sidebar, or None on a page without one."""
    found = re.search(r'<nav class="pathway-nav".*?</nav>', page, re.S)
    return found.group(0) if found else None


def section_in(sidebar, title):
    """✨ The sidebar's entry for one section, found by its title."""
    assert sidebar is not None, "no sidebar on the page"
    entries = re.findall(r'<li class="pathway-nav-section.*?</li>', sidebar, re.S)
    return next(entry for entry in entries if title in entry)


@pytest.mark.django_db
def test_observers_and_the_coachs_pages_have_no_header_sidebar_or_sign_out_even_in_the_participants_browser(
    signed_in_client, load_pathway  # noqa: F811
):
    """✨ The participant's own browser is the likeliest to open their links, and is signed in."""
    load_pathway(with_a_coach_and_contacts())
    choose(signed_in_client)
    coach_link = issue_coach_link(signed_in_client)
    save_contacts(signed_in_client, JO, PRIYA)
    observer_link = issue_link(signed_in_client, "Jo")
    landing = signed_in_client.get(observer_link).content.decode()
    claim(signed_in_client, observer_link)

    for page in (
        signed_in_client.get(coach_link).content.decode(),
        landing,
        signed_in_client.get("/observe/").content.decode(),
    ):
        assert header_of(page) is None
        assert sidebar_of(page) is None
        assert "/accounts/logout/" not in page


@pytest.mark.django_db
def test_a_locked_section_is_listed_but_its_address_is_nowhere_in_the_sidebar(participant):
    sidebar = sidebar_of(participant.get("/sections/onboarding/").content.decode())

    assert "Locked" in section_in(sidebar, "Putting your calling into words")
    assert "Locked" in section_in(sidebar, "Strengths assessment")
    assert f"/sections/{CALLING}/" not in sidebar  # ✨ the coach page is on it, so not that either
    assert f"/sections/{STRENGTHS}/" not in sidebar


@pytest.mark.django_db
def test_after_onboarding_the_sidebar_shows_statuses_marks_the_current_section_and_leads_everywhere_open(under_way):
    sidebar = sidebar_of(under_way.get(f"/sections/{CALLING}/").content.decode())

    assert "Complete" in section_in(sidebar, "Before we begin")
    assert "In progress" in section_in(sidebar, "Strengths assessment")
    calling = section_in(sidebar, "Putting your calling into words")
    assert "Not started" in calling
    assert 'aria-current="page"' in calling
    assert sidebar.count('aria-current="page"') == 1
    for address in (
        f'href="/sections/{CALLING}/"',
        f'href="/results/{SORT}/"',
        f'href="/results/{SORT}/comparison/"',
        'href="/invitations/"',
        f'href="/sections/{CALLING}/#block-coach"',
    ):
        assert address in sidebar


@pytest.mark.django_db
@pytest.mark.parametrize(
    "address",
    ["/hub/", f"/sections/{CALLING}/", f"/results/{SORT}/", f"/results/{SORT}/comparison/", "/invitations/"],
)
def test_every_participant_page_carries_the_header_with_sign_out_and_the_sidebar(under_way, address):
    page = under_way.get(address).content.decode()

    header = the_header(page)
    assert re.search(r'<a [^>]*href="/hub/"[^>]*>\s*Test Pathway\s*</a>', header)
    assert re.search(r'<form [^>]*method="post"[^>]*action="/accounts/logout/"', header)
    assert sidebar_of(page) is not None


@pytest.mark.django_db
def test_with_the_sidebar_switched_off_the_header_and_sign_out_remain(under_way, settings):
    settings.ANVILLE_SIDEBAR = False

    page = under_way.get(f"/sections/{CALLING}/").content.decode()

    header = the_header(page)
    assert 'href="/hub/"' in header
    assert 'action="/accounts/logout/"' in header
    assert sidebar_of(page) is None
    assert "pathway-nav" not in page


@pytest.mark.django_db
def test_the_credits_page_carries_the_header_only_for_someone_signed_in(under_way):
    """✨ It is public, and reached from every page's footer: a participant gets their way back, a visitor nothing."""
    assert header_of(under_way.get("/credits/").content.decode()) is not None

    under_way.logout()

    assert header_of(under_way.get("/credits/").content.decode()) is None


@pytest.mark.django_db
def test_signing_out_from_the_header_ends_the_session_and_leads_to_the_homepage(under_way):
    header = the_header(under_way.get("/hub/").content.decode())
    action = re.search(r'<form [^>]*action="([^"]+)"', header).group(1)

    signed_out = under_way.post(action)

    assert signed_out.status_code == 302
    assert signed_out.url == "/"
    assert under_way.get("/hub/").url.startswith("/accounts/login/")
