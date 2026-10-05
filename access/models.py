from django.conf import settings
from django.db import models
from django.utils import timezone


DISPLAY_NAME_MAX_LENGTH = 150  # ✨ as long as a contact's name, the other names a participant types


class Account(models.Model):
    """✨ What Anville keeps about a participant beyond Django's own user: the name they gave at sign-up (ticket 37).

    It names them to their observers and coach and on their own results. It need not be unique, and nothing finds a
    participant by it. Accounts made before display names existed have none, and are named from their email.
    """

    participant = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account")
    display_name = models.CharField(max_length=DISPLAY_NAME_MAX_LENGTH)

    def __str__(self):
        return self.display_name


def name_shown_for(participant):
    """✨ The name a participant is shown by: their display name, else the part of their email before the @. Never their
    username, which is their whole email for new accounts, unless an account has no email (one made with
    `createsuperuser`), so that an observer is never asked to answer for a blank."""
    account = getattr(participant, "account", None)
    if account:
        return account.display_name
    return participant.email.partition("@")[0] or participant.get_username()


class Consent(models.Model):
    """✨ A participant's explicit consent to one version of the consent text (ADR 0004).

    Each consent is its own row, so a new version of the text is consented to afresh and the earlier
    consent stays on record. Declining leaves no row at all: declining stores nothing beyond the account.
    """

    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consents")
    text_version = models.PositiveIntegerField()
    given_at = models.DateTimeField(default=timezone.now)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Consent to version {self.text_version} by {self.participant}"
