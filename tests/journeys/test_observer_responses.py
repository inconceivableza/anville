"""✨ Observers' answers are kept as their own records, apart from who the observer is (ADR 0005), and a seeding
command creates test observers directly, so the comparison can be shown before, or without, the questionnaire.

Only submitted observer assessments reach the observer average, and nothing of any one observer reaches the
participant.
"""

import json
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.db import IntegrityError
from django.utils import timezone

from engine.document import answer_from_form, answerable_block
from engine.document.scoring import score
from engine.models import ObserverAssessments, ObserverResponse, Publication, Response, Result
from tests.documents import complete_sort, pathway_document, sort_pathway
from tests.journeys.test_answers import participant  # noqa: F401 (a fixture)
from tests.journeys.test_results import SORT, STRENGTHS, results, signed_in, submit_sort  # noqa: F401 (signed_in is a fixture, used by name)

SEED_PASSWORD = "information."


@pytest.fixture
def participant_response(participant, load_pathway):
    load_pathway(sort_pathway())
    return Response.objects.create(participant=participant, version=Publication.current_version())


def an_observer(response, assessment, *, submitted=True, is_test_data=False, written_answers=None):
    return ObserverResponse.objects.create(
        response=response,
        assessment=assessment,
        written_answers=written_answers or {},
        submitted_at=timezone.now() if submitted else None,
        is_test_data=is_test_data,
    )


def seed(observers=3):
    out = StringIO()
    call_command("seed_observers", "--observers", str(observers), stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_only_submitted_observer_assessments_are_read_for_the_observer_average(participant_response):
    submitted = complete_sort(a5={"bucket": "not-me", "value": 20})
    an_observer(participant_response, submitted)
    an_observer(participant_response, complete_sort(), submitted=False)

    assert ObserverResponse.assessments_for(participant_response).assessments == [submitted]


@pytest.mark.django_db
def test_a_submitted_observer_response_without_an_assessment_is_refused(participant_response):
    with pytest.raises(IntegrityError):
        an_observer(participant_response, None)


@pytest.mark.django_db
def test_the_read_for_the_observer_average_carries_the_assessments_and_nothing_else(participant_response):
    an_observer(participant_response, complete_sort(), written_answers={"energises": "Teaching the youth group."})

    assert ObserverResponse.assessments_for(participant_response) == ObserverAssessments(
        assessments=[complete_sort()], all_test_data=False
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "observers, all_test_data",
    [
        ([True, True, True], True),
        ([True, False, True], False),
        ([], False),
    ],
    ids=["every one test data", "one real among test data", "no observers"],
)
def test_the_read_says_all_test_data_only_when_every_submitted_observer_is(participant_response, observers, all_test_data):
    for is_test_data in observers:
        an_observer(participant_response, complete_sort(), is_test_data=is_test_data)

    assert ObserverResponse.assessments_for(participant_response).all_test_data is all_test_data


@pytest.mark.django_db
def test_seeding_creates_a_fake_participant_with_a_self_result_and_test_observers_all_marked_as_test_data(load_pathway):
    document = sort_pathway()
    load_pathway(document)

    seed(observers=4)

    response = Response.objects.get()
    self_assessment = response.answers[SORT]
    block = answerable_block(document, SORT)
    assert response.participant.email.endswith("@example.com")
    assert response.is_test_data is True
    assert answer_from_form(document, block, json.dumps(self_assessment)) == self_assessment
    assert Result.objects.get(response=response, block_id=SORT).scores == score(document, self_assessment)
    observers = ObserverResponse.assessments_for(response)
    assert len(observers.assessments) == 4
    assert observers.all_test_data is True
    for assessment in observers.assessments:
        assert answer_from_form(document, block, json.dumps(assessment)) == assessment


@pytest.mark.django_db
def test_the_seeded_participant_signs_in_with_the_seed_password_and_reaches_the_pathway_without_a_consent_step(
    client, load_pathway
):
    load_pathway(sort_pathway())
    seed()
    email = Response.objects.get().participant.email

    signed_in_page = client.post("/accounts/login/", {"login": email, "password": SEED_PASSWORD}, follow=True)

    assert signed_in_page.status_code == 200
    assert signed_in_page.redirect_chain[-1][0] == "/"


@pytest.mark.django_db
def test_seeding_again_gives_the_new_participant_the_same_observer_assessments(load_pathway):
    load_pathway(sort_pathway())

    seed()
    seed()

    first, second = Response.objects.order_by("pk")
    assert first.participant != second.participant
    assert ObserverResponse.assessments_for(first) == ObserverResponse.assessments_for(second)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "document, observers",
    [(None, 3), (pathway_document(), 3), (sort_pathway(), 0)],
    ids=["nothing published", "no assessment block", "no observers asked for"],
)
def test_seeding_is_refused_and_stores_nothing_without_an_assessment_or_observers(load_pathway, document, observers):
    if document is not None:
        load_pathway(document)

    with pytest.raises(CommandError):
        seed(observers)

    assert not get_user_model().objects.exists()
    assert not Response.objects.exists()
    assert not ObserverResponse.objects.exists()


@pytest.mark.django_db
def test_an_observers_written_answer_is_on_none_of_the_participants_pages(signed_in, participant):
    submit_sort(signed_in, complete_sort())
    response = Response.objects.get(participant=participant)
    an_observer(response, complete_sort(), written_answers={"struggles": "Saying no to people."})

    pages = [signed_in.get("/"), signed_in.get(f"/sections/{STRENGTHS}/"), results(signed_in)]

    for page in pages:
        assert page.status_code == 200
        assert "Saying no to people." not in page.content.decode()
