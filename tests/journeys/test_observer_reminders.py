# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Observers who have not sent are reminded once a week while their link works, and can stop it (ticket 43a,
ADR 0016).

The daily job is run here by calling it, as its command does, against the database; the stop page is driven over HTTP.
"""

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
from tests.journeys.test_consent import withdraw_consent
from tests.journeys.test_contact_list import save_contacts, save_person
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_observer_assessment import observed_pathway

# ✨ Addresses at no reserved example domain, so the job does not skip them.
ALEX, BEA = ("Alex", "alex@harbourfield.uk"), ("Bea", "bea@harbourfield.uk")

ISSUED_AT = datetime(2030, 3, 4, 14, 0, tzinfo=timezone.utc)
DAY = timedelta(days=1)


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(observed_pathway())
    with time_machine.travel(ISSUED_AT, tick=False):
        signed_in_client.force_login(get_user_model().objects.get())  # ✨ a session of that day, so it has not expired
        save_contacts(signed_in_client, ALEX)
    return signed_in_client


def as_participant(client, day, act, *args):
    """✨ Something the participant does `day` days after the links were made."""
    with time_machine.travel(ISSUED_AT + day * DAY, tick=False):
        client.force_login(get_user_model().objects.get())
        return act(client, *args)


def run_on(day, at=ISSUED_AT):
    """✨ The daily job, run `day` days after `at`, the next morning's run of that day; returns the reminders sent by it."""
    before = len(mail.outbox)
    with time_machine.travel(at + day * DAY + timedelta(hours=1), tick=False):
        send_due_reminders()
    return [message.to for message in mail.outbox[before:]]


# Who is reminded, and when


@pytest.mark.django_db
def test_a_person_who_has_not_sent_is_reminded_a_week_after_their_link_was_made_and_weekly_after_while_it_works(
    participant,
):
    reminded = [run_on(day) for day in range(1, 36)]

    days = [day for day, to in enumerate(reminded, start=1) if to]
    assert days == [7, 14, 21, 28]
    assert all(to == [[ALEX[1]]] for to in filter(None, reminded))


def freeze(client):
    Response.objects.update(collection_frozen_at=django_timezone.now())


def stop_from_the_email(client):
    return Client().post(stop_path(Contact.objects.get(name=ALEX[0])))


def stop_path(contact):
    return urlsplit(stop_link(contact)).path


def at_an_example_domain(client):
    return save_person(client, ALEX[0], (ALEX[0], "alex@mail.example.org"))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "act",
    [freeze, withdraw_consent, stop_from_the_email, at_an_example_domain],
    ids=["frozen", "consent withdrawn", "stopped", "example domain"],
)
def test_nobody_is_reminded_while_frozen_or_withdrawn_once_stopped_or_at_an_example_domain(participant, act):
    as_participant(participant, 3, act)

    assert run_on(7) == []


@pytest.mark.django_db
def test_a_coach_is_never_reminded(participant):
    with time_machine.travel(ISSUED_AT, tick=False):
        Contact.objects.all().delete()
        coach = Contact.objects.create(
            response=Response.objects.get(), block_id="coach", role=Contact.Role.COACH, position=0, name="Sam",
            email="sam@harbourfield.uk",
        )
        Invitation.issue(coach, timedelta(days=30))

    assert run_on(7) == []
