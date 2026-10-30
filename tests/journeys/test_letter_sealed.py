# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The letter to the participant's future self is sealed as its section is finished, until a date they pick, then
opens in place, and an email to their own address says it is ready (ticket 104).

The section is driven over HTTP; the daily job is run by calling it, as its command does, as the reminders' tests do.
"""

from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

import pytest
import time_machine
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail.backends import locmem

from engine.letters import send_ready_letters
from engine.models import Publication, Response, SealedLetter
from tests.documents import letter_pathway
from tests.journeys.test_consent import give_consent, withdraw_consent

LETTER = "Dear me, remember the harbour at dawn."
ADDRESS = "sam@harbourfield.uk"  # ✨ at no reserved example domain, so the job does not skip it
SEALED_AT = datetime(2030, 3, 4, 10, 0, tzinfo=timezone.utc)
OPENS_ON = date(2031, 3, 4)
SECTION = "/sections/letter/"


def at(day, hour=10):
    """✨ `day` (a date) at `hour`, UTC, the site's time zone."""
    return datetime(day.year, day.month, day.day, hour, tzinfo=timezone.utc)


def on(client, when, act, *args):
    """✨ Something the participant does at `when`, in a session of that day."""
    with time_machine.travel(when, tick=False):
        client.force_login(get_user_model().objects.get())
        return act(client, *args)


def answer(client, block_id, value):
    return client.post(f"/answers/{block_id}/", {"value": value, "version": Publication.current_version().pk})


def seal(client, opens_on=OPENS_ON):
    """✨ The press that finishes the section, with the date the letter opens on, as the form sends it."""
    return client.post(f"{SECTION}complete/", {"opens_on": str(opens_on)})


def reopen(client):
    return client.post(f"{SECTION}reopen/")


def shown(client):
    return client.get(SECTION).content.decode()


@pytest.fixture
def participant(client, load_pathway):
    """✨ Onboarding done, the letter written and the closing rating answered, on the day the letter is sealed."""
    load_pathway(letter_pathway())
    get_user_model().objects.create_user(username="sam", email=ADDRESS)
    with time_machine.travel(SEALED_AT, tick=False):
        client.force_login(get_user_model().objects.get())
        give_consent(client)
        client.post("/sections/onboarding/complete/")
        answer(client, "letter-box", LETTER)
        answer(client, "closing", "7")
    return client


@pytest.fixture
def sealed(participant):
    assert on(participant, SEALED_AT, seal).status_code == 303
    return participant


def opened_at():
    return SealedLetter.objects.get().opened_at


def run_on(day, hour=11):
    """✨ The daily job, run at `hour` on `day`; returns the emails it sent."""
    before = len(mail.outbox)
    with time_machine.travel(at(day, hour), tick=False):
        send_ready_letters()
    return mail.outbox[before:]


# Sealing


@pytest.mark.django_db
def test_once_sealed_neither_the_page_nor_a_save_carries_the_letter_and_a_save_changes_nothing(sealed):
    page = on(sealed, SEALED_AT + timedelta(days=1), shown)
    saved = on(sealed, SEALED_AT + timedelta(days=1), answer, "letter-box", "Dear me, something else.")

    assert LETTER not in page
    assert "4 March 2031" in page
    assert saved.status_code == 409
    assert LETTER not in saved.content.decode()
    assert Response.objects.get().answers["letter-box"] == LETTER


@pytest.mark.django_db
@pytest.mark.parametrize(
    "opens_on",
    ["", "next spring", "2030-06-03", "2032-03-05"],
    ids=["missing", "garbled", "a day under 3 months", "a day over 24 months"],
)
def test_a_date_outside_3_to_24_months_is_refused_and_nothing_is_finished_or_sealed(participant, opens_on):
    refused = on(participant, SEALED_AT, seal, opens_on)

    assert refused.status_code == 400
    assert "4 June 2030" in refused.content.decode() and "4 March 2032" in refused.content.decode()
    assert "letter" not in Response.objects.get().completed_sections
    assert not SealedLetter.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("opens_on", [date(2030, 6, 4), date(2032, 3, 4)], ids=["3 months", "24 months"])
def test_a_date_from_3_to_24_months_on_seals_the_letter_until_then(participant, opens_on):
    assert on(participant, SEALED_AT, seal, opens_on).status_code == 303

    assert SealedLetter.objects.get().opens_on == opens_on
    assert "letter" in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_marking_the_section_not_complete_leaves_the_letter_sealed_and_finishing_again_keeps_its_date(sealed):
    later = SEALED_AT + timedelta(days=2)
    on(sealed, later, reopen)
    page = on(sealed, later, shown)
    finished_again = on(sealed, later, seal, date(2031, 9, 4))

    assert LETTER not in page
    assert "4 March 2031" in page
    assert finished_again.status_code == 303
    assert SealedLetter.objects.get().opens_on == OPENS_ON


@pytest.mark.django_db
def test_a_letter_finished_before_sealing_existed_stays_open_until_the_section_is_finished_again(participant):
    """✨ Nothing before ticket 104 told a participant their letter was sealed, so one finished then carries no seal."""
    Response.objects.update(completed_sections={"onboarding": SEALED_AT.isoformat(), "letter": SEALED_AT.isoformat()})

    assert LETTER in on(participant, SEALED_AT, shown)

    on(participant, SEALED_AT, reopen)
    assert on(participant, SEALED_AT, seal).status_code == 303
    assert LETTER not in on(participant, SEALED_AT, shown)


# Opening


@pytest.mark.django_db
def test_the_letter_opens_in_place_on_its_date_and_its_first_opening_is_stored(sealed):
    day_before = on(sealed, at(OPENS_ON - timedelta(days=1)), shown)
    assert LETTER not in day_before
    assert opened_at() is None

    assert LETTER in on(sealed, at(OPENS_ON, 9), shown)
    on(sealed, at(OPENS_ON + timedelta(days=1)), shown)
    assert opened_at() == at(OPENS_ON, 9)


# The email


@pytest.mark.django_db
def test_on_its_date_one_email_tells_the_participant_their_letter_is_ready_without_carrying_it(sealed):
    [sent] = run_on(OPENS_ON)

    assert sent.to == [ADDRESS]
    everything = sent.body + "".join(content for content, _ in sent.alternatives)
    assert LETTER not in everything
    [link] = [word for word in sent.body.split() if word.startswith("http")]
    assert urlsplit(link).path == "/accounts/login/"
    assert parse_qs(urlsplit(link).query)["next"] == [SECTION]
    assert run_on(OPENS_ON, hour=12) == [] and run_on(OPENS_ON + timedelta(days=1)) == []


@pytest.mark.django_db
def test_on_its_date_the_email_goes_even_if_the_letter_was_opened_that_day(sealed):
    on(sealed, at(OPENS_ON, 8), shown)

    assert len(run_on(OPENS_ON, hour=9)) == 1


def consent_withdrawn_on_the_day(client):
    on(client, at(OPENS_ON - timedelta(days=1)), withdraw_consent)
    assert run_on(OPENS_ON) == []
    on(client, at(OPENS_ON + timedelta(days=2), 8), give_consent)


def job_not_run_on_the_day(client):
    pass


@pytest.mark.django_db
@pytest.mark.parametrize("missed", [consent_withdrawn_on_the_day, job_not_run_on_the_day], ids=["consent", "job off"])
@pytest.mark.parametrize("opened", [False, True], ids=["unopened", "opened"])
def test_an_email_missed_on_the_day_goes_later_only_if_the_letter_has_not_been_opened_since(sealed, missed, opened):
    missed(sealed)
    if opened:
        on(sealed, at(OPENS_ON + timedelta(days=2), 9), shown)

    assert len(run_on(OPENS_ON + timedelta(days=3))) == (0 if opened else 1)


def sending_fails_once(monkeypatch):
    delivering = locmem.EmailBackend.send_messages
    failed = []

    def fails_the_first_time(backend, messages):
        if not failed:
            failed.append(True)
            raise ConnectionError("the mail server is down")
        return delivering(backend, messages)

    monkeypatch.setattr(locmem.EmailBackend, "send_messages", fails_the_first_time)
    return 1


def at_an_example_domain(monkeypatch):
    get_user_model().objects.update(email="sam@mail.example.org")
    return 0


@pytest.mark.django_db
@pytest.mark.parametrize("setback", [sending_fails_once, at_an_example_domain], ids=["sending fails", "example domain"])
def test_a_failed_email_goes_on_the_next_run_and_none_goes_to_an_example_domain(sealed, monkeypatch, setback):
    sent_next_day = setback(monkeypatch)

    assert run_on(OPENS_ON) == []
    assert len(run_on(OPENS_ON + timedelta(days=1))) == sent_next_day
