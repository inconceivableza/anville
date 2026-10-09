# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

import re
from html import escape

from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailAlternative

# ✨ What the subject of every message from a test system starts with.
SUBJECT_MARK = "[TEST]"

BODY_TAG = re.compile(r"<body[^>]*>", re.IGNORECASE)


class DisclaimerBackend(BaseEmailBackend):
    """✨ Marks every outgoing message as coming from a test system, then hands it to the real backend.

    A staging environment that sends actual email reaches real mailboxes, and whoever opens a message must be able to
    see that it is not from the real service. The disclaimer is added here, where mail leaves, so that it covers every
    message whichever code sent it, allauth's included, and no template has to remember it.

    Settings turn this on by setting ANVILLE_EMAIL_DISCLAIMER, and keep the backend it wraps in
    ANVILLE_DISCLAIMED_EMAIL_BACKEND.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.delivering = get_connection(
            settings.ANVILLE_DISCLAIMED_EMAIL_BACKEND, fail_silently=fail_silently, **kwargs
        )

    def open(self):
        return self.delivering.open()

    def close(self):
        return self.delivering.close()

    def send_messages(self, email_messages):
        for message in email_messages:
            add_disclaimer(message, settings.ANVILLE_EMAIL_DISCLAIMER)
        return self.delivering.send_messages(email_messages)


def add_disclaimer(message, disclaimer):
    """✨ Put the mark on the subject and the disclaimer at the top of the body, in its text and its HTML alike.

    A message already marked is left alone, so one that is sent again is not marked twice.
    """
    if message.subject.startswith(SUBJECT_MARK):
        return
    message.subject = f"{SUBJECT_MARK} {message.subject}"
    if message.content_subtype == "html":
        message.body = _with_html_disclaimer(message.body, disclaimer)
    else:
        message.body = f"{disclaimer}\n\n{message.body}"
    alternatives = getattr(message, "alternatives", None)
    if alternatives:
        message.alternatives = [
            EmailAlternative(_with_html_disclaimer(content, disclaimer) if mimetype == "text/html" else content, mimetype)
            for content, mimetype in alternatives
        ]


def _with_html_disclaimer(html, disclaimer):
    notice = f"<p><strong>{escape(disclaimer)}</strong></p>"
    body = BODY_TAG.search(html)
    if body is None:
        return notice + html
    return html[: body.end()] + notice + html[body.end() :]
