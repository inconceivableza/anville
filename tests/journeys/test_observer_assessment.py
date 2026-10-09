# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The observer's assessment: the same sort, about the participant, in the third person (ADR 0005).

An observer reaches it only through the link they claimed, sends it once, and never sees it again through any link.
"""

import json

import pytest
from django.test import Client

from engine.models import Invitation, ObserverAssessments, ObserverResponse, Response
from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_contact_list import JO, PRIYA, save_contacts
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import (  # noqa: F401  (observer is a fixture, used by name)
    A_WRONG_TOKEN,
    invitation_action,
    issue_link,
    observer,
    token_of,
)
from tests.journeys.test_observer_landing import claim, the_observers_page
from tests.journeys.test_results import widget_data


def observed_pathway():
    """✨ The sort pathway with a contact list in onboarding, and observer wording for one bucket and the sort's heading
    (its item a5 already has observer wording)."""
    document = sort_pathway()
    document["content"]["sections"][0]["blocks"].append({"id": "contacts", "type": "contact_list", "min_rows": 2})
    not_me = document["instrument"]["buckets"][0]
    not_me["label"] = {"participant": not_me["label"], "observer": "Not {name}"}
    document["presentation"]["sort_wording"] = {
        "sort_heading": {"participant": "Sort your strengths", "observer": "Sort {name}'s strengths"},
    }
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(observed_pathway())
    save_contacts(signed_in_client, JO, PRIYA)
    return signed_in_client


def send(client, assessment, link=None):
    """✨ Send an observer assessment as the widget's form does: through a link if given, else by the observer cookie."""
    return client.post(f"{link}assessment/" if link else "/observe/assessment/", {"value": json.dumps(assessment)})


def observer_assessments():
    """✨ What the observer average reads of the participant's observers."""
    return ObserverResponse.assessments_for(Response.objects.get())


# Sending


@pytest.mark.django_db
@pytest.mark.parametrize("through", ["cookie", "own link"])
def test_an_assessment_sent_through_the_claimed_link_counts_on_its_own_and_leaves_the_participants_answers_alone(
    participant, observer, through  # noqa: F811
):
    own_link = claim(observer, issue_link(participant, "Jo"))
    answers_before = Response.objects.get().answers

    if through == "cookie":
        sent = send(observer, complete_sort())
    else:
        sent = send(Client(), complete_sort(), own_link)

    assert sent.status_code == 303
    assert sent["Location"] == ("/observe/" if through == "cookie" else own_link)
    assert observer_assessments() == ObserverAssessments(assessments=[complete_sort()], all_test_data=False)
    assert Response.objects.get().answers == answers_before


@pytest.mark.django_db
@pytest.mark.parametrize("by", ["unclaimed copy", "claimed copy", "wrong link", "no claim"])
def test_neither_the_participants_copy_nor_a_wrong_link_nor_no_claim_can_send_an_assessment(
    participant, observer, by  # noqa: F811
):
    link = issue_link(participant, "Jo")
    if by == "claimed copy":
        claim(observer, link)
    if by == "wrong link":
        link = f"/observe/{A_WRONG_TOKEN}/"

    refused = send(participant, complete_sort(), None if by == "no claim" else link)

    assert refused.status_code == 404
    assert not ObserverResponse.objects.exists()


@pytest.mark.django_db
def test_once_sent_the_assessment_is_locked_and_no_link_offers_it_or_shows_it_again(participant, observer):  # noqa: F811
    own_link = claim(observer, issue_link(participant, "Jo"))
    first = complete_sort(a5={"bucket": "strength", "value": 73})
    send(observer, first)

    again = send(Client(), complete_sort(), own_link)

    assert again.status_code == 409
    assert observer_assessments().assessments == [first]
    for page in (the_observers_page(observer), Client().get(own_link)):
        assert page.status_code == 200
        assert widget_data(page.content.decode()) is None
        assert 'name="value"' not in page.content.decode()


@pytest.mark.django_db
def test_an_assessment_that_breaks_the_contract_is_refused_and_nothing_is_stored(participant, observer):  # noqa: F811
    claim(observer, issue_link(participant, "Jo"))

    refused = send(observer, complete_sort(a5={"bucket": "strength", "value": 101}))

    assert refused.status_code == 400
    assert not ObserverResponse.objects.exists()


# Outliving the link (ADR 0007), held apart from who sent it


@pytest.mark.django_db
@pytest.mark.parametrize("ended", ["revoked", "reissued", "taken off the list"])
def test_a_sent_assessment_survives_its_link_being_revoked_or_reissued_or_its_person_taken_off_the_list(
    participant, observer, ended  # noqa: F811
):
    claim(observer, issue_link(participant, "Jo"))
    send(observer, complete_sort())

    if ended == "revoked":
        participant.post(invitation_action(participant, "Jo", "revoke"))
    if ended == "reissued":
        issue_link(participant, "Jo")
    if ended == "taken off the list":
        save_contacts(participant, PRIYA)

    assert observer_assessments().assessments == [complete_sort()]


@pytest.mark.django_db
def test_a_reissued_link_once_claimed_sends_an_assessment_of_its_own_and_both_count(participant, observer):  # noqa: F811
    claim(observer, issue_link(participant, "Jo"))
    send(observer, complete_sort())
    reissued_to = Client()
    claim(reissued_to, issue_link(participant, "Jo"))

    assert send(reissued_to, complete_sort()).status_code == 303

    assert len(observer_assessments().assessments) == 2


@pytest.mark.django_db
def test_nothing_kept_with_a_sent_assessment_ties_it_to_the_contact_or_their_link(participant, observer):  # noqa: F811
    secret = token_of(claim(observer, issue_link(participant, "Jo")))
    send(observer, complete_sort())

    invitation = Invitation.objects.get()
    kept = ObserverResponse.objects.values().get()
    assert "contact_id" not in kept and "invitation_id" not in kept
    ties = {invitation.token_hash, invitation.secret_hash, secret}
    assert [field for field, value in kept.items() if str(value) in ties] == []


# The observer's wording


@pytest.mark.django_db
def test_the_observers_widget_is_in_the_observers_wording_naming_the_participant(participant, observer):  # noqa: F811
    claim(observer, issue_link(participant, "Jo"))

    page = the_observers_page(observer).content.decode()

    shown = widget_data(page)
    assert shown["items"] == [
        {"id": "a5", "text": "Building something that will outlast them"},
        {"id": "p1", "text": "Going against the grain"},
    ]
    assert shown["buckets"][0]["label"] == "Not participant"
    assert shown["wording"]["sort_heading"] == "Sort participant's strengths"
    assert "{name}" not in json.dumps(shown)
    for participants_wording in ("outlast you", "Sort your strengths", '"Not me"'):
        assert participants_wording not in page
