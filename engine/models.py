from django.conf import settings
from django.db import models
from django.db.models import F, Func, Value
from django.utils import timezone


class PathwayVersion(models.Model):
    """✨ An immutable snapshot of a pathway document. The database refuses any update to a stored row."""

    document = models.JSONField()
    content_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pathway version {self.pk} ({self.content_hash[:12]})"


class Publication(models.Model):
    """✨ A record that a pathway version became the published one. The latest publication is current.

    Publishing is appended rather than flagged, because a pathway version can never be updated.
    """

    version = models.ForeignKey(PathwayVersion, on_delete=models.PROTECT, related_name="publications")
    published_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def current_version(cls):
        latest = cls.objects.select_related("version").order_by("-pk").first()
        return latest.version if latest else None


class Response(models.Model):
    """✨ A participant's answers to one pathway version, keyed by block identifier.

    A participant stays on the version their response was started against, even after a later one is
    published. Whether a response is test or seed data is decided here on the server, never by a client.
    """

    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="responses")
    version = models.ForeignKey(PathwayVersion, on_delete=models.PROTECT, related_name="responses")
    answers = models.JSONField(default=dict)
    # ✨ When the participant said each section was finished. Completing is their own act, so it is recorded
    # rather than derived: an answer changed afterwards does not quietly undo it.
    completed_sections = models.JSONField(default=dict)
    is_test_data = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["participant", "version"], name="one_response_per_participant_per_version"),
        ]

    @classmethod
    def in_progress(cls, participant):
        return cls.objects.select_related("version").filter(participant=participant).order_by("-pk").first()

    def save_answer(self, block_id, value):
        """✨ Store one block's answer in a single UPDATE that merges it into the stored answers.

        The rest of the response is never re-serialised, so a save from a stale copy of this object
        cannot undo an answer saved to another block since.
        """
        self._merge(answers=Value({block_id: value}, output_field=models.JSONField()))

    def complete_section(self, section_id):
        """✨ Record that the participant completed a section, merged in the same way as an answer.

        The caller has already re-checked the section's gate. Completing twice is harmless: the second
        time replaces the timestamp and nothing else.
        """
        self._merge(completed_sections=Value({section_id: timezone.now().isoformat()}, output_field=models.JSONField()))

    def _merge(self, **fields):
        Response.objects.filter(pk=self.pk).update(
            **{name: _MergeJson(F(name), value) for name, value in fields.items()},
            updated_at=timezone.now(),
        )


class _MergeJson(Func):
    """✨ PostgreSQL's jsonb `||`: the right-hand object's keys replace the left's, and every other key is kept."""

    arg_joiner = " || "
    template = "%(expressions)s"
    output_field = models.JSONField()
