# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Before we begin as a wizard (ticket 50): a section the document marks as a wizard is where a participant who has
not completed it is taken in place of the hub, page by page, and afterwards it is listed in the hub like any other.
Its coach and contacts pages became the hub side cards Walk with a coach and Five trusted voices."""

import json
from pathlib import Path

import pytest
from django.utils import timezone

from engine.models import Contact, Publication, Response
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)

DOCUMENT = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do.json"
WIZARD = "/sections/onboarding/"
RATINGS_PAGE = "/sections/onboarding/pages/2/"
RATINGS = ("bl-bible", "bl-gifts", "bl-call", "bl-plan", "bl-peace")


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(json.loads(DOCUMENT.read_text(encoding="utf-8")))
    return signed_in_client


def answer(client, block_id, value):
    return client.post(f"/answers/{block_id}/", {"value": value, "version": Publication.current_version().pk})


def through_the_first_page(client):
    answer(client, "reason", "exploring")
    return client.post("/sections/onboarding/pages/1/continue/")


def through_the_wizard(client):
    """✨ The reason, then the five ratings, then completing it, as the participant does; returns the completion."""
    through_the_first_page(client)
    for rating in RATINGS:
        answer(client, rating, "7")
    return client.post("/sections/onboarding/complete/")


def a_response_from_before(user):
    """✨ A participant who completed Before we begin before this change, every answer it asks for stored, with a coach
    chosen and two people listed on what were then its own pages."""
    response = Response.objects.create(
        participant=user,
        version=Publication.current_version(),
        answers={"reason": "exploring", **{rating: 7 for rating in RATINGS}},
        completed_sections={"onboarding": timezone.now().isoformat()},
        fixed_answers={rating: timezone.now().isoformat() for rating in RATINGS},
    )
    response.replace_contacts("coach", [{"name": "Sam", "email": "sam@example.com"}], Contact.Role.COACH)
    people = [{"name": "Ana", "email": "ana@example.com"}, {"name": "Bo", "email": "bo@example.com"}]
    response.replace_contacts("contacts", people, Contact.Role.CONTACT)
    return response


@pytest.mark.django_db
def test_a_participant_who_has_not_completed_it_is_taken_to_its_wizard_in_place_of_the_hub(participant):
    hub = participant.get("/hub/")

    assert (hub.status_code, hub.url) == (302, WIZARD)
    page = participant.get(WIZARD).content.decode()
    assert 'id="answer-reason"' in page
    assert 'id="answer-bl-bible-1"' not in page  # ✨ the ratings are its second page
    assert 'class="pathway-nav"' not in page
    assert 'href="/hub/"' not in page
    assert 'src="/photos/onboarding/"' in page
    assert participant.get("/photos/onboarding/").status_code == 200


@pytest.mark.django_db
def test_completing_the_two_pages_lands_on_the_hub_with_it_complete_and_never_sends_them_back(participant):
    completed = through_the_wizard(participant)

    assert (completed.status_code, completed.url) == (303, "/hub/")
    assert "onboarding" in Response.objects.get().completed_sections
    for _ in range(2):
        hub = participant.get("/hub/")
        assert hub.status_code == 200
    assert '<a class="hub-section-title" href="/sections/onboarding/">' in hub.content.decode()


@pytest.mark.django_db
def test_one_part_way_through_lands_on_the_page_they_had_reached(participant):
    through_the_first_page(participant)

    hub = participant.get("/hub/")

    assert (hub.status_code, hub.url) == (302, RATINGS_PAGE)


@pytest.mark.django_db
def test_a_participant_who_completed_it_before_this_change_is_not_sent_through_it(participant, django_user_model):
    a_response_from_before(django_user_model.objects.get())

    assert participant.get("/hub/").status_code == 200


@pytest.mark.django_db
def test_a_coach_and_people_given_before_show_in_the_side_cards(participant, django_user_model):
    a_response_from_before(django_user_model.objects.get())

    coach = participant.get("/sections/walk-with-a-coach/").content.decode()
    voices = participant.get("/sections/trusted-voices/").content.decode()

    assert "You've chosen Sam" in coach
    assert 'value="ana@example.com"' in voices
    assert 'value="bo@example.com"' in voices


@pytest.mark.django_db
def test_once_complete_it_can_be_reread_and_a_changed_rating_is_refused(participant):
    through_the_wizard(participant)

    reread = participant.get(RATINGS_PAGE)

    assert reread.status_code == 200
    assert 'id="answer-bl-bible-7" name="value" value="7" checked disabled' in reread.content.decode()
    assert answer(participant, "bl-bible", "2").status_code == 409
    assert Response.objects.get().answers["bl-bible"] == 7
