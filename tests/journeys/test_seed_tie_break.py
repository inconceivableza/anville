# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ `seed_tie_break` makes a made-up participant ready for the tie-break's pairs, and only on a development or demo
system (fix-15)."""

import re
from io import StringIO
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.utils.html import escape

WHATEVER_YOU_DO = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do.json"


@pytest.fixture
def published():
    call_command("load_pathway", str(WHATEVER_YOU_DO), stdout=StringIO())


def printed(text, label):
    """✨ What the command printed after `label: ` on a line of its own."""
    return re.search(rf"^{label}: (.+)$", text, re.MULTILINE)[1]


@pytest.mark.django_db
def test_it_refuses_with_debug_off_and_no_demo_notice(published, settings):
    settings.DEBUG = False
    settings.ANVILLE_DEMO_NOTICE = ""

    with pytest.raises(CommandError):
        call_command("seed_tie_break", "tied-both", stdout=StringIO())

    assert not get_user_model().objects.exists()


@pytest.mark.django_db
def test_it_refuses_on_for_a_scenario_that_does_not_take_it(published, settings):
    settings.DEBUG = True

    with pytest.raises(CommandError, match="tied-both does not take --on"):
        call_command("seed_tie_break", "tied-both", "--on", "pep", stdout=StringIO())

    assert not get_user_model().objects.exists()


@pytest.mark.django_db
def test_the_tied_on_both_participant_signs_in_to_the_first_pair(published, client, settings):
    settings.DEBUG = True
    out = StringIO()
    call_command("seed_tie_break", "tied-both", stdout=out)
    text = out.getvalue()
    first_answer = re.search(r"^  1\. .+: choose “(.+)”$", text, re.MULTILINE)[1]

    signed_in = client.post(
        printed(text, "Sign in at"), {"login": printed(text, "Email"), "password": printed(text, "Password")}, follow=True
    )

    assert signed_in.redirect_chain[-1][0] == "/results/strengths-sort/tie-break/"
    assert "1 of 4" in signed_in.content.decode()
    assert escape(first_answer) in signed_in.content.decode()
