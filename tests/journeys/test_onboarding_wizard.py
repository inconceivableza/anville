# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Before we begin as a wizard (ticket 50): a section the document marks as a wizard is where a participant who has
not completed it is taken in place of the hub, page by page, and afterwards it is listed in the hub like any other.
Its coach and contacts pages became the hub side cards Walk with a coach and Five trusted voices. In *Whatever You Do*
it is once-only too (ticket 69), so once complete it is never seen again; the tests of a wizard listed once complete
read the document without that."""

import json
from pathlib import Path

import pytest
from django.utils import timezone

from engine.models import Contact, Publication, Response
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_navigation import sidebar_of

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
def test_completing_the_two_pages_lands_on_the_hub_with_it_complete_and_never_sends_them_back(
    wizard_listed_once_complete,
):
    participant = wizard_listed_once_complete
    completed = through_the_wizard(participant)

    assert (completed.status_code, completed.url) == (303, "/hub/")
    assert "onboarding" in Response.objects.get().completed_sections
    for _ in range(2):
        hub = participant.get("/hub/")
        assert hub.status_code == 200
    assert '<a class="hub-section-title" href="/sections/onboarding/">' in hub.content.decode()


@pytest.mark.django_db
def test_once_complete_it_offers_no_way_to_mark_it_not_complete(wizard_listed_once_complete):
    """✨ Ticket 50: the hub never asks for it again, so it is never taken back (fix-2)."""
    participant = wizard_listed_once_complete
    through_the_wizard(participant)

    page = participant.get(RATINGS_PAGE).content.decode()

    assert "/sections/onboarding/reopen/" not in page
    assert "Mark as not complete" not in page


@pytest.mark.django_db
def test_once_complete_taking_its_completion_back_is_refused(participant):
    through_the_wizard(participant)

    refused = participant.post("/sections/onboarding/reopen/")

    assert refused.status_code == 404
    assert "onboarding" in Response.objects.get().completed_sections
    assert participant.get("/hub/").status_code == 200


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


def stored(response):
    """✨ Everything a participant's response holds that a press on a section could change."""
    response.refresh_from_db()
    return (
        response.answers,
        response.completed_sections,
        response.fixed_answers,
        response.pages_moved_past,
        response.updated_at,
    )


# ✨ Every way into Before we begin: its two pages, going on from the first, an answer to each page, with and without
# JavaScript, and completing it again.
WAYS_IN = [
    ("get", WIZARD, {}, {}),
    ("get", RATINGS_PAGE, {}, {}),
    ("post", "/sections/onboarding/pages/1/continue/", {}, {}),
    ("post", "/answers/reason/", {"value": "other"}, {}),
    ("post", "/answers/reason/", {"value": "other"}, {"HTTP_HX_REQUEST": "true"}),
    ("post", "/answers/bl-bible/", {"value": "2"}, {}),
    ("post", "/answers/bl-bible/", {"value": "2"}, {"HTTP_HX_REQUEST": "true"}),
    ("post", "/sections/onboarding/complete/", {}, {}),
]


@pytest.mark.django_db
@pytest.mark.parametrize("method, path, form, headers", WAYS_IN)
def test_once_complete_every_way_into_it_sends_the_participant_to_the_hub_and_changes_nothing(
    participant, method, path, form, headers
):
    """✨ Before we begin is once-only (ticket 69): once complete, neither its reason nor its ratings can be seen or
    changed."""
    through_the_wizard(participant)
    response = Response.objects.get()
    before = stored(response)

    sent = getattr(participant, method)(path, form, **headers)

    if headers:
        assert sent.headers["HX-Redirect"] == "/hub/"
    else:
        assert (sent.status_code in (302, 303), sent.url) == (True, "/hub/")
    assert stored(response) == before


@pytest.mark.django_db
def test_once_complete_it_is_gone_from_the_hub_the_sidebar_and_the_count(participant):
    through_the_wizard(participant)
    sections = json.loads(DOCUMENT.read_text(encoding="utf-8"))["content"]["sections"]

    hub = participant.get("/hub/").content.decode()
    sidebar = sidebar_of(participant.get("/sections/designed/").content.decode())

    assert "/sections/onboarding/" not in hub
    assert "Before we begin" not in sidebar
    # ✨ Nothing else is complete yet, and Before we begin is not one of the sections counted, which are the numbered
    # ones alone (ticket 87).
    assert f"0 of {sum('number' in section for section in sections)} sections complete" in hub


def without_once_only(document):
    """✨ *Whatever You Do* with Before we begin a wizard but not once-only, as a document may have one."""
    del document["content"]["sections"][0]["once_only"]
    return document


@pytest.fixture
def wizard_listed_once_complete(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(without_once_only(json.loads(DOCUMENT.read_text(encoding="utf-8"))))
    return signed_in_client


@pytest.mark.django_db
def test_once_complete_it_can_be_reread_and_a_changed_rating_is_refused(wizard_listed_once_complete):
    participant = wizard_listed_once_complete
    through_the_wizard(participant)

    reread = participant.get(RATINGS_PAGE)

    assert reread.status_code == 200
    assert 'id="answer-bl-bible-7" name="value" value="7" checked disabled' in reread.content.decode()
    assert answer(participant, "bl-bible", "2").status_code == 409
    assert Response.objects.get().answers["bl-bible"] == 7
