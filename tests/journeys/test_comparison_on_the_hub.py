# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The comparison signpost on the hub (ticket 67b): a row within its section, after the part holding its sort, and a
button beside Manage on the Five trusted voices card. Each makes the same press as the section's card, through the
same freeze warning (ADR 0017), and the row shows the same status (the button no longer does, ticket 81)."""

import re

import pytest

from engine.document.blocks import COMPARISON_STATUSES
from engine.models import Response
from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_coach_checklist import text
from tests.journeys.test_comparison_signpost import CARD, card
from tests.journeys.test_contact_list import with_trusted_voices
from tests.journeys.test_hub import (  # noqa: F401  (signed_in_client is a fixture, used by name)
    PEOPLE,
    add_people_with_links,
    answer_through,
    signed_in_client,
    voices_card,
)
from tests.journeys.test_observer_assessment import RESULTS_SEEN, press_compare
from tests.journeys.test_results import SORT, STRENGTHS, submit_sort

ACTION = re.compile(r'<form[^>]* method="post" action="([^"]+)"')


def with_the_card_on_the_hub():
    """✨ The sort pathway with Five trusted voices beside the hub, the Strengths assessment a part of the calling
    section, and the comparison signpost in that section, as Section 1 has them in *Whatever You Do*."""
    document = with_trusted_voices(sort_pathway())
    sections = {section["id"]: section for section in document["content"]["sections"]}
    sections[STRENGTHS]["part_of"] = "calling"
    sections["calling"]["blocks"].append(
        {"id": CARD, "type": "comparison_signpost", "sort": SORT, "title": "How others see you"}
    )
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    """✨ Onboarding complete and three people with links, none of whom has answered yet."""
    load_pathway(with_the_card_on_the_hub())
    signed_in_client.post("/sections/onboarding/complete/")
    signed_in_client.links = add_people_with_links(signed_in_client, *PEOPLE)
    return signed_in_client


def hub_row(client):
    """✨ The comparison's row on the hub, or None when the hub shows none."""
    page = client.get("/hub/").content.decode()
    found = re.search(r'<li class="[^"]*hub-comparison.*?</li>', page, re.S)
    return found.group(0) if found else None


def voices_button(client):
    """✨ The voices card's form for the comparison, or None when the card shows none."""
    found = re.search(r'<form[^>]* method="post".*?</form>', voices_card(client), re.S)
    return found.group(0) if found else None


def statuses(html):
    """✨ Which of the comparison's statuses the markup reads, for any number of answers out of a minimum of three."""
    words = text(html)
    waiting = re.findall(r"\d+ of 3 answered", words)
    return waiting + [COMPARISON_STATUSES[state] for state in ("ready", "viewed") if COMPARISON_STATUSES[state] in words]


@pytest.mark.django_db
def test_once_there_is_a_result_the_hubs_row_shows_with_the_cards_status_and_the_voices_cards_button_without_it(
    participant,
):
    """✨ The voices card's Answered meter and tag already say where the answers stand (developer's call, 23 Oct, ticket
    81)."""
    answer_through(*participant.links[:2])
    assert hub_row(participant) is None
    assert voices_button(participant) is None

    submit_sort(participant, complete_sort())

    on_the_card = statuses(card(participant))
    assert on_the_card == ["2 of 3 answered"]
    assert statuses(hub_row(participant)) == on_the_card
    assert voices_button(participant) is not None
    assert statuses(voices_card(participant)) == []

    answer_through(participant.links[2])
    press_compare(participant)

    assert statuses(card(participant)) == [COMPARISON_STATUSES["viewed"]]
    assert statuses(hub_row(participant)) == [COMPARISON_STATUSES["viewed"]]
    assert statuses(voices_card(participant)) == []


@pytest.mark.django_db
@pytest.mark.parametrize("htmx", [False, True], ids=["without JavaScript", "with htmx"])
def test_both_presses_reach_the_same_freeze_warning(participant, htmx):
    submit_sort(participant, complete_sort())
    answer_through(*participant.links)
    on_the_card = ACTION.search(card(participant)).group(1)
    headers = {"HX-Request": "true"} if htmx else {}

    for press in (ACTION.search(hub_row(participant)).group(1), ACTION.search(voices_button(participant)).group(1)):
        asked = participant.post(press, headers=headers)

        assert press == on_the_card
        assert asked.status_code == 200
        assert asked.templates[0].name == "engine/comparison_confirm.html"
        assert Response.objects.get().collection_frozen_at is None


@pytest.mark.django_db
def test_while_collection_is_frozen_the_voices_card_keeps_its_frozen_line_and_its_button_leads_to_the_comparison(
    participant,
):
    submit_sort(participant, complete_sort())
    answer_through(*participant.links)
    press_compare(participant)
    assert Response.objects.get().collection_frozen_at is not None

    shown = voices_card(participant)
    pressed = participant.post(ACTION.search(voices_button(participant)).group(1))

    assert RESULTS_SEEN in text(shown)
    assert (pressed.status_code, pressed["Location"]) == (303, f"/results/{SORT}/comparison/")
