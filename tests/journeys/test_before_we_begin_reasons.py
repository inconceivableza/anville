# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Before we begin's reason takes one or more choices (ticket 112): v3's cards, each a checkbox, every one ticked
kept as its option's identifier. How the cards look is a hand check (docs/manual-checks.md)."""

import re

import pytest

from engine.models import Response
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_onboarding_wizard import (  # noqa: F401  (participant is a fixture, used by name)
    WIZARD,
    answer,
    before_we_begin,
    participant,
)


def ticked(page):
    """✨ The identifiers of the reason's cards a page shows ticked, in the order shown."""
    return re.findall(r'<input type="checkbox" name="value" value="([^"]+)" checked>', page)


def reason_options():
    [reason] = [block for block in before_we_begin()["blocks"] if block["id"] == "reason"]
    return [option["id"] for option in reason["options"]]


@pytest.mark.django_db
def test_the_reason_keeps_every_choice_ticked_and_shows_each_ticked_again(participant):
    chosen = [reason_options()[2], reason_options()[5]]

    saved = answer(participant, "reason", chosen)

    assert saved.status_code in (200, 303)
    page = participant.get(WIZARD).content.decode()
    assert "<select" not in page
    assert len(re.findall(r'<input type="checkbox" name="value"', page)) == len(reason_options())
    assert ticked(page) == chosen
    assert Response.objects.get().answers["reason"] == chosen
