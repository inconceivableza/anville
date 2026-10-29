# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The comparison signpost on the hub (ticket 67b): a row within its section, after the part holding its sort, and a
button beside "Invite people" on the Five trusted voices card. Each makes the same press as the section's card, through
the same freeze warning (ADR 0017), and the row shows the same status (the button no longer does, ticket 81)."""

import re

import pytest

from engine.document.blocks import COMPARISON_STATUSES
from engine.models import Response
from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_coach_checklist import text
from tests.journeys.test_comparison_signpost import CARD, card
from tests.journeys.test_contact_list import VOICES, with_trusted_voices
from tests.journeys.test_hub import (  # noqa: F401  (signed_in_client is a fixture, used by name)
    PEOPLE,
    add_people_with_links,
    answer_through,
    signed_in_client,
    tag_of,
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


def sidebar_entry(client):
    """✨ The comparison's entry in the sidebar of the calling section's page, or None when it shows none."""
    page = client.get("/sections/calling/").content.decode()
    found = re.search(r'<li class="[^"]*pathway-nav-comparison.*?</li>', page, re.S)
    return found.group(0) if found else None


def where_it_leads(html):
    """✨ Whether the markup leads to Five trusted voices' page, and whether it presses on to the comparison."""
    return (f'href="/sections/{VOICES}/"' in html, f'action="/results/{SORT}/comparison/visit/"' in html)


def opens_the_comparison(html):
    """✨ Whether the markup opens the comparison itself, by a link and without the press, as it does while waiting."""
    return f'href="/results/{SORT}/comparison/"' in html


@pytest.mark.django_db
def test_below_the_minimum_the_hubs_row_and_the_sidebar_open_the_comparison_and_from_it_compare(
    participant, settings
):
    """✨ The hub's row and the sidebar's entry always lead to the comparison (fix-16, reversing fix-3 there): below the
    minimum by a link to its waiting page, from it by the press. The section's card offers the way to invite people
    beside its greyed press (fix-8). The voices card offers nothing in its place: its "Invite people" already leads
    there, and its Answered meter and tag say where the answers stand (developer's call, 23 Oct, ticket 81)."""
    settings.ANVILLE_SIDEBAR = True
    answer_through(*participant.links[:2])
    assert hub_row(participant) is None
    assert voices_button(participant) is None

    submit_sort(participant, complete_sort())

    assert where_it_leads(card(participant)) == (True, False)
    for shown in (hub_row(participant), sidebar_entry(participant)):
        assert where_it_leads(shown) == (False, False)
        assert opens_the_comparison(shown)
    for shown in (card(participant), hub_row(participant), sidebar_entry(participant)):
        assert statuses(shown) == ["2 of 3 answered"]
    assert voices_button(participant) is None
    assert statuses(voices_card(participant)) == []

    answer_through(participant.links[2])

    for with_invitation, shown in (
        (True, card(participant)),  # ✨ the section's card keeps its invitation from the minimum (fix-8)
        (False, hub_row(participant)),
        (False, sidebar_entry(participant)),
    ):
        assert where_it_leads(shown) == (with_invitation, True)
        assert statuses(shown) == [COMPARISON_STATUSES["ready"]]
    assert voices_button(participant) is not None
    assert statuses(voices_card(participant)) == []

    press_compare(participant)

    assert statuses(card(participant)) == statuses(hub_row(participant)) == [COMPARISON_STATUSES["viewed"]]


def followed(client, html):
    """✨ The page the markup's first link opens."""
    return client.get(re.search(r'href="([^"]+)"', html).group(1))


@pytest.mark.django_db
def test_below_the_minimum_the_comparison_waits_with_the_way_to_invite_people_and_no_observer_data(participant):
    """✨ The row's link opens a waiting page, not an empty comparison (fix-16): the count phrase the row shows and the
    way to Five trusted voices, and nothing of the two answers in, which stay hidden below the minimum (ADR 0005)."""
    answer_through(*participant.links[:2])
    submit_sort(participant, complete_sort())

    page = followed(participant, hub_row(participant))

    assert page.status_code == 200
    assert page.context["comparison"]["frameworks"] is None
    assert "comparison-pair" not in page.content.decode()
    assert f'href="/sections/{VOICES}/"' in page.content.decode()
    assert "2 of 3 answered" in text(page)


@pytest.mark.django_db
def test_opening_the_comparison_from_the_row_below_the_minimum_marks_nothing_viewed(participant, settings):
    """✨ Only the press from the minimum is the view "Viewed" reads (ticket 67a); the row's link below it is not, so
    once the minimum is in, the comparison is ready, not viewed (fix-16)."""
    settings.ANVILLE_SIDEBAR = True
    answer_through(*participant.links[:2])
    submit_sort(participant, complete_sort())
    before = [statuses(card(participant)), statuses(hub_row(participant)), tag_of(voices_card(participant))]

    followed(participant, hub_row(participant))
    followed(participant, sidebar_entry(participant))

    assert [statuses(card(participant)), statuses(hub_row(participant)), tag_of(voices_card(participant))] == before
    answer_through(participant.links[2])
    assert statuses(card(participant)) == statuses(hub_row(participant)) == [COMPARISON_STATUSES["ready"]]


@pytest.mark.django_db
def test_below_the_minimum_with_too_few_links_the_card_and_row_say_whose_answers_are_still_needed(
    signed_in_client, load_pathway  # noqa: F811
):
    """✨ In words that say what is needed (29 Oct), where they said "1 more needed" as the voices card still does,
    which counts links."""
    load_pathway(with_the_card_on_the_hub())
    signed_in_client.post("/sections/onboarding/complete/")
    answer_through(*add_people_with_links(signed_in_client, *PEOPLE[:2]))
    submit_sort(signed_in_client, complete_sort())

    assert tag_of(voices_card(signed_in_client)) == "1 more needed"
    assert "Still need answers from 1 person who knows you" in text(card(signed_in_client))
    assert "Still need answers from 1 person who knows you" in text(hub_row(signed_in_client))


@pytest.mark.django_db
def test_below_the_minimum_the_answers_still_needed_count_answers_not_links(
    signed_in_client, load_pathway  # noqa: F811
):
    """✨ One person with a link who has not answered: three answers are still needed, though two more links are."""
    load_pathway(with_the_card_on_the_hub())
    signed_in_client.post("/sections/onboarding/complete/")
    add_people_with_links(signed_in_client, PEOPLE[0])
    submit_sort(signed_in_client, complete_sort())

    assert tag_of(voices_card(signed_in_client)) == "2 more needed"
    assert "Still need answers from 3 people who know you" in text(card(signed_in_client))


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
