# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ Reminding observers who have not sent, once a week while their link works, and stopping it (ticket 43a, ADR 0016).

The `send_reminders` command runs `send_due_reminders` once a day. Nothing here is shown to the participant.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import dateformat, timezone

from access.consent import withdrawn_participants
from access.models import name_shown_for
from engine.document.letter import SHOWN_DATE
from engine.document.observers import reminder_email
from engine.models import Contact, Invitation

logger = logging.getLogger(__name__)

WEEK = timedelta(days=7)

# ✨ Reserved for examples and testing (RFC 2606, RFC 6761), so nobody receives mail there: staging's fake people
# use them, and reminding them would only bounce.
EXAMPLE_DOMAINS = ("example.com", "example.net", "example.org")
RESERVED_TOP_LEVEL = ("example", "test", "invalid", "localhost")

STOP_SALT = "engine.reminders.stop"
ANSWER_SALT = "engine.reminders.answer"


def send_due_reminders():
    """✨ Send every reminder that is due now, and return how many were sent.

    One is due to a person who has not sent, has not stopped reminders and is not a coach, while their link works, the
    participant's consent stands and answer collection is open, once a whole week of the link's own clock has passed
    since the week last reminded for. Only one goes however many weeks were missed, as after an unfreeze.

    Each is claimed by one UPDATE of the week before it is sent, so of two runs at once only one sends it, and released
    if sending fails, so the next run tries again. Addresses at reserved example domains are passed over."""
    now = timezone.now()
    candidates = (
        Invitation.objects.exclude(contact__response__participant__in=withdrawn_participants())
        .select_related("contact__response__participant", "contact__response__version")
        .filter(
            contact__role=Contact.Role.CONTACT,
            contact__sent_at__isnull=True,
            contact__reminders_stopped_at__isnull=True,
            contact__response__collection_frozen_at__isnull=True,
            expires_at__gt=now,
            issued_at__lte=now - WEEK,
        )
        .order_by("pk")
    )
    sent = 0
    for invitation in candidates:
        week = (now - invitation.issued_at) // WEEK
        if week <= invitation.reminded_week or at_example_domain(invitation.contact.email):
            continue
        if not _claim(invitation, week):
            continue
        try:
            _reminder(invitation).send()
        except Exception as failure:  # ✨ any failure to send, whichever backend: released, and tried again next run
            _release(invitation, week)
            logger.error("A reminder could not be sent and will be tried again: %s", type(failure).__name__)
            continue
        sent += 1
    return sent


def _claim(invitation, week):
    """✨ Take the reminder for `week` on this link, unless another run took it first, the link was reissued, or the
    person sent or stopped reminders meanwhile."""
    return (
        Invitation.objects.filter(
            pk=invitation.pk,
            reminded_week=invitation.reminded_week,
            contact__sent_at__isnull=True,
            contact__reminders_stopped_at__isnull=True,
        ).update(reminded_week=week)
        == 1
    )


def _release(invitation, week):
    Invitation.objects.filter(pk=invitation.pk, reminded_week=week).update(reminded_week=invitation.reminded_week)


def at_example_domain(address):
    """✨ Whether an address is at a reserved example domain, which no mail is sent to (the letter's email too)."""
    domain = address.rpartition("@")[2].lower().rstrip(".")
    return (
        domain.rpartition(".")[2] in RESERVED_TOP_LEVEL
        or domain in EXAMPLE_DOMAINS
        or domain.endswith(tuple(f".{example}" for example in EXAMPLE_DOMAINS))
    )


def _reminder(invitation):
    """✨ The email for one reminder, as plain text and HTML: the document's wording, naming the participant and the day
    the link stops working, the button for a fresh link and the link to its privacy notice (ticket 43b), and the way to
    stop as a link and as `List-Unsubscribe` headers with one-click POST (RFC 8058)."""
    contact = invitation.contact
    participant_response = contact.response
    until = dateformat.format(timezone.localtime(invitation.expires_at), SHOWN_DATE)
    wording = reminder_email(
        participant_response.version.document, name_shown_for(participant_response.participant), contact.name, until
    )
    stop = stop_link(contact)
    answer = answer_link(invitation)
    reminder = EmailMultiAlternatives(
        subject=wording["subject"],
        body=f"{wording['body']}\n\n{wording['answer']}\n{answer}\n\n{wording['stop']}:\n{stop}\n",
        to=[contact.email],
        headers={"List-Unsubscribe": f"<{stop}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"},
    )
    html = render_to_string("engine/reminder_email.html", {**wording, "answer_link": answer, "stop_link": stop})
    reminder.attach_alternative(html, "text/html")
    return reminder


def answer_link(invitation):
    """✨ The address of a reminder's button (ticket 43b): a page with the privacy notice and a button that gives the
    observer a fresh link of their own. Signed with a salt of its own, so it is no stop address, and naming this
    invitation, so a reissue, which makes a new one, leaves it naming nothing. It never expires of itself."""
    signed = signing.Signer(salt=ANSWER_SALT).sign(str(invitation.pk))
    return settings.ANVILLE_SITE_URL + reverse("fresh_link", args=[signed])


def invitation_to_answer(signed):
    """✨ The id of the invitation a button's address was made for, or None if it was tampered with."""
    try:
        return int(signing.Signer(salt=ANSWER_SALT).unsign(signed))
    except signing.BadSignature:
        return None


def stop_link(contact):
    """✨ The address that stops this participant's reminders to this person, signed so it cannot be made for anyone
    else's. It never expires: it works while the contact exists, whatever has happened to their link."""
    signed = signing.Signer(salt=STOP_SALT).sign(str(contact.pk))
    return settings.ANVILLE_SITE_URL + reverse("stop_reminders", args=[signed])


def contact_to_stop(signed):
    """✨ The contact a stop address was made for, or None if it was tampered with or the contact has been removed."""
    try:
        pk = signing.Signer(salt=STOP_SALT).unsign(signed)
    except signing.BadSignature:
        return None
    return Contact.objects.select_related("response__participant").filter(pk=pk, role=Contact.Role.CONTACT).first()


def stop_reminders(contact):
    """✨ Stop this participant's reminders to this person. Stopping again keeps the first time; nothing undoes it."""
    Contact.objects.filter(pk=contact.pk, reminders_stopped_at__isnull=True).update(reminders_stopped_at=timezone.now())
