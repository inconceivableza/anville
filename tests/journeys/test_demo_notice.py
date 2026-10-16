# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The demo notice (ticket 26, step 12a, and ticket 46).

A demo deployment's sign-up is open (ticket 37), so the homepage and the sign-up page say plainly that it is a demo,
that visitors should use made-up details, and that what they enter may be wiped. The deployment turns it on from the
environment; a production deployment never does.

Observers and coaches arrive from their links without seeing the homepage, and enter data too, so their landing pages
and the hub show the full notice as well; every other page shows a smaller one, and none shows both (ticket 46).
"""

import json

import pytest
from django.test import Client

from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_answers import answer
from tests.journeys.test_coach_checklist import choose
from tests.journeys.test_coach_link import issue_coach_link, with_a_coach_and_contacts
from tests.journeys.test_contact_list import JO, PRIYA, save_contacts
from tests.journeys.test_hub import a_fresh_participant
from tests.journeys.test_invitations import issue_link
from tests.journeys.test_observer_landing import claim

NOTICE = "This is a demo. Use made-up details, not your own: anything entered here may be wiped."
FULL, SMALLER = 'class="demo-notice"', 'class="demo-strip"'


@pytest.fixture
def a_demo(settings):
    settings.ANVILLE_DEMO_NOTICE = NOTICE


def pages_of_a_pathway(client, load_pathway):
    """✨ Every kind of page beyond the homepage and the account pages, as each person reaching it sees it: the
    participant's hub, a section page and results, the observer's landing page and own page, and the coach's page."""
    load_pathway(with_a_coach_and_contacts())
    a_fresh_participant(client, "participant@example.com")
    save_contacts(client, JO, PRIYA)
    assert choose(client).status_code == 200
    observer = Client()
    claim(observer, issue_link(client, "Priya"))
    pages = {
        "hub": client.get("/hub/"),
        "section": client.get("/sections/onboarding/"),
        "observer landing": Client().get(issue_link(client, "Jo")),
        "observer's own": observer.get("/observe/"),
        "coach": Client().get(issue_coach_link(client)),
    }
    load_pathway(sort_pathway())
    a_fresh_participant(client, "sorted@example.com")
    client.post("/sections/onboarding/complete/")
    answer(client, "strengths-sort", json.dumps(complete_sort()), section="strengths")
    pages["results"] = client.get("/results/strengths-sort/")
    assert all(page.status_code == 200 for page in pages.values())
    return {name: page.content.decode() for name, page in pages.items()}


@pytest.mark.django_db
def test_the_hub_and_the_pages_observers_and_coaches_land_on_show_the_full_notice(a_demo, client, load_pathway):
    pages = pages_of_a_pathway(client, load_pathway)

    for name in ("hub", "observer landing", "coach"):
        assert FULL in pages[name] and NOTICE in pages[name], name
        assert SMALLER not in pages[name], name


@pytest.mark.django_db
def test_every_other_page_shows_the_smaller_notice_alone(a_demo, client, load_pathway):
    pages = pages_of_a_pathway(client, load_pathway)

    for name in ("section", "results", "observer's own"):
        assert SMALLER in pages[name], name
        assert FULL not in pages[name], name


@pytest.mark.django_db
def test_with_no_notice_set_no_page_says_it_is_a_demo(client, load_pathway):
    for name, page in pages_of_a_pathway(client, load_pathway).items():
        assert "demo-notice" not in page and "demo-strip" not in page, name


@pytest.mark.django_db
@pytest.mark.parametrize("page", ["/", "/accounts/signup/", "/accounts/login/"])
def test_a_demo_says_so_where_people_arrive_and_sign_up(a_demo, client, page):
    shown = client.get(page).content.decode()

    assert 'class="demo-notice"' in shown
    assert NOTICE in shown


@pytest.mark.django_db
@pytest.mark.parametrize("page", ["/", "/accounts/signup/", "/accounts/login/"])
def test_with_no_notice_set_nothing_is_said(client, page):
    assert "demo-notice" not in client.get(page).content.decode()


@pytest.mark.django_db
def test_the_notice_is_shown_as_written(settings, client):
    settings.ANVILLE_DEMO_NOTICE = "A demo <for testing> & nothing else"

    shown = client.get("/accounts/signup/").content.decode()

    assert "A demo &lt;for testing&gt; &amp; nothing else" in shown
