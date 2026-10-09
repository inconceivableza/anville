# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The disclaimer a test system puts on every email it sends (ticket 26, part 2).

Staging starts with fake email. Once it sends actual email, to the real addresses of people who know they are testing,
every message must say that it comes from a test system and is not intended for production use.
"""

import pytest
from django.core import mail
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mail

DISCLAIMER = "This message comes from a test system for Anville. It is not intended for production use."


@pytest.fixture
def a_test_system(settings):
    """✨ As ANVILLE_EMAIL_DISCLAIMER sets things, delivering to the outbox that tests read."""
    settings.ANVILLE_EMAIL_DISCLAIMER = DISCLAIMER
    settings.ANVILLE_DISCLAIMED_EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_BACKEND = "config.email.DisclaimerBackend"


def test_a_message_says_in_its_subject_and_first_lines_that_it_is_from_a_test_system(a_test_system):
    send_mail("Your coach's link", "Here is the link.", "hello@example.org", ["coach@example.com"])

    [sent] = mail.outbox
    assert sent.subject == "[TEST] Your coach's link"
    assert sent.body == f"{DISCLAIMER}\n\nHere is the link."
    assert sent.to == ["coach@example.com"]


def test_the_html_of_a_message_carries_the_disclaimer_too(a_test_system):
    message = EmailMultiAlternatives("Invitation", "Plain words.", "hello@example.org", ["observer@example.com"])
    message.attach_alternative('<html><body class="mail"><p>Fine words.</p></body></html>', "text/html")

    message.send()

    [sent] = mail.outbox
    [(html, mimetype)] = sent.alternatives
    assert mimetype == "text/html"
    assert html == f'<html><body class="mail"><p><strong>{DISCLAIMER}</strong></p><p>Fine words.</p></body></html>'
    assert sent.body == f"{DISCLAIMER}\n\nPlain words."


def test_a_message_that_is_only_html_carries_it_as_html(a_test_system):
    message = EmailMessage("Invitation", "<p>Fine words.</p>", "hello@example.org", ["observer@example.com"])
    message.content_subtype = "html"

    message.send()

    [sent] = mail.outbox
    assert sent.body == f"<p><strong>{DISCLAIMER}</strong></p><p>Fine words.</p>"


def test_a_disclaimer_with_markup_in_it_is_shown_as_written_in_html(a_test_system, settings):
    settings.ANVILLE_EMAIL_DISCLAIMER = "Test system <not for real use> & nothing else"
    message = EmailMultiAlternatives("Invitation", "Plain words.", "hello@example.org", ["observer@example.com"])
    message.attach_alternative("<p>Fine words.</p>", "text/html")

    message.send()

    [(html, _)] = mail.outbox[0].alternatives
    assert html.startswith("<p><strong>Test system &lt;not for real use&gt; &amp; nothing else</strong></p>")


def test_a_message_sent_again_is_not_marked_twice(a_test_system):
    message = EmailMessage("Reminder", "Do reply.", "hello@example.org", ["observer@example.com"])

    message.send()
    message.send()

    assert [sent.subject for sent in mail.outbox] == ["[TEST] Reminder", "[TEST] Reminder"]
    assert mail.outbox[1].body == f"{DISCLAIMER}\n\nDo reply."


def test_every_message_of_a_batch_is_marked(a_test_system):
    messages = [EmailMessage(f"Note {n}", "Words.", "hello@example.org", ["someone@example.com"]) for n in (1, 2, 3)]

    assert mail.get_connection().send_messages(messages) == 3

    assert [sent.subject for sent in mail.outbox] == ["[TEST] Note 1", "[TEST] Note 2", "[TEST] Note 3"]


def test_with_no_disclaimer_set_a_message_goes_as_written():
    send_mail("Your coach's link", "Here is the link.", "hello@example.org", ["coach@example.com"])

    [sent] = mail.outbox
    assert sent.subject == "Your coach's link"
    assert sent.body == "Here is the link."
