# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ Telling a participant, by email to their own address, that their sealed letter is ready to open (ticket 104).

The `send_letter_emails` command runs `send_ready_letters` once a day. The email never carries the letter.
"""

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from access.consent import withdrawn_participants
from engine.document.blocks import blocks_of, section_of
from engine.document.letter import ready_email
from engine.models import SealedLetter
from engine.reminders import at_example_domain

logger = logging.getLogger(__name__)


def send_ready_letters():
    """✨ Send every email saying a letter is ready that is due now, and return how many were sent.

    One is due once the letter's date has come, while the participant's consent stands, and never twice: on the date
    itself whatever else has happened, even if the letter was opened that day; after it, only if the letter has not
    been opened since, as when consent was withdrawn on the date or the job was not run then.

    Each is claimed by one UPDATE before it is sent, so of two runs at once only one sends it, and released if sending
    fails, so the next run tries again. Addresses at reserved example domains are passed over."""
    today = timezone.localdate()
    due = (
        SealedLetter.objects.exclude(response__participant__in=withdrawn_participants())
        .select_related("response__participant", "response__version")
        .filter(ready_email_sent_at__isnull=True, opens_on__lte=today)
        .filter(Q(opens_on=today) | Q(opened_at__isnull=True))
        .order_by("pk")
    )
    sent = 0
    for letter in due:
        address = letter.response.participant.email
        if not address or at_example_domain(address):
            continue
        claimed_at = timezone.now()
        if not _claim(letter, claimed_at):
            continue
        try:
            _email(letter, address).send()
        except Exception as failure:  # ✨ any failure to send, whichever backend: released, and tried again next run
            SealedLetter.objects.filter(pk=letter.pk, ready_email_sent_at=claimed_at).update(ready_email_sent_at=None)
            logger.error("A letter's email could not be sent and will be tried again: %s", type(failure).__name__)
            continue
        sent += 1
    return sent


def _claim(letter, claimed_at):
    return (
        SealedLetter.objects.filter(pk=letter.pk, ready_email_sent_at__isnull=True).update(
            ready_email_sent_at=claimed_at
        )
        == 1
    )


def _email(letter, address):
    """✨ The email, as plain text and HTML: the document's wording and a link to the letter's page through sign-in."""
    document = letter.response.version.document
    block = next(block for block in blocks_of(document) if block["id"] == letter.block_id)
    wording = ready_email(block)
    page = reverse("section", args=[section_of(document, letter.block_id)["id"]])
    link = f"{settings.ANVILLE_SITE_URL}{reverse('account_login')}?{urlencode({'next': page})}"
    email = EmailMultiAlternatives(
        subject=wording["subject"],
        body=f"{wording['body']}\n\n{wording['link_label']}:\n{link}\n",
        to=[address],
    )
    email.attach_alternative(render_to_string("engine/letter_ready_email.html", {**wording, "link": link}), "text/html")
    return email
