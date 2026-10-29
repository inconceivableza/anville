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
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import pytest
import time_machine
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.utils import timezone as django_timezone

from engine.models import Contact, Invitation, Response
from engine.reminders import send_due_reminders, stop_link
from tests.documents import complete_sort
from tests.journeys.test_answers import shown
from tests.journeys.test_contact_list import (  # noqa: F401  (participant is a fixture, used by name)
    ONBOARDING,
    JO,
    PRIYA,
    participant,
    save_contacts,
    take_off_the_list,
    with_a_contact_list,
)
from tests.journeys.test_consent import withdraw_consent
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
    """✨ Start from a link as the observer does, and return the link of their own it takes them on to."""
    started = start(client, link)
    assert started.status_code == 302
    return started["Location"]


def the_observers_page(client):
    """✨ The observer's own page, reached by the cookie claiming left, with no link: on to their own link, if any."""
    return client.get("/observe/", follow=True)


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

    assert start(observer, link).status_code == 302


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
            take_off_the_list(participant, "Jo")

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


# Opening the start address (ticket 78): a reload, a bookmark or Back after starting


def open_start(client, link):
    """✨ Open the start address as a reload from the address bar or a bookmark does: a GET, followed wherever it leads."""
    return client.get(f"{link}start/", follow=True)


@pytest.mark.django_db
def test_opening_an_unclaimed_links_start_address_claims_nothing_and_starting_from_there_still_works(
    participant, observer
):
    save_contacts(participant, JO)
    link = issue_link(participant, "Jo")

    opened = open_start(observer, link)

    assert opened.status_code == 200
    assert f'action="{link}start/"' in opened.content.decode()
    assert Client().get(link).status_code == 200
    claim(observer, link)
    assert the_observers_page(observer).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("dead", ["wrong", "expired", "revoked", "taken off the list", "withdrawn by the observer"])
def test_opening_a_refused_links_start_address_shows_the_refusal_its_plain_address_shows(participant, observer, dead):
    with time_machine.travel(ISSUED_AT, tick=False):
        save_contacts(participant, JO, PRIYA)
        link = f"/observe/{A_WRONG_TOKEN}/" if dead == "wrong" else issue_link(participant, "Jo")
        if dead == "revoked":
            participant.post(invitation_action(participant, "Jo", "revoke"))
        if dead == "taken off the list":
            take_off_the_list(participant, "Jo")
        if dead == "withdrawn by the observer":
            link = claim(observer, link)  # ✨ the participant's copy is used, not refused: the next test
            assessment.withdraw(observer)

    with time_machine.travel(ISSUED_AT + timedelta(days=31 if dead == "expired" else 1), tick=False):
        opened = open_start(observer, link)
        plain = observer.get(link)

    assert opened.status_code == plain.status_code == 404
    assert opened.content.decode() == plain.content.decode()


@pytest.mark.django_db
def test_opening_a_used_links_start_address_says_it_has_been_used_as_its_plain_address_does(participant, observer):
    save_contacts(participant, JO)
    link = issue_link(participant, "Jo")
    claim(observer, link)

    opened = open_start(observer, link)

    assert opened.status_code == observer.get(link).status_code == 410
    assert opened.content.decode() == observer.get(link).content.decode()


# While the participant's consent is withdrawn (ticket 45)


@pytest.mark.django_db
def test_while_the_participant_has_withdrawn_every_observers_link_is_refused_and_nothing_is_claimed(
    participant, observer
):
    save_contacts(participant, JO, PRIYA)
    unclaimed = issue_link(participant, "Priya")
    own_link = claim(observer, issue_link(participant, "Jo"))

    withdraw_consent(participant)

    stranger = Client()
    for refused in (
        stranger.get(unclaimed),
        start(stranger, unclaimed),
        stranger.get(own_link),
        the_observers_page(observer),
    ):
        assert refused.status_code == 404
    assert not Invitation.objects.filter(contact__name="Priya", claimed_at__isnull=False).exists()


@pytest.mark.django_db
def test_while_the_participant_has_withdrawn_a_link_is_refused_exactly_as_a_revoked_one_is(participant, observer):
    """✨ So a link says nothing of the participant's consent to whoever holds it."""
    save_contacts(participant, JO, PRIYA)
    revoked = issue_link(participant, "Priya")
    participant.post(invitation_action(participant, "Priya", "revoke"))
    refused_as_revoked = observer.get(revoked).content.decode()
    link = issue_link(participant, "Jo")

    withdraw_consent(participant)

    refused = observer.get(link)
    assert refused.status_code == 404
    assert refused.content.decode() == refused_as_revoked


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


# A fresh link from a reminder (ticket 43b, ADR 0016)

# ✨ Imported here, after `claim` and `the_observers_page`, since that module imports them from this one.
import tests.journeys.test_observer_assessment as assessment  # noqa: E402

# ✨ At no reserved example domain, so the reminders job does not pass them over.
ALEX = ("Alex", "alex@harbourfield.uk")
LINKS_MADE = datetime(2030, 3, 4, 14, 0, tzinfo=timezone.utc)


@pytest.fixture
def reminded(signed_in_client, load_pathway):  # noqa: F811
    """✨ A participant whose observer was sent a link and, a week on, a reminder; the clock stays at the day after it.
    Gives the participant's client and their copy of the link."""
    load_pathway(assessment.observed_pathway())
    user = get_user_model().objects.get()
    with time_machine.travel(LINKS_MADE, tick=False):
        signed_in_client.force_login(user)
        save_contacts(signed_in_client, ALEX)
        link = issue_link(signed_in_client, ALEX[0])
    with time_machine.travel(LINKS_MADE + timedelta(days=7, hours=1), tick=False):
        assert send_due_reminders() == 1
    with time_machine.travel(LINKS_MADE + timedelta(days=8), tick=False):
        signed_in_client.force_login(user)
        yield signed_in_client, link


def answer_address():
    """✨ Where the last reminder's "Answer for …" button leads, from the email's HTML part."""
    html = next(content for content, kind in mail.outbox[-1].alternatives if kind == "text/html")
    return urlsplit(re.search(r'href="([^"]*/reminders/answer/[^"]+)"', html).group(1)).path


def press(client, address):
    """✨ Press the button on the reminder's page, and return the observer's own link it takes them on to."""
    pressed = client.post(address)
    assert pressed.status_code == 302
    return pressed["Location"]


@pytest.mark.django_db
def test_opening_the_reminders_page_changes_nothing_and_pressing_it_gives_a_fresh_claimed_link_into_the_assessment(
    reminded, observer
):
    _, link = reminded
    address = answer_address()

    assert observer.get(address).status_code == 200
    assert Client().get(address).status_code == 200
    assert Client().get(link).status_code == 200  # ✨ still unclaimed
    assert observer.get(f"/observe/{address.split('/')[3]}/").status_code == 404  # ✨ not a link the landing takes

    own_link = press(observer, address)

    assert Client().get(own_link).status_code == 200
    assert assessment.send(observer, complete_sort()).status_code == 303  # ✨ by the cookie the press left
    assert assessment.send(Client(), complete_sort(), link=own_link).status_code == 409  # ✨ the same claim


@pytest.mark.django_db
def test_pressing_the_reminders_button_takes_the_observer_to_their_own_link(reminded, observer):
    """✨ As starting from the landing does (the developer's 29 Oct hand check), so it is the page they are on."""
    pressed = observer.post(answer_address())

    assert pressed.status_code == 302
    assert re.fullmatch(r"/observe/[A-Za-z0-9_-]+/", pressed["Location"])
    assert Client().get(pressed["Location"]).status_code == 200


def frozen(participant):
    Response.objects.update(collection_frozen_at=django_timezone.now())


def tampered(address):
    """✨ The address with the last character of its signature changed."""
    signed = address.split("/")[3]
    return address.replace(signed, signed[:-1] + ("A" if signed[-1] != "A" else "B"))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ended", ["expired", "revoked", "reissued", "taken off the list", "frozen", "consent withdrawn", "tampered", "stop"]
)
def test_the_reminders_address_is_refused_as_a_dead_link_is_once_the_link_cannot_be_answered(
    reminded, observer, ended
):
    participant, _ = reminded
    address = answer_address()
    refused_as_dead = observer.get(f"/observe/{A_WRONG_TOKEN}/").content.decode()
    later = LINKS_MADE + timedelta(days=31 if ended == "expired" else 8)
    if ended == "revoked":
        participant.post(invitation_action(participant, ALEX[0], "revoke"))
    if ended == "reissued":
        issue_link(participant, ALEX[0])
    if ended == "taken off the list":
        take_off_the_list(participant, ALEX[0])
    if ended == "frozen":
        frozen(participant)
    if ended == "consent withdrawn":
        withdraw_consent(participant)
    if ended == "tampered":
        address = tampered(address)
    if ended == "stop":  # ✨ a stop address, which is signed for the contact with another salt
        address = address.replace(address.split("/")[3], urlsplit(stop_link(Contact.objects.get())).path.split("/")[3])

    with time_machine.travel(later, tick=False):
        for refused in (observer.get(address), observer.post(address)):
            assert refused.status_code == 404
            assert refused.content.decode() == refused_as_dead
        assert assessment.send(observer, complete_sort()).status_code == 404  # ✨ nothing was claimed


@pytest.mark.django_db
@pytest.mark.parametrize("claimed_before", [False, True])
def test_after_the_press_the_participants_copy_and_any_earlier_claim_are_dead_and_the_expiry_and_page_are_unchanged(
    reminded, observer, claimed_before
):
    participant, link = reminded
    earlier = claim(Client(), link) if claimed_before else None
    expires_at = Invitation.objects.get().expires_at
    page = without_csrf_tokens(shown(participant, ONBOARDING))

    own_link = press(observer, answer_address())

    assert Client().get(link).status_code == 404
    if earlier:
        assert Client().get(earlier).status_code == 404
    assert Client().get(own_link).status_code == 200
    assert Invitation.objects.get().expires_at == expires_at
    assert without_csrf_tokens(shown(participant, ONBOARDING)) == page


def without_csrf_tokens(page):
    """✨ A page with its CSRF tokens taken out, since each render masks them afresh."""
    return re.sub(r'name="csrfmiddlewaretoken" value="[^"]*"', "", page)


@pytest.mark.django_db
def test_the_reminders_button_works_again_until_the_person_has_sent_and_still_after_they_stopped_reminders(
    reminded, observer
):
    address = answer_address()
    assert Client().post(urlsplit(stop_link(Contact.objects.get())).path).status_code == 200

    first = press(Client(), address)
    second = press(observer, address)

    assert Client().get(first).status_code == 404
    assert assessment.send(observer, complete_sort()).status_code == 303
    assert Client().get(second).status_code == 200
    assert Client().get(address).status_code == 404
    assert Client().post(address).status_code == 404
