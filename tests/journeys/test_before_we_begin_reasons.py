# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Before we begin's reason takes one or more choices (ticket 112): v3's cards, each a checkbox, every one ticked
kept as its option's identifier. How the cards look is a hand check (docs/manual-checks.md)."""

import re

import pytest

from engine.models import Publication, Response
from tests.journeys.pages import gate_checklist
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_messages_after_a_press import gate_message
from tests.journeys.test_onboarding_wizard import (  # noqa: F401  (participant is a fixture, used by name)
    RATINGS_PAGE,
    WIZARD,
    answer,
    before_we_begin,
    participant,
)

CONTINUE = "/sections/onboarding/pages/1/continue/"
# ✨ What the form sends first, before a value for each card ticked, so that it says when none is.
BLANK = ""


def ticked(page):
    """✨ The identifiers of the reason's cards a page shows ticked, in the order shown."""
    return re.findall(r'<input type="checkbox" [^>]*value="([^"]+)" checked>', page)


def reason_options():
    [reason] = [block for block in before_we_begin()["blocks"] if block["id"] == "reason"]
    return [option["id"] for option in reason["options"]]


@pytest.mark.django_db
def test_the_reason_keeps_every_choice_ticked_and_shows_each_ticked_again(participant):
    chosen = [reason_options()[2], reason_options()[5]]

    saved = answer(participant, "reason", [BLANK, *chosen])

    assert saved.status_code in (200, 303)
    page = participant.get(WIZARD).content.decode()
    assert "<select" not in page
    assert len(re.findall(r'<input type="checkbox" ', page)) == len(reason_options())
    assert ticked(page) == chosen
    assert Response.objects.get().answers["reason"] == chosen


@pytest.mark.django_db
@pytest.mark.parametrize("sent", [["exploring", "lottery-win"], ["exploring", "exploring"]], ids=["unknown", "twice"])
def test_a_reason_not_among_its_options_or_sent_twice_is_refused_and_the_one_before_kept(participant, sent):
    answer(participant, "reason", ["job-change"])

    refused = answer(participant, "reason", sent)

    assert refused.status_code == 400
    assert Response.objects.get().answers["reason"] == ["job-change"]


@pytest.mark.django_db
def test_unticking_every_reason_takes_it_back_so_continue_is_refused_until_one_is_ticked_again(participant):
    answer(participant, "reason", [BLANK, "exploring"])

    answer(participant, "reason", [BLANK])
    refused = participant.post(CONTINUE)

    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode()) == {gate_message("onboarding", "reason"): False}
    assert ticked(participant.get(WIZARD).content.decode()) == []
    answer(participant, "reason", [BLANK, "exploring", "retirement"])
    assert participant.post(CONTINUE).url == RATINGS_PAGE


@pytest.mark.django_db
def test_a_reason_stored_as_one_choice_before_it_took_many_shows_as_that_card_ticked_and_goes_on(
    participant, django_user_model
):
    """✨ As a single select stored it, before ticket 112."""
    Response.objects.create(
        participant=django_user_model.objects.get(),
        version=Publication.current_version(),
        answers={"reason": "exploring"},
    )

    page = participant.get(WIZARD).content.decode()

    assert ticked(page) == ["exploring"]
    assert participant.post(CONTINUE).url == RATINGS_PAGE
