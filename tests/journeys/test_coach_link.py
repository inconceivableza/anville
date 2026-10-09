# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The coach's link: the coach the participant chose is asked, through a link of the observer kind, to accept or
decline the six commitments from the content owner's coach-selection mock-up.

The participant issues, copies, revokes and reissues it on the coach page, beside the coach it is for, and is told
there whether the coach accepted or declined, nothing more. Only that answer is kept, on the link: which boxes were
ticked would be special category data about the coach. The coach has no account, and claims nothing, since the
participant holding a copy could claim as easily as use it (spec, Coach).
"""

import re
from datetime import timedelta

import pytest
import time_machine

from engine.models import Contact, Invitation, ObserverResponse, Response
from tests.journeys.test_answers import shown
from tests.journeys.test_coach_checklist import QUESTION_IDS, choose, step, text, the_coach_checklist
from tests.journeys.test_contact_list import JO, ONBOARDING, save_contacts, with_a_contact_list
from tests.journeys.test_hub import a_fresh_participant, signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import (  # noqa: F401  (observer is a fixture, used by name)
    A_WRONG_TOKEN,
    ISSUED_AT,
    issue_link,
    observer,
    token_of,
)


def with_a_coach_and_contacts():
    """✨ The test pathway with a contact list and Whatever You Do's coach checklist, both on onboarding's one page."""
    document = with_a_contact_list()
    document["content"]["sections"][0]["blocks"].append(the_coach_checklist())
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    """✨ A participant who has chosen Sam as their coach."""
    load_pathway(with_a_coach_and_contacts())
    assert choose(signed_in_client).status_code == 200
    return signed_in_client


def coach_link_action(client, action):
    """✨ Where the coach page posts to issue or revoke the coach's link, from a button within the checklist's form."""
    found = re.search(rf'formaction="(/invitations/\d+/{action}/)"', shown(client, ONBOARDING))
    assert found, f"no way to {action} the coach's link on the coach page"
    return found.group(1)


def issue_coach_link(client):
    """✨ Issue (or reissue) the coach's link as the participant does, and return its path as shown to copy."""
    issued = client.post(coach_link_action(client, "issue"), follow=True)
    assert issued.status_code == 200
    return re.search(r"http://testserver(/coaching/[A-Za-z0-9_-]+/)", issued.content.decode()).group(1)


def answer_as_coach(client, link, answer, ticked=QUESTION_IDS):
    """✨ The coach pressing accept or decline, with the boxes `ticked`."""
    return client.post(f"{link}answer/", {"answer": answer, "commitment": list(ticked)})


def told(client):
    """✨ What the coach page tells the participant of their coach's answer: waiting, accepted or declined."""
    found = re.search(r'data-coach-answer="(\w+)"', shown(client, ONBOARDING))
    return found.group(1) if found else None


def stored_besides_links():
    """✨ Every row the coach's answer must leave alone: the participant's response, their contacts, observers' answers."""
    return [list(model.objects.order_by("pk").values()) for model in (Response, Contact, ObserverResponse)]


# What is kept


@pytest.mark.django_db
def test_accepting_keeps_only_that_the_coach_accepted(participant, observer):
    link = issue_coach_link(participant)
    before = stored_besides_links()

    accepted = answer_as_coach(observer, link, "accept")

    assert accepted.status_code == 303
    assert stored_besides_links() == before
    kept = [str(value) for row in Invitation.objects.values() for value in row.values()]
    assert "accepted" in kept
    assert not any(question_id in value for value in kept for question_id in QUESTION_IDS)


@pytest.mark.django_db
@pytest.mark.parametrize("ticked", [[], QUESTION_IDS[:5]])
def test_accepting_needs_every_box_and_declining_needs_none(participant, observer, ticked):
    link = issue_coach_link(participant)

    refused = answer_as_coach(observer, link, "accept", ticked)

    assert refused.status_code == 400
    assert told(participant) == "waiting"
    assert answer_as_coach(observer, link, "decline", ticked).status_code == 303
    assert told(participant) == "declined"


# Refusals


@pytest.mark.django_db
@pytest.mark.parametrize("dead", ["wrong", "expired", "revoked"])
def test_wrong_expired_and_revoked_coach_links_are_refused_alike_saying_nothing_of_the_participant(
    participant, observer, dead
):
    with time_machine.travel(ISSUED_AT, tick=False):
        link = issue_coach_link(participant)
        if dead == "revoked":
            participant.post(coach_link_action(participant, "revoke"))
    refused_as_wrong = observer.get(f"/coaching/{A_WRONG_TOKEN}/")

    with time_machine.travel(ISSUED_AT + timedelta(days=31 if dead == "expired" else 1), tick=False):
        used = f"/coaching/{A_WRONG_TOKEN}/" if dead == "wrong" else link
        refused = observer.get(used)
        assert answer_as_coach(observer, used, "accept").status_code == 404

    page = refused.content.decode()
    assert refused.status_code == 404
    assert page == refused_as_wrong.content.decode()
    for detail in ("Sam", "sam@example.com", "participant"):
        assert detail not in page
    assert told(participant) != "accepted"


@pytest.mark.django_db
def test_an_observers_link_does_nothing_for_a_coach_and_the_coachs_link_nothing_for_an_observer(
    participant, observer
):
    save_contacts(participant, JO)
    jos = issue_link(participant, "Jo")
    coachs = issue_coach_link(participant)

    assert observer.get(f"/coaching/{token_of(jos)}/").status_code == 404
    assert answer_as_coach(observer, f"/coaching/{token_of(jos)}/", "accept").status_code == 404
    assert observer.get(f"/observe/{token_of(coachs)}/").status_code == 404
    assert observer.post(f"/observe/{token_of(coachs)}/start/").status_code == 404
    assert observer.post(f"/observe/{token_of(coachs)}/assessment/").status_code == 404
    assert observer.get(coachs).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("change", ["another coach saved", "coach removed"])
def test_saving_another_coach_or_removing_this_one_stops_the_coachs_link(participant, observer, change):
    link = issue_coach_link(participant)

    if change == "another coach saved":
        assert choose(participant, name="Alex", email="alex@example.com").status_code == 200
    else:
        assert step(participant, "remove").status_code == 200

    assert observer.get(link).status_code == 404


@pytest.mark.django_db
def test_a_coach_answers_once_per_link_and_a_reissued_link_asks_again(participant, observer):
    first = issue_coach_link(participant)
    answer_as_coach(observer, first, "accept")

    again = answer_as_coach(observer, first, "decline")

    assert again.status_code == 409
    assert told(participant) == "accepted"
    second = issue_coach_link(participant)
    assert told(participant) == "waiting"
    assert observer.get(first).status_code == 404
    assert answer_as_coach(observer, second, "decline").status_code == 303
    assert told(participant) == "declined"


@pytest.mark.django_db
@pytest.mark.parametrize("answer, outcome", [("accept", "accepted"), ("decline", "declined")])
def test_the_participant_is_told_the_answer_and_nothing_of_the_boxes(participant, observer, answer, outcome):
    """✨ A decline with five boxes ticked is told as a decline, as one with none would be. The coach page keeps its
    way to choose someone else."""
    link = issue_coach_link(participant)

    answer_as_coach(observer, link, answer, QUESTION_IDS if answer == "accept" else QUESTION_IDS[:5])

    page = shown(participant, ONBOARDING)
    assert told(participant) == outcome
    assert not re.search(r"\b(5|five) of (6|six)\b", text(page), re.I)
    assert re.search(r'<button[^>]*name="step" value="restart"', page)


# Whose link


@pytest.mark.django_db
def test_another_participant_can_neither_issue_nor_revoke_the_coachs_link(participant, observer):
    link = issue_coach_link(participant)
    issue, revoke = coach_link_action(participant, "issue"), coach_link_action(participant, "revoke")

    someone_else = a_fresh_participant(participant, "someone@example.com")

    assert someone_else.post(issue).status_code == 404
    assert someone_else.post(revoke).status_code == 404
    assert observer.get(link).status_code == 200


# What the coach sees


@pytest.mark.django_db
def test_the_coachs_link_names_the_participant_and_offers_a_box_per_commitment(participant, observer):
    page = observer.get(issue_coach_link(participant)).content.decode()

    assert "participant" in text(page)
    for question_id in QUESTION_IDS:
        assert re.search(rf'<input[^>]*type="checkbox"[^>]*name="commitment"[^>]*value="{question_id}"', page)
