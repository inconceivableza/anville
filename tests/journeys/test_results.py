"""✨ A sort is scored once, when it is submitted, and the result is kept against the response's pathway version."""

import json

import pytest

from engine.document.scoring import score
from engine.models import Response, Result
from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_answers import answer, participant  # noqa: F401 (a fixture)

SORT, STRENGTHS = "strengths-sort", "strengths"


@pytest.fixture
def signed_in(client, participant, load_pathway):
    """✨ A participant with onboarding complete, so the Strengths assessment section is open."""
    load_pathway(sort_pathway())
    client.force_login(participant)
    client.post("/sections/onboarding/complete/")
    return client


def submit_sort(client, sort):
    return answer(client, SORT, json.dumps(sort), section=STRENGTHS)


@pytest.mark.django_db
def test_submitting_a_sort_stores_its_result_against_the_responses_pathway_version(signed_in, participant):
    submit_sort(signed_in, complete_sort())

    response = Response.objects.get(participant=participant)
    result = Result.objects.get(response=response, block_id=SORT)
    assert response.answers[SORT] == complete_sort()
    assert result.scores == score(sort_pathway(), complete_sort())


@pytest.mark.django_db
def test_a_sort_that_breaks_the_contract_stores_neither_an_answer_nor_a_result(signed_in, participant):
    incomplete = complete_sort()
    del incomplete["p1"]

    refused = submit_sort(signed_in, incomplete)

    assert refused.status_code == 400
    assert not Result.objects.exists()
    assert SORT not in getattr(Response.objects.filter(participant=participant).first(), "answers", {})


@pytest.mark.django_db
def test_a_second_sort_is_refused_and_the_first_result_stands(signed_in, participant):
    """✨ Retake is not offered in this milestone. When it is, it makes a new attempt and keeps this one."""
    submit_sort(signed_in, complete_sort())

    again = submit_sort(signed_in, complete_sort(a5={"bucket": "not-me", "value": 0}))

    assert again.status_code == 409
    assert "not offered" in again.content.decode()
    assert Response.objects.get(participant=participant).answers[SORT] == complete_sort()
    assert [result.scores for result in Result.objects.all()] == [score(sort_pathway(), complete_sort())]


@pytest.mark.django_db
def test_a_later_pathway_version_never_recomputes_a_stored_result(signed_in, participant, load_pathway):
    submit_sort(signed_in, complete_sort())
    rescored = sort_pathway()
    rescored["instrument"]["items"][0]["loads"] = ["prophet", "deliver"]

    load_pathway(rescored)
    signed_in.get(f"/sections/{STRENGTHS}/")

    assert [result.scores for result in Result.objects.all()] == [score(sort_pathway(), complete_sort())]
