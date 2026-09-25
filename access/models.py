from django.conf import settings
from django.db import models
from django.utils import timezone


class Consent(models.Model):
    """✨ A participant's explicit agreement to one version of the consent text (ADR 0004).

    Each agreement is its own row, so a new version of the text is agreed to afresh and the earlier
    agreement stays on record. Declining leaves no row at all: declining stores nothing beyond the account.
    """

    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consents")
    text_version = models.PositiveIntegerField()
    given_at = models.DateTimeField(default=timezone.now)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Consent to version {self.text_version} by {self.participant}"
