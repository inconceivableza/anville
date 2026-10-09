# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The demo notice (ticket 26, step 12a).

A demo deployment's sign-up is open (ticket 37), so the homepage and the sign-up page say plainly that it is a demo,
that visitors should use made-up details, and that what they enter may be wiped. The deployment turns it on from the
environment; a production deployment never does.
"""

import pytest

NOTICE = "This is a demo. Use made-up details, not your own: anything entered here may be wiped."


@pytest.fixture
def a_demo(settings):
    settings.ANVILLE_DEMO_NOTICE = NOTICE


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
