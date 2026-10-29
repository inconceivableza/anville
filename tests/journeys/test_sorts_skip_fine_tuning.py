# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A pathway whose sorts skip fine-tuning: every card takes its bucket's seed, for participants as
for observers, and the widget is told which cards are twins, so it never deals one straight after the other."""

import pytest

from engine.document.blocks import BLOCK_TYPES
from engine.models import Response
from tests.documents import sort_pathway
from tests.journeys.test_answers import participant  # noqa: F401 (a fixture)
from tests.journeys.test_consent import give_consent
from tests.journeys.test_contact_list import JO, PRIYA, save_contacts
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import (  # noqa: F401  (observer is a fixture, used by name)
    issue_link,
    observer,
)
from tests.journeys.test_observer_assessment import observed_pathway
from tests.journeys.test_observer_landing import claim, the_observers_page
from tests.journeys.test_results import SORT, STRENGTHS, submit_sort, widget_data


def skipping(document):
    return {**document, "sorts_skip_fine_tuning": True}


def at_the_sort(client, participant, load_pathway, document):
    """✨ The participant signed in with onboarding complete, so the sort's section is open, under `document`."""
    load_pathway(document)
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    return client


def the_participants_widget(client):
    return widget_data(client.get(f"/sections/{STRENGTHS}/").content.decode())


@pytest.mark.django_db
def test_with_fine_tuning_off_a_participants_sort_of_buckets_alone_is_kept_at_their_seeds(
    client, participant, load_pathway
):
    at_the_sort(client, participant, load_pathway, skipping(sort_pathway()))

    sent = submit_sort(client, {"a5": {"bucket": "strength"}, "p1": {"bucket": "not-me"}})

    assert sent.status_code < 400
    assert Response.objects.get().answers[SORT] == {
        "a5": {"bucket": "strength", "value": 85},
        "p1": {"bucket": "not-me", "value": 10},
    }


@pytest.mark.django_db
@pytest.mark.parametrize("skips", [True, False], ids=["fine-tuning off", "by default"])
def test_a_participant_is_offered_fine_tuning_unless_the_pathway_skips_it(client, participant, load_pathway, skips):
    document = skipping(sort_pathway()) if skips else sort_pathway()
    at_the_sort(client, participant, load_pathway, document)

    assert the_participants_widget(client)["fine_tunes"] is not skips


@pytest.mark.django_db
def test_with_fine_tuning_off_an_observer_is_not_offered_it_either(
    signed_in_client, load_pathway, observer  # noqa: F811
):
    load_pathway(skipping(observed_pathway()))
    save_contacts(signed_in_client, JO, PRIYA)
    claim(observer, issue_link(signed_in_client, "Jo"))

    assert widget_data(the_observers_page(observer).content.decode())["fine_tunes"] is False


@pytest.mark.django_db
def test_the_widget_is_told_each_cards_twin_both_ways(client, participant, load_pathway):
    document = sort_pathway()
    document["instrument"]["items"].append(
        {"id": "a5b", "text": "Leaving a blueprint", "loads": ["apostle", "deliver"], "twin": "a5"}
    )
    at_the_sort(client, participant, load_pathway, document)

    twins = {item["id"]: item.get("twin") for item in the_participants_widget(client)["items"]}

    assert twins == {"a5": "a5b", "p1": None, "a5b": "a5"}


def with_a_twin(document):
    document["instrument"]["items"].append(
        {"id": "a5b", "text": "Leaving a blueprint", "loads": ["apostle", "deliver"], "twin": "a5"}
    )
    return document


@pytest.mark.django_db
def test_each_card_is_dealt_in_its_round_the_rewordings_in_the_second(client, participant, load_pathway):
    at_the_sort(client, participant, load_pathway, skipping(with_a_twin(sort_pathway())))

    rounds = {item["id"]: item["round"] for item in the_participants_widget(client)["items"]}

    assert rounds == {"a5": 1, "p1": 1, "a5b": 2}


def test_each_rounds_title_is_the_prototypes_in_the_readers_wording():
    sort_widget = BLOCK_TYPES["sort_assessment"].widget
    document = skipping(with_a_twin(sort_pathway()))

    titles = {
        role: [sort_widget(document, role, "Sam")["wording"][f"round_{n}_title"] for n in (1, 2)]
        for role in ("participant", "observer")
    }

    assert titles == {
        "participant": ["What you’re good at", "What you find yourself doing"],
        "observer": ["What Sam is good at", "What you’d see Sam doing"],
    }


@pytest.mark.parametrize("role", ["participant", "observer"])
def test_the_halfway_screen_says_whether_round_1_was_spread_well(role):
    """✨ Well spread is 5 or more of the 7 buckets used, none holding more than a third of the cards; otherwise the
    reader is asked to spread round 2 more, told which bucket holds too many where one does. The widget fills in the
    figures."""
    wording = BLOCK_TYPES["sort_assessment"].widget(skipping(with_a_twin(sort_pathway())), role, "Sam")["wording"]

    assert [wording[field] for field in ("buckets_spread_well", "buckets_spread_more", "buckets_crowded")] == [
        "You used {used} of the {buckets} buckets. That’s a good spread, and it makes your results clearer. Keep doing "
        "the same in round 2.",
        "You used {used} of the {buckets} buckets{crowded}. Spreading your answers out makes the results clearer, so "
        "in round 2 try using the whole range where it fits.",
        ", and {count} of your {cards} cards are in “{bucket}”",
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("skips", [True, False], ids=["fine-tuning off", "by default"])
def test_a_participant_gets_the_quick_check_only_where_fine_tuning_is_skipped(
    client, participant, load_pathway, skips
):
    document = with_a_twin(sort_pathway())
    at_the_sort(client, participant, load_pathway, skipping(document) if skips else document)

    assert the_participants_widget(client)["quick_check"] is skips


@pytest.mark.django_db
def test_an_observer_never_gets_the_quick_check(signed_in_client, load_pathway, observer):  # noqa: F811
    """✨ The prototype's: several observers' contradictions average out."""
    load_pathway(skipping(with_a_twin(observed_pathway())))
    save_contacts(signed_in_client, JO, PRIYA)
    claim(observer, issue_link(signed_in_client, "Jo"))

    assert widget_data(the_observers_page(observer).content.decode())["quick_check"] is False
