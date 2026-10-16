# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A participant tied on both frameworks is told on their results that they are a generalist (ticket 30a). The tie
detection runs on the participant's own sort alone, never an observer's."""

import pytest

from tests.documents import complete_sort, sort_pathway, with_a_tie_break
from engine.models import Result
from tests.journeys.test_answers import participant  # noqa: F401 (a fixture)
from tests.journeys.test_comparison import comparison, observer_sort, with_observers
from tests.journeys.test_consent import give_consent
from tests.journeys.test_contact_list import JO, PRIYA, save_contacts
from tests.journeys.test_hub import signed_in_client  # noqa: F401 (a fixture)
from tests.journeys.test_invitations import issue_link, observer  # noqa: F401 (observer is a fixture)
from tests.journeys.test_observer_assessment import observed_pathway, send
from tests.journeys.test_observer_landing import claim
from tests.journeys.test_results import results, submit_sort

GENERALIST = "Two flat profiles"

# ✨ The test pathway's two items each load onto one construct of each framework, so a sort splitting them evenly is
# tied on both, and one leaning on either is tied on neither.
EVEN = complete_sort(a5={"bucket": "strength", "value": 50}, p1={"bucket": "strength", "value": 50})


@pytest.fixture
def signed_in(client, participant, load_pathway):
    """✨ A participant with onboarding complete, on a pathway with a tie-break and the generalist's wording."""
    load_pathway(with_a_tie_break(sort_pathway(), threshold=4, cluster=4))
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    return client


@pytest.mark.django_db
def test_a_participant_tied_on_both_frameworks_is_told_on_their_results_they_are_a_generalist(signed_in):
    submit_sort(signed_in, EVEN)

    assert GENERALIST in results(signed_in).content.decode()


@pytest.mark.django_db
def test_a_participant_with_a_clear_leader_is_not_told_they_are_a_generalist(signed_in):
    submit_sort(signed_in, complete_sort())

    assert GENERALIST not in results(signed_in).content.decode()


@pytest.mark.django_db
def test_observers_sorts_tied_on_both_frameworks_never_make_the_participant_a_generalist(signed_in, participant):
    with_observers(signed_in, participant, [observer_sort(50)] * 3)

    assert GENERALIST not in results(signed_in).content.decode()
    assert GENERALIST not in comparison(signed_in).content.decode()


# ✨ The tie-break's pairs (ticket 30b). The test pathway's two items load the same way on both frameworks, so a third,
# loading onto Prophet and Deliver, lets a sort tie one framework alone: Apostle 50 and Prophet 10 + 40 on APEST(d),
# Ponder 10 and Deliver 50 + 40 on PEP. Tied on Apostle and Prophet, two pairs follow, one each round.
TIE_BREAK = "/results/strengths-sort/tie-break/"
TIED_ON_ONE = complete_sort(
    a5={"bucket": "strength", "value": 50},
    p1={"bucket": "not-me", "value": 10},
    x1={"bucket": "strength", "value": 40},
)
CLEAR = complete_sort(x1={"bucket": "not-me", "value": 10})


def tie_breaking_pathway(document=None):
    document = document or sort_pathway()
    document["instrument"]["items"].append({"id": "x1", "text": "Seeing it through", "loads": ["prophet", "deliver"]})
    return with_a_tie_break(document)


@pytest.fixture
def marked(client, participant, load_pathway):
    """✨ A participant with onboarding complete, on a pathway whose sort can tie one framework alone."""
    load_pathway(tie_breaking_pathway())
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    return client


def choose(client, pair, chosen):
    """✨ Answer one pair as its form does: by its place in the plan and the construct chosen, or "" to skip."""
    return client.post(TIE_BREAK, {"pair": pair, "chosen": chosen})


def stored():
    result = Result.objects.get()
    return result.scores, result.tie_break_answers


@pytest.mark.django_db
def test_sending_a_sort_tied_on_one_framework_leads_to_its_pairs(marked):
    sent = submit_sort(marked, TIED_ON_ONE)

    assert sent["HX-Redirect"] == TIE_BREAK
    page = marked.get(TIE_BREAK).content.decode()
    assert "I am apostle, first" in page and "I am prophet, second" in page


@pytest.mark.django_db
def test_sending_a_sort_with_nothing_to_break_leads_to_the_results(marked):
    sent = submit_sort(marked, CLEAR)

    assert sent["HX-Redirect"] == "/results/strengths-sort/"
    assert marked.get(TIE_BREAK)["Location"] == "/results/strengths-sort/"


@pytest.mark.django_db
def test_answers_and_skips_are_stored_beside_the_sorts_result_which_is_unchanged(marked):
    submit_sort(marked, TIED_ON_ONE)
    scores_before, _ = stored()

    choose(marked, 0, "prophet")
    choose(marked, 1, "")

    scores, answers = stored()
    assert scores == scores_before
    assert [answer["chosen"] for answer in answers] == ["prophet", None]
    assert [answer["constructs"] for answer in answers] == [["apostle", "prophet"]] * 2


@pytest.mark.django_db
def test_a_choice_outside_the_pair_is_refused_and_nothing_is_stored(marked):
    submit_sort(marked, TIED_ON_ONE)

    refused = choose(marked, 0, "deliver")

    assert refused.status_code == 400
    assert stored()[1] == []


@pytest.mark.django_db
def test_leaving_part_way_comes_back_to_the_next_pair_and_the_last_leads_to_the_results(marked):
    submit_sort(marked, TIED_ON_ONE)
    choose(marked, 0, "apostle")

    assert results(marked)["Location"] == TIE_BREAK
    page = marked.get(TIE_BREAK).content.decode()
    assert "I am apostle, second" in page and "I am prophet, third" in page

    assert choose(marked, 1, "prophet")["Location"] == TIE_BREAK
    assert marked.get(TIE_BREAK)["Location"] == "/results/strengths-sort/"
    assert results(marked).status_code == 200


@pytest.fixture
def observed(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(tie_breaking_pathway(observed_pathway()))
    save_contacts(signed_in_client, JO, PRIYA)
    return signed_in_client


@pytest.mark.django_db
def test_an_observer_sending_a_tied_sort_is_never_offered_the_tie_break(observed, observer):  # noqa: F811
    claim(observer, issue_link(observed, "Jo"))

    sent = send(observer, TIED_ON_ONE)

    assert sent["Location"] == "/observe/"
