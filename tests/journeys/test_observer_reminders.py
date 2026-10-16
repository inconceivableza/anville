# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Observers who have not sent are reminded once a week while their link works, and can stop it (ticket 43a,
ADR 0016).

The daily job is run here by calling it, as its command does, against the database; the stop page is driven over HTTP.
"""

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import pytest
import time_machine
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.utils import timezone as django_timezone

from django.core.mail.backends import locmem

from engine.models import Contact, Invitation, Response
from engine.reminders import send_due_reminders, stop_link
from tests.documents import complete_sort
from tests.journeys.test_consent import withdraw_consent
from tests.journeys.test_contact_list import ONBOARDING, save_contacts, save_person
from tests.journeys.test_invitations import invitation_action, issue_link
from tests.journeys.test_observer_assessment import send
from tests.journeys.test_observer_landing import claim
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
def test_two_runs_at_once_never_send_the_same_reminder_twice(participant, monkeypatch):
    as_participant(participant, 0, save_contacts, BEA)
    delivering = locmem.EmailBackend.send_messages
    overlapped = []

    def while_sending_another_run_starts(backend, messages):
        if not overlapped:
            overlapped.append(True)
            send_due_reminders()  # ✨ the second run, started while the first is part-way through sending
        return delivering(backend, messages)

    monkeypatch.setattr(locmem.EmailBackend, "send_messages", while_sending_another_run_starts)

    reminded = run_on(7)

    assert sorted(reminded) == [[ALEX[1]], [BEA[1]]]


@pytest.mark.django_db
def test_a_failed_send_is_tried_again_on_the_next_run(participant, monkeypatch):
    delivering = locmem.EmailBackend.send_messages

    def refused(backend, messages):
        raise ConnectionError("the provider is down")

    monkeypatch.setattr(locmem.EmailBackend, "send_messages", refused)
    assert run_on(7) == []
    monkeypatch.setattr(locmem.EmailBackend, "send_messages", delivering)

    assert run_on(8) == [[ALEX[1]]]
    assert run_on(9) == []


def own_link_of_someone_who_sent(participant):
    """✨ Alex claims a fresh link the participant gave them and sends, the day after the links were made; returns the
    link of their own."""
    link = as_participant(participant, 0, issue_link, ALEX[0])
    with time_machine.travel(ISSUED_AT + DAY, tick=False):
        observer = Client()
        own_link = claim(observer, link)
        assert send(observer, complete_sort()).status_code == 303
    return own_link


def reissue(client):
    return issue_link(client, ALEX[0])


def change_address(client):
    return save_person(client, ALEX[0], (ALEX[0], "alex.new@harbourfield.uk"))


@pytest.mark.django_db
@pytest.mark.parametrize("then", [None, "reissue", "withdrawal", "edit"])
def test_someone_who_sent_is_never_reminded_through_a_reissue_a_withdrawal_or_an_edit(participant, then):
    own_link = own_link_of_someone_who_sent(participant)
    if then == "reissue":
        as_participant(participant, 2, reissue)
    if then == "withdrawal":
        with time_machine.travel(ISSUED_AT + 2 * DAY, tick=False):
            assert Client().post(f"{own_link}withdraw/").status_code == 200
    if then == "edit":
        as_participant(participant, 2, change_address)

    assert [run_on(day) for day in range(3, 36)] == [[]] * 33


@pytest.mark.django_db
def test_a_reissue_restarts_the_week(participant):
    as_participant(participant, 3, reissue)

    assert run_on(7) == []
    assert run_on(10) == [[ALEX[1]]]


@pytest.mark.django_db
def test_after_an_unfreeze_an_overdue_reminder_goes_on_the_next_run_and_then_weekly_again(participant):
    as_participant(participant, 3, freeze)
    assert run_on(7) == [] and run_on(14) == []

    with time_machine.travel(ISSUED_AT + 16 * DAY, tick=False):
        Response.objects.get().unfreeze_below_minimum()

    assert run_on(17) == [[ALEX[1]]]
    assert run_on(18) == []
    assert run_on(21) == [[ALEX[1]]]


# Stopping


def first_reminder(participant):
    run_on(7)
    return mail.outbox[-1]


def stop_paths_of(reminder):
    """✨ Where the email's stop link and its List-Unsubscribe header lead."""
    in_the_body = re.search(r"(http\S+/reminders/stop/\S+/)", reminder.body).group(1)
    in_the_header = reminder.extra_headers["List-Unsubscribe"].strip("<>")
    return urlsplit(in_the_body).path, urlsplit(in_the_header).path


def stopped(participant, day):
    """✨ Whether Alex goes unreminded from `day` until their link runs out, through a reissue and an edit meanwhile."""
    as_participant(participant, day, reissue)
    as_participant(participant, day, change_address)
    return all(run_on(later, ISSUED_AT + day * DAY) == [] for later in range(1, 30))


@pytest.mark.django_db
def test_opening_the_stop_page_changes_nothing(participant):
    by_link, _ = stop_paths_of(first_reminder(participant))

    opened = Client().get(by_link)

    assert opened.status_code == 200
    assert run_on(14) == [[ALEX[1]]]


@pytest.mark.django_db
@pytest.mark.parametrize("pressed", ["the page's button", "one-click unsubscribe"])
@pytest.mark.parametrize("link", ["working", "revoked"])
def test_a_stop_holds_through_a_reissue_and_an_edit_whatever_happened_to_the_link(participant, pressed, link):
    by_link, by_header = stop_paths_of(first_reminder(participant))
    if link == "revoked":
        as_participant(participant, 8, lambda client: client.post(invitation_action(client, ALEX[0], "revoke")))

    if pressed == "the page's button":
        action = re.search(r'<form method="post" action="([^"]+)"', Client().get(by_link).content.decode()).group(1)
        done = Client(enforce_csrf_checks=True).post(action)
    else:
        done = Client(enforce_csrf_checks=True).post(by_header, {"List-Unsubscribe": "One-Click"})

    assert done.status_code == 200
    assert stopped(participant, 9)


@pytest.mark.django_db
def test_a_tampered_stop_address_is_refused_as_a_dead_link_is(participant):
    by_link, _ = stop_paths_of(first_reminder(participant))
    signed = by_link.split("/")[-2]
    someone_else = f"{int(signed.split(':')[0]) + 1}:{signed.split(':')[1]}"

    refused = Client().post(by_link.replace(signed, someone_else))

    assert refused.status_code == 404
    assert run_on(14) == [[ALEX[1]]]


@pytest.mark.django_db
def test_a_reminder_and_a_stop_change_nothing_on_the_participants_pages(participant):
    pages = ("/hub/", f"/sections/{ONBOARDING}/")

    def seen():
        with time_machine.travel(ISSUED_AT + 9 * DAY, tick=False):
            participant.force_login(get_user_model().objects.get())
            shown = [participant.get(page) for page in pages]
            assert [page.status_code for page in shown] == [200, 200]
            return [CSRF.sub("", page.content.decode()) for page in shown]

    before = seen()
    by_link, _ = stop_paths_of(first_reminder(participant))
    Client().post(by_link)

    assert seen() == before


CSRF = re.compile(r'name="csrfmiddlewaretoken" value="[^"]*"|data-csrf="[^"]*"|"X-CSRFToken": "[^"]*"')


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
