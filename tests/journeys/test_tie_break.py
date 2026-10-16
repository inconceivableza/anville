# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A participant tied on both frameworks is told on their results that they are a generalist (ticket 30a). The tie
detection runs on the participant's own sort alone, never an observer's."""

import pytest

from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_answers import participant  # noqa: F401 (a fixture)
from tests.journeys.test_comparison import comparison, observer_sort, with_observers
from tests.journeys.test_consent import give_consent
from tests.journeys.test_results import results, submit_sort

GENERALIST = "Two flat profiles"

# ✨ The test pathway's two items each load onto one construct of each framework, so a sort splitting them evenly is
# tied on both, and one leaning on either is tied on neither.
EVEN = complete_sort(a5={"bucket": "strength", "value": 50}, p1={"bucket": "strength", "value": 50})


@pytest.fixture
def signed_in(client, participant, load_pathway):
    """✨ A participant with onboarding complete, on a pathway with a tie-break and the generalist's wording."""
    pathway = sort_pathway()
    pathway["measurement"]["tie_break"] = {"threshold": 4, "cluster": 4}
    pathway["presentation"]["generalist"] = {"heading": "A generalist", "text": f"{GENERALIST} is itself a finding."}
    load_pathway(pathway)
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
