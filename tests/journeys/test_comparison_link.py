# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A comparison link (ticket 67a): a card for the way to the comparison, saying where it stands, whose button is the
results page's "Compare with how others see you →", warning before answer collection freezes as that one does (ADR
0017). "Viewed" is pressing it with at least the minimum in, and is kept once withdrawals unfreeze collection."""

import re

import pytest

from engine.document.blocks import COMPARISON_STATUSES
from engine.models import Response
from tests.documents import complete_sort
from tests.journeys.test_coach_checklist import text
from tests.journeys.test_contact_list import CHRIS, JO, PRIYA, save_contacts
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_observer_assessment import (
    SAM,
    answered_by,
    observed_pathway,
    press_compare,
    withdraw,
)
from tests.journeys.test_results import SORT, submit_sort

CARD = "how-others-see-you"
WAITING, READY, VIEWED = (COMPARISON_STATUSES[state] for state in ("waiting", "ready", "viewed"))


def with_the_card():
    """✨ The observed pathway with the card in the calling section, which opens with onboarding, as the sort's does."""
    document = observed_pathway()
    document["content"]["sections"][1]["blocks"].append(
        {"id": CARD, "type": "comparison_link", "sort": SORT, "title": "How others see you"}
    )
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    """✨ Onboarding complete and four people on the list, none of whom has answered yet."""
    load_pathway(with_the_card())
    save_contacts(signed_in_client, JO, PRIYA, CHRIS, SAM)
    signed_in_client.post("/sections/onboarding/complete/")
    return signed_in_client


def card(client):
    """✨ The card's markup on its section's page, or None when the page shows none."""
    found = re.search(rf'<div id="block-{CARD}".*?</form>.*?</div>', client.get("/sections/calling/").content.decode(), re.S)
    return found.group(0) if found else None


def status(client):
    return text(card(client))


def is_frozen():
    return Response.objects.get().collection_frozen_at is not None


@pytest.mark.django_db
def test_a_press_below_the_minimum_freezes_nothing_and_one_with_it_in_confirmed_freezes_and_reads_viewed(participant):
    submit_sort(participant, complete_sort())
    answered_by(participant, "Jo", "Priya")

    below = press_compare(participant, confirmed=False)

    assert (below.status_code, below["Location"]) == (303, f"/results/{SORT}/comparison/")
    assert not is_frozen()
    assert WAITING.format(answered=2, minimum=3) in status(participant)

    answered_by(participant, "Chris")
    assert press_compare(participant, confirmed=False).status_code == 200
    assert not is_frozen() and VIEWED not in status(participant)
    assert press_compare(participant).status_code == 303

    assert is_frozen()
    assert VIEWED in status(participant)


@pytest.mark.django_db
def test_viewed_stays_once_a_withdrawal_unfreezes_collection(participant):
    submit_sort(participant, complete_sort())
    browsers = answered_by(participant, "Jo", "Priya", "Chris")
    press_compare(participant)

    withdraw(browsers["Jo"])

    assert not is_frozen()
    assert VIEWED in status(participant)


@pytest.mark.django_db
def test_opening_the_comparison_by_its_address_is_not_viewing_it(participant):
    submit_sort(participant, complete_sort())
    answered_by(participant, "Jo", "Priya", "Chris")

    assert participant.get(f"/results/{SORT}/comparison/").status_code == 200

    assert READY in status(participant)
    assert VIEWED not in status(participant)


@pytest.mark.django_db
@pytest.mark.parametrize("htmx", [False, True], ids=["without JavaScript", "with htmx"])
def test_the_cards_press_is_the_results_pages_and_reaches_the_same_freeze_warning(participant, htmx):
    submit_sort(participant, complete_sort())
    answered_by(participant, "Jo", "Priya", "Chris")
    action = re.compile(r'<form[^>]* method="post" action="([^"]+)"')
    on_results = action.findall(participant.get(f"/results/{SORT}/").content.decode())
    on_card = action.search(card(participant)).group(1)
    headers = {"HX-Request": "true"} if htmx else {}

    asked = participant.post(on_card, headers=headers)

    assert on_card in on_results
    assert asked.status_code == 200
    assert asked.templates[0].name == "engine/comparison_confirm.html"
    assert not is_frozen()


@pytest.mark.django_db
@pytest.mark.parametrize("answered", [2, 3, "viewed"])
def test_the_status_reads_waiting_below_the_minimum_ready_at_it_and_viewed_once_pressed(participant, answered):
    submit_sort(participant, complete_sort())
    answered_by(participant, *["Jo", "Priya", "Chris"][: 2 if answered == 2 else 3])
    if answered == "viewed":
        press_compare(participant)

    shown = status(participant)

    expected = {2: WAITING.format(answered=2, minimum=3), 3: READY, "viewed": VIEWED}[answered]
    assert expected in shown
    assert [state for state in (WAITING.format(answered=2, minimum=3), READY, VIEWED) if state in shown] == [expected]


@pytest.mark.django_db
def test_there_is_no_card_before_there_is_a_result(participant):
    answered_by(participant, "Jo", "Priya", "Chris")

    assert participant.get("/sections/calling/").status_code == 200
    assert card(participant) is None
