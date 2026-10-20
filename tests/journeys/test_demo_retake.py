# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Retaking the self-assessment, a demo-only tool (fix-19): on a development or demo system, a participant can
clear their own sort and everything worked out from it, and sort the cards again from the start. Nothing else of
theirs is touched, and nothing of anyone else's."""

from datetime import timedelta

import pytest
from django.test import Client

from engine.models import Contact, Invitation, ObserverResponse, Response, Result
from tests.journeys.test_answers import answer, participant  # noqa: F401 (participant is a fixture)
from tests.journeys.test_comparison import THREE_OBSERVERS, press_compare
from tests.journeys.test_consent import give_consent
from tests.journeys.test_observer_responses import an_observer
from tests.journeys.test_results import SORT, STRENGTHS, results, submit_sort
from tests.journeys.test_tie_break import CLEAR, TIED_ON_ONE, choose, tie_breaking_pathway

RETAKE = f"/results/{SORT}/retake/"


def retake_pathway():
    """✨ The tie-break's test pathway with the Strengths assessment a part of the calling section, whose gate needs the
    sort as well as the statement, as Section 1's does in Whatever You Do."""
    document = tie_breaking_pathway()
    sections = {section["id"]: section for section in document["content"]["sections"]}
    sections[STRENGTHS]["part_of"] = "calling"
    sections["calling"]["gate"]["clauses"].append({"type": "has_answer", "block": SORT, "message": "Finish the sort."})
    return document


@pytest.fixture
def demo(settings):
    """✨ A demo system, whatever the developer's `.env` sets."""
    settings.DEBUG = False
    settings.ANVILLE_DEMO_NOTICE = "This is a demo."


@pytest.fixture
def sorted_in(demo, client, participant, load_pathway):  # noqa: F811
    """✨ A participant who has sent a sort tied on one framework, answered both its pairs, and seen their results."""
    load_pathway(retake_pathway())
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    submit_sort(client, TIED_ON_ONE)
    choose(client, 0, "prophet")
    choose(client, 1, "apostle")
    results(client)
    return client


@pytest.mark.django_db
def test_with_debug_off_and_no_demo_notice_there_is_no_retake_and_no_link_to_it(sorted_in, settings):
    settings.DEBUG = False
    settings.ANVILLE_DEMO_NOTICE = ""

    assert sorted_in.get(RETAKE).status_code == 404
    assert sorted_in.post(RETAKE).status_code == 404
    assert RETAKE not in results(sorted_in).content.decode()
    assert Result.objects.exists()


@pytest.mark.django_db
def test_on_a_demo_system_the_link_is_hidden_until_revealed(sorted_in):
    """✨ fix-20: the link is in the page but `hidden` (not seen, not in the tab order, not read out) until the
    participant holds Option/Alt or presses and holds the title; those reveals are hand checks."""
    page = results(sorted_in).content.decode()

    assert f'<p class="back-to-hub" data-demo-reveal hidden><a href="{RETAKE}">' in page
    assert "<h1 data-demo-reveal-hold>" in page


@pytest.mark.django_db
def test_off_a_demo_system_neither_the_hidden_link_nor_its_reveal_is_in_the_page(sorted_in, settings):
    settings.DEBUG = False
    settings.ANVILLE_DEMO_NOTICE = ""

    page = results(sorted_in).content.decode()

    assert "data-demo-reveal" not in page  # ✨ nor data-demo-reveal-hold, which starts the same


@pytest.mark.django_db
def test_retaking_clears_the_sort_its_result_and_its_tie_break_and_the_assessment_shows_the_sort_again(sorted_in):
    answer(sorted_in, "statement", "To build things that last.")
    sorted_in.post("/sections/calling/complete/")
    press_compare(sorted_in)
    assert Result.objects.get().reweighted is not None
    assert RETAKE in results(sorted_in).content.decode()
    asked = sorted_in.get(RETAKE)
    assert f'action="{RETAKE}"' in asked.content.decode()
    assert Result.objects.exists()  # ✨ opening the page clears nothing

    retaken = sorted_in.post(RETAKE)

    response = Response.objects.get()
    assert retaken.status_code == 303
    assert not Result.objects.exists()
    assert SORT not in response.answers
    assert SORT not in response.comparisons_visited
    assert "calling" not in response.completed_sections
    shown = sorted_in.get(f"/sections/{STRENGTHS}/")
    assert shown.status_code == 200
    assert f'data-sort="sort-{SORT}"' in shown.content.decode()
    assert submit_sort(sorted_in, CLEAR)["HX-Redirect"] == f"/results/{SORT}/"


@pytest.mark.django_db
def test_retaking_leaves_observers_assessments_the_coach_link_and_other_answers_alone(sorted_in):
    answer(sorted_in, "statement", "To build things that last.")
    response = Response.objects.get()
    for sort in THREE_OBSERVERS:
        an_observer(response, sort)
    [coach] = response.replace_contacts("coach", [{"name": "Sam", "email": "sam@example.com"}], Contact.Role.COACH)
    Invitation.issue(coach, timedelta(days=30))
    press_compare(sorted_in, confirmed=True)
    assert Response.objects.get().collection_frozen_at is not None

    sorted_in.post(RETAKE)

    response = Response.objects.get()
    assert response.answers["statement"] == "To build things that last."
    assert "onboarding" in response.completed_sections
    assert sorted(ObserverResponse.objects.values_list("assessment", flat=True), key=str) == sorted(
        THREE_OBSERVERS, key=str
    )
    assert Invitation.objects.filter(contact__role=Contact.Role.COACH).exists()
    assert response.collection_frozen_at is None


@pytest.mark.django_db
def test_a_participant_can_clear_only_their_own_assessment(sorted_in, django_user_model):
    someone_else = django_user_model.objects.create_user(username="someone", email="someone@example.com")
    other = Client()
    other.force_login(someone_else)
    give_consent(other)

    other.post(RETAKE)
    Client().post(RETAKE)

    assert Result.objects.get().tie_break_answers
    assert SORT in Response.objects.get(participant__username="participant").answers
