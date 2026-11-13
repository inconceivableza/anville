# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ "Haven't seen this" (ticket 108): an observer's eighth choice beside the buckets, where the pathway offers it.

A card placed there is kept as placed, and left out of that observer's scores; the observer still counts toward the
minimum while any card of theirs is in a bucket, but one who saw nothing counts toward no minimum and is left out of the
comparison, having nothing to add (sprint-3d-r1-fix-1). The participant has no such choice.
"""

import pytest

from engine.models import ObserverResponse, Response, Result
from tests.documents import complete_sort
from tests.journeys.pages import text_of
from tests.journeys.test_comparison import THREE_OBSERVERS, looked_at, strips
from tests.journeys.test_contact_list import JO, PRIYA, save_contacts
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import issue_link, observer  # noqa: F401  (observer is a fixture)
from tests.journeys.test_observer_assessment import observed_pathway, observer_assessments, send
from tests.journeys.test_observer_landing import claim, the_observers_page
from tests.journeys.test_observer_responses import an_observer
from tests.journeys.test_results import SORT, STRENGTHS, submit_sort, widget_data

NOT_SEEN = {"seen": False}
A_CARD_NOT_SEEN = {"a5": {"bucket": "strength"}, "p1": NOT_SEEN}
NOTHING_SEEN = {"a5": NOT_SEEN, "p1": NOT_SEEN}


def offering_it(document):
    """✨ `document` offering observers "Haven't seen this", scored by the method that leaves such cards out."""
    document["instrument"]["not_seen"] = {"label": "Haven’t seen this"}
    document["measurement"]["scoring"] = {"method": "compositional_share_of_seen"}
    return document


def a_participant(client, load_pathway, document):
    """✨ The participant on `document`, two people on their list and onboarding complete, so the sort is open."""
    load_pathway(document)
    save_contacts(client, JO, PRIYA)
    client.post("/sections/onboarding/complete/")
    return client


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    return a_participant(signed_in_client, load_pathway, offering_it(observed_pathway()))


@pytest.mark.django_db
def test_an_observers_card_in_havent_seen_this_is_kept_as_placed_and_they_count_toward_the_minimum(
    participant, observer  # noqa: F811
):
    claim(observer, issue_link(participant, "Jo"))

    sent = send(observer, A_CARD_NOT_SEEN)

    assert sent.status_code == 303
    assert observer_assessments().assessments == [{"a5": {"bucket": "strength", "value": 85}, "p1": NOT_SEEN}]
    submit_sort(participant, complete_sort())
    for _ in range(2):
        an_observer(Response.objects.get(), complete_sort())
    assert "Others:" in text_of(looked_at(participant).content.decode())


def jo_sends_having_seen_nothing(participant, observer):  # noqa: F811
    """✨ Jo claims her link and sends with every card in "Haven't seen this", which is stored as any send is."""
    claim(observer, issue_link(participant, "Jo"))
    assert send(observer, NOTHING_SEEN).status_code == 303


@pytest.mark.django_db
def test_an_observer_who_saw_nothing_is_kept_but_counts_toward_no_minimum(participant, observer):  # noqa: F811
    """✨ With two others in, the press freezes nothing and the comparison still waits on a third."""
    jo_sends_having_seen_nothing(participant, observer)
    submit_sort(participant, complete_sort())
    for _ in range(2):
        an_observer(Response.objects.get(), complete_sort())

    shown = looked_at(participant).content.decode()

    assert ObserverResponse.objects.filter(submitted_at__isnull=False).count() == 3
    assert Response.objects.get().collection_frozen_at is None
    assert "2 of 3" in shown
    assert "Others:" not in text_of(shown)


@pytest.mark.django_db
def test_an_observer_who_saw_nothing_is_left_out_of_the_averages_and_the_spread(participant, observer):  # noqa: F811
    """✨ Counted, their even share would be a fourth dot in each construct's spread, and pull each mean toward it."""
    jo_sends_having_seen_nothing(participant, observer)
    submit_sort(participant, complete_sort())
    for sort in THREE_OBSERVERS:
        an_observer(Response.objects.get(), sort)

    spreads = strips(looked_at(participant).content.decode())

    assert spreads and all(len(spread) == 3 for spread in spreads)


@pytest.mark.django_db
def test_a_participants_sort_with_a_card_in_havent_seen_this_is_refused_and_nothing_is_kept(participant):
    refused = submit_sort(participant, {**complete_sort(), "p1": NOT_SEEN})

    assert refused.status_code == 400
    assert SORT not in Response.objects.get().answers
    assert not Result.objects.exists()


@pytest.mark.django_db
def test_where_the_pathway_does_not_offer_it_an_observers_card_in_havent_seen_this_is_refused(
    signed_in_client, load_pathway, observer  # noqa: F811
):
    a_participant(signed_in_client, load_pathway, observed_pathway())
    claim(observer, issue_link(signed_in_client, "Jo"))

    refused = send(observer, A_CARD_NOT_SEEN)

    assert refused.status_code == 400
    assert not ObserverResponse.objects.filter(submitted_at__isnull=False).exists()


@pytest.mark.django_db
def test_the_observers_sort_offers_havent_seen_this_and_the_participants_does_not(participant, observer):  # noqa: F811
    claim(observer, issue_link(participant, "Jo"))
    label = offering_it(observed_pathway())["instrument"]["not_seen"]["label"]

    observers = widget_data(the_observers_page(observer).content.decode())
    participants = widget_data(participant.get(f"/sections/{STRENGTHS}/").content.decode())

    assert observers["not_seen"] == {"label": label}
    assert participants["not_seen"] is None
