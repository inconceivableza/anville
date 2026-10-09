# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ An observer's landing page, and claiming the link (ADR 0005).

The participant holds a copy of every link they send, so the observer claims theirs on first use: starting exchanges
the link for a secret only the observer holds, kept in a cookie and shown once as a link of their own, and the
participant's copy stops working. Opening the link claims nothing. A second claim is told the link has been used, so a
participant who claimed it first is noticed, and can reissue; a reissued link reaches nothing the old one did.
"""

import base64
import re
from datetime import timedelta

import pytest
import time_machine
from django.test import Client

from engine.models import Invitation
from tests.journeys.test_contact_list import (  # noqa: F401  (participant is a fixture, used by name)
    JO,
    PRIYA,
    participant,
    save_contacts,
    with_a_contact_list,
)
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import (  # noqa: F401  (observer is a fixture, used by name)
    A_WRONG_TOKEN,
    ISSUED_AT,
    invitation_action,
    issue_link,
    observer,
    token_of,
)


def start(client, link):
    """✨ Press the landing page's start button: the claim."""
    return client.post(f"{link}start/")


def claim(client, link):
    """✨ Start from a link as the observer does, and return the link of their own that is shown to bookmark."""
    started = start(client, link)
    assert started.status_code == 200
    return re.search(r"http://testserver(/observe/[A-Za-z0-9_-]+/)", started.content.decode()).group(1)


def the_observers_page(client):
    """✨ The observer's own page, reached by the cookie claiming left, with no link."""
    return client.get("/observe/")


# Claiming


@pytest.mark.django_db
def test_starting_claims_the_link_for_the_observer_and_the_participants_copy_is_used_up(participant, observer):
    save_contacts(participant, JO)
    link = issue_link(participant, "Jo")

    own_link = claim(observer, link)

    assert own_link != link
    assert the_observers_page(observer).status_code == 200
    assert Client().get(own_link).status_code == 200
    assert participant.get(link).status_code == 410
    assert start(participant, link).status_code == 410


@pytest.mark.django_db
def test_the_observers_own_link_holds_32_random_bytes_of_which_only_a_hash_is_kept(participant, observer):
    save_contacts(participant, JO)

    secret = token_of(claim(observer, issue_link(participant, "Jo")))

    assert len(base64.urlsafe_b64decode(secret + "=")) == 32
    stored = [str(value) for row in Invitation.objects.values() for value in row.values()]
    assert stored
    assert not any(secret in value for value in stored)


@pytest.mark.django_db
def test_opening_the_link_claims_nothing(participant, observer):
    save_contacts(participant, JO)
    link = issue_link(participant, "Jo")

    assert participant.get(link).status_code == 200

    assert start(observer, link).status_code == 200


@pytest.mark.django_db
def test_a_second_claim_is_told_the_link_has_been_used_and_the_first_claim_keeps_working(participant, observer):
    """✨ Whoever claims first keeps the link, so a participant who claimed it is noticed by the observer, not hidden."""
    save_contacts(participant, JO)
    link = issue_link(participant, "Jo")
    first = Client()
    own_link = claim(first, link)

    assert start(observer, link).status_code == 410

    assert the_observers_page(first).status_code == 200
    assert first.get(own_link).status_code == 200
    assert the_observers_page(observer).status_code == 404


# When a claimed link stops


@pytest.mark.django_db
@pytest.mark.parametrize("ended", ["revoked", "expired", "taken off the list"])
def test_a_claimed_link_stops_when_it_is_revoked_or_expires_or_its_person_is_taken_off_the_list(
    participant, observer, ended
):
    with time_machine.travel(ISSUED_AT, tick=False):
        save_contacts(participant, JO, PRIYA)
        own_link = claim(observer, issue_link(participant, "Jo"))
        if ended == "revoked":
            participant.post(invitation_action(participant, "Jo", "revoke"))
        if ended == "taken off the list":
            save_contacts(participant, PRIYA)

    with time_machine.travel(ISSUED_AT + timedelta(days=31 if ended == "expired" else 1), tick=False):
        assert the_observers_page(observer).status_code == 404
        assert Client().get(own_link).status_code == 404


@pytest.mark.django_db
def test_a_link_reissued_after_a_claim_starts_unclaimed_and_the_old_claim_reaches_nothing(participant, observer):
    save_contacts(participant, JO)
    old_own_link = claim(Client(), issue_link(participant, "Jo"))

    reissued = issue_link(participant, "Jo")

    assert observer.get(reissued).status_code == 200
    assert Client().get(old_own_link).status_code == 404
    claim(observer, reissued)
    assert the_observers_page(observer).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("dead", ["wrong", "expired", "revoked"])
def test_starting_from_a_wrong_expired_or_revoked_link_is_refused_as_opening_one_is(participant, observer, dead):
    with time_machine.travel(ISSUED_AT, tick=False):
        save_contacts(participant, JO)
        link = issue_link(participant, "Jo")
        if dead == "revoked":
            participant.post(invitation_action(participant, "Jo", "revoke"))
    refused_as_wrong = observer.get(f"/observe/{A_WRONG_TOKEN}/")

    with time_machine.travel(ISSUED_AT + timedelta(days=31 if dead == "expired" else 1), tick=False):
        refused = start(observer, f"/observe/{A_WRONG_TOKEN}/" if dead == "wrong" else link)

    assert refused.status_code == 404
    assert refused.content.decode() == refused_as_wrong.content.decode()
    assert the_observers_page(observer).status_code == 404


# The privacy notice


@pytest.mark.django_db
def test_the_landing_page_shows_the_documents_privacy_notice_in_the_observers_wording(
    signed_in_client, load_pathway, observer  # noqa: F811
):
    document = with_a_contact_list()
    document["observers"] = {
        "privacy_notice": {"participant": "Wording meant for participants.", "observer": "Wording meant for observers."}
    }
    load_pathway(document)
    save_contacts(signed_in_client, JO)

    page = observer.get(issue_link(signed_in_client, "Jo")).content.decode()

    assert "Wording meant for observers." in page
    assert "Wording meant for participants." not in page
