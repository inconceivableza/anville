# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Demo shortcuts (ticket 113), offered only on a development or demo system: an observer's sort loads one of the
participant's demo profiles, the hub's hidden control completes what a chosen section needs to open, making up the
people and answers a real participant would have, and the homepage and sign-up page suggest a made-up @example.com
address. Off a demo system none of it is offered, and the server refuses it."""

import re

import pytest
from django.core import mail
from django.test import Client

from engine.models import Contact, Invitation, ObserverResponse, Response, Result
from engine.tie_break_scenarios import PROFILES
from tests.journeys.test_coach_checklist import choose
from tests.journeys.test_invitations import issue_link
from tests.journeys.test_observer_assessment import send
from tests.journeys.test_observer_landing import claim
from tests.journeys.test_results import widget_data
from tests.journeys.test_whatever_you_do import (  # noqa: F401  (participant and signed_in_client are fixtures)
    a_whole_sort,
    answer_onboarding,
    participant,
    signed_in_client,
    submit_the_sort,
    the_pathway,
)
from tests.journeys.test_whatever_you_do_faithful_port import add_people, complete

SHORTCUT = "/hub/demo-shortcut/"
SORT = "strengths-sort"
SECTION_3, SECTION_4, SECTION_6 = "/sections/shape/", "/sections/calling/", "/sections/letter/"


@pytest.fixture
def demo(settings):
    """✨ A demo system, whatever the developer's `.env` sets."""
    settings.DEBUG = False
    settings.ANVILLE_DEMO_NOTICE = "This is a demo."


def off_a_demo(settings):
    settings.DEBUG = False
    settings.ANVILLE_DEMO_NOTICE = ""


@pytest.fixture
def at_the_hub(demo, participant):  # noqa: F811
    """✨ A participant of Whatever You Do through Before we begin, so the hub is theirs, and nothing else done."""
    answer_onboarding(participant)
    complete(participant, "onboarding")
    return participant


def open_up_to(client, section_id):
    """✨ The hub's hidden control pressed with `section_id` chosen."""
    return client.post(SHORTCUT, {"section": section_id})


def response():
    return Response.objects.get(participant__username="participant")


def an_observer_of(client):
    """✨ One person added to the participant's list, and their link claimed in a browser of their own; returns that
    browser and the observer's own link."""
    add_people(client, 1)
    browser = Client()
    return browser, claim(browser, issue_link(client, "Person 0"))


@pytest.mark.django_db
def test_off_a_demo_system_the_shortcut_is_refused_the_hub_offers_none_and_an_observer_is_offered_no_profile(
    at_the_hub, settings
):
    browser, own_link = an_observer_of(at_the_hub)
    assert f'action="{SHORTCUT}"' in at_the_hub.get("/hub/").content.decode()
    assert "data-demo-reveal" in browser.get(own_link).content.decode()
    off_a_demo(settings)

    refused = open_up_to(at_the_hub, "calling")

    assert refused.status_code == 404
    assert SHORTCUT not in at_the_hub.get("/hub/").content.decode()
    shown = browser.get(f"{own_link}?profile=tied-both").content.decode()
    assert "data-demo-reveal" not in shown
    assert "placed" not in widget_data(shown, SORT)
    assert not response().completed_sections.keys() - {"onboarding", "walk-with-a-coach", "trusted-voices"}


@pytest.mark.django_db
def test_section_3_completes_section_1_and_the_cards_alone_and_section_4_the_rest_with_the_look_and_no_email(
    at_the_hub,
):
    """✨ Section 3 leaves Section 2 and the comparison alone; Section 4, which needs Section 2 finished, has the made-up
    people answer and records the look, which freezes collection as the real press does."""
    to_section_3 = open_up_to(at_the_hub, "shape")

    assert (to_section_3.status_code, to_section_3["Location"]) == (303, "/hub/")
    assert at_the_hub.get(SECTION_3).status_code == 200
    assert "designed" in response().completed_sections
    assert "others" not in response().completed_sections
    assert response().collection_frozen_at is None
    assert not ObserverResponse.objects.exists()

    to_section_4 = open_up_to(at_the_hub, "calling")

    assert (to_section_4.status_code, to_section_4["Location"]) == (303, "/hub/")
    assert at_the_hub.get(SECTION_4).status_code == 200
    assert {"designed", "others", "shape"} <= response().completed_sections.keys()
    assert "calling" not in response().completed_sections
    coach = Invitation.objects.get(contact__role=Contact.Role.COACH)
    assert coach.coach_answer == Invitation.CoachAnswer.ACCEPTED
    people = Contact.objects.filter(role=Contact.Role.CONTACT)
    assert people.count() == 3 and all(person.email == "" for person in people)
    assert ObserverResponse.counted(response()) == 3
    assert all(sent.is_test_data for sent in ObserverResponse.objects.all())
    assert response().collection_frozen_at is not None
    assert SORT in response().comparisons_viewed
    assert mail.outbox == []


@pytest.mark.django_db
def test_on_a_participant_who_has_started_everything_is_kept_and_only_what_is_missing_is_added(at_the_hub):
    submit_the_sort(at_the_hub)
    complete(at_the_hub, "designed")
    choose(at_the_hub)
    add_people(at_the_hub, 2)
    browser = Client()
    claim(browser, issue_link(at_the_hub, "Person 0"))
    send(browser, a_whole_sort())
    before = response()
    result = Result.objects.get()
    kept = {contact.pk: (contact.name, contact.email) for contact in Contact.objects.all()}
    [sent] = ObserverResponse.objects.all()

    assert open_up_to(at_the_hub, "letter").status_code == 303

    after = response()
    assert at_the_hub.get(SECTION_6).status_code == 200
    assert {key: after.answers[key] for key in before.answers} == before.answers
    assert {key: after.completed_sections[key] for key in before.completed_sections} == before.completed_sections
    assert Result.objects.get().scores == result.scores
    assert {pk: (contact.name, contact.email) for pk, contact in Contact.objects.in_bulk(kept).items()} == kept
    coach = Invitation.objects.get(contact__role=Contact.Role.COACH)
    assert coach.contact_id in kept and coach.coach_answer == Invitation.CoachAnswer.ACCEPTED
    assert ObserverResponse.objects.get(pk=sent.pk).is_test_data is False
    added = Contact.objects.exclude(pk__in=kept)
    assert added.count() == 2 and all(person.email == "" for person in added)
    assert ObserverResponse.counted(after) == 3


@pytest.mark.django_db
def test_an_observers_demo_profile_places_the_cards_some_not_seen_and_nothing_is_stored_until_they_send(at_the_hub):
    browser, own_link = an_observer_of(at_the_hub)
    offered = browser.get(own_link).content.decode()
    assert set(re.findall(r'<option value="([a-z-]+)"', offered)) == set(PROFILES)

    shown = browser.get(f"{own_link}?profile=tied-both").content.decode()

    placed = widget_data(shown, SORT)["placed"]
    loads = {item["id"]: item["loads"] for item in the_pathway()["instrument"]["items"]}
    unseen = [item for item, placement in placed.items() if placement == {"seen": False}]
    assert placed.keys() == loads.keys()
    assert len(unseen) == 9
    gifts = [gift for item in unseen for gift in loads[item]]
    assert max(gifts.count(gift) for gift in gifts) <= 2
    assert not ObserverResponse.objects.exists()
    assert send(browser, placed, link=own_link).status_code == 303
    assert ObserverResponse.counted(response()) == 1


@pytest.mark.django_db
def test_the_homepage_and_sign_up_suggest_a_made_up_example_address_only_where_demo_tools_are_on(client, settings):
    off_a_demo(settings)
    for page in ("/", "/accounts/signup/"):
        assert "@example.com" not in client.get(page).content.decode(), page

    settings.ANVILLE_DEMO_NOTICE = "This is a demo."

    for page in ("/", "/accounts/signup/"):
        assert re.search(r"\b[a-z]+[1-9][0-9]@example\.com\b", client.get(page).content.decode()), page
    assert "@example.com" not in client.get("/accounts/login/").content.decode()
