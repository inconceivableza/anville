"""✨ Observers' invitations: a link per person on the participant's contact list, which the participant copies and
sends themselves.

A link carries a token of 32 random bytes, of which only a hash is kept, so the link can be shown once, when it is
issued. It stops working when it expires (after the pathway document's lifetime, 30 days by default), when it is
revoked or reissued, or when its person is taken off the list, and a refused link says nothing about whose it was.
"""

import base64
import re
from datetime import datetime, timedelta, timezone

import pytest
import time_machine
from django.test import Client

from tests.journeys.test_contact_list import JO, PRIYA, participant, save_contacts, with_a_contact_list  # noqa: F401
from tests.journeys.test_hub import a_fresh_participant, signed_in_client  # noqa: F401  (fixtures, used by name)

ISSUED_AT = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
A_WRONG_TOKEN = "q" * 43


@pytest.fixture
def observer():
    """✨ Whoever follows a link: no account, and not signed in."""
    return Client()


def invitation_action(client, name, action):
    """✨ Where the invitations page posts to issue or revoke the named person's link."""
    page = client.get("/invitations/").content.decode()
    found = re.search(rf">{name}<.*?action=\"(/invitations/\d+/{action}/)\"", page, re.S)
    assert found, f"no way to {action} {name}'s link on the invitations page"
    return found.group(1)


def issue_link(client, name):
    """✨ Issue (or reissue) the named person's link as the participant does, and return its path as shown to copy."""
    issued = client.post(invitation_action(client, name, "issue"))
    assert issued.status_code == 200
    return re.search(r"http://testserver(/observe/[A-Za-z0-9_-]+/)", issued.content.decode()).group(1)


def token_of(link):
    return link.split("/")[2]


# Refusals


@pytest.mark.django_db
@pytest.mark.parametrize("dead", ["wrong", "expired", "revoked"])
def test_wrong_expired_and_revoked_links_are_refused_alike_saying_nothing_of_the_participant(
    participant, observer, dead
):
    with time_machine.travel(ISSUED_AT, tick=False):
        save_contacts(participant, JO)
        link = issue_link(participant, "Jo")
        if dead == "revoked":
            participant.post(invitation_action(participant, "Jo", "revoke"))
    refused_as_wrong = observer.get(f"/observe/{A_WRONG_TOKEN}/")

    with time_machine.travel(ISSUED_AT + timedelta(days=31 if dead == "expired" else 1), tick=False):
        refused = observer.get(f"/observe/{A_WRONG_TOKEN}/" if dead == "wrong" else link)

    page = refused.content.decode()
    assert refused.status_code == 404
    assert page == refused_as_wrong.content.decode()
    for detail in ("Jo", "jo@example.com", "participant@example.com"):
        assert detail not in page


@pytest.mark.django_db
def test_another_participant_can_neither_issue_nor_revoke_a_contacts_link(participant, observer):
    save_contacts(participant, JO)
    link = issue_link(participant, "Jo")
    issue, revoke = invitation_action(participant, "Jo", "issue"), invitation_action(participant, "Jo", "revoke")

    someone_else = a_fresh_participant(participant, "someone@example.com")

    assert someone_else.post(issue).status_code == 404
    assert someone_else.post(revoke).status_code == 404
    assert observer.get(link).status_code == 200


# Issuing


@pytest.mark.django_db
def test_an_issued_link_holds_32_random_bytes_of_which_only_a_hash_is_kept(participant):
    from engine.models import Invitation  # ✨ here, so the other tests fail on behaviour until the model exists

    save_contacts(participant, JO)

    token = token_of(issue_link(participant, "Jo"))

    assert len(base64.urlsafe_b64decode(token + "=")) == 32
    stored = [str(value) for row in Invitation.objects.values() for value in row.values()]
    assert stored
    assert not any(token in value for value in stored)


@pytest.mark.django_db
def test_an_issued_link_reaches_the_landing_page(participant, observer):
    save_contacts(participant, JO, PRIYA)

    assert observer.get(issue_link(participant, "Priya")).status_code == 200


@pytest.mark.django_db
def test_reissuing_a_link_stops_the_previous_one_and_the_new_one_works(participant, observer):
    save_contacts(participant, JO)
    first = issue_link(participant, "Jo")

    second = issue_link(participant, "Jo")

    assert second != first
    assert observer.get(first).status_code == 404
    assert observer.get(second).status_code == 200


# How long a link lasts


@pytest.mark.django_db
@pytest.mark.parametrize("authored_days, lasts_days", [(None, 30), (7, 7)])
def test_a_link_lasts_as_long_as_the_pathway_document_says_30_days_unless_it_says_otherwise(
    signed_in_client, load_pathway, observer, authored_days, lasts_days  # noqa: F811
):
    document = with_a_contact_list()
    if authored_days is not None:
        document["observers"] = {"link_lifetime_days": authored_days}
    load_pathway(document)
    with time_machine.travel(ISSUED_AT, tick=False):
        save_contacts(signed_in_client, JO)
        link = issue_link(signed_in_client, "Jo")

    with time_machine.travel(ISSUED_AT + timedelta(days=lasts_days, minutes=-1), tick=False):
        assert observer.get(link).status_code == 200
    with time_machine.travel(ISSUED_AT + timedelta(days=lasts_days, minutes=1), tick=False):
        assert observer.get(link).status_code == 404
