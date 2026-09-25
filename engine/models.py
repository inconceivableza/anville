from django.conf import settings
from django.db import models, transaction
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
    # ✨ When each answer an author marked `fixed_once_complete` became fixed. Recorded, like completion, so that
    # reopening the section afterwards does not quietly make it changeable again.
    fixed_answers = models.JSONField(default=dict)
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
        cannot undo an answer saved to another block since. Nor can it change an answer fixed since: the
        same UPDATE skips a fixed answer, so a save that raced a completion writes nothing. Returns whether
        the answer was stored.
        """
        stored = (
            Response.objects.filter(pk=self.pk)
            .exclude(fixed_answers__has_key=block_id)
            .update(
                answers=_MergeJson(F("answers"), Value({block_id: value}, output_field=models.JSONField())),
                updated_at=timezone.now(),
            )
        )
        return stored == 1

    def submit_sort(self, block_id, sort, scores):
        """✨ Store a sort and the result scored from it together, or neither.

        A second sort for the same block raises IntegrityError from the database and changes nothing,
        since retake is not offered yet.
        """
        with transaction.atomic():
            Result.objects.create(response=self, block_id=block_id, scores=scores)
            self.save_answer(block_id, sort)

    def complete_section(self, section_id, fixed_block_ids=()):
        """✨ Record that the participant completed a section, and fix the answers to `fixed_block_ids`, in one UPDATE.

        The caller has already re-checked the section's gate. Completing twice is harmless: the second
        time replaces the completion timestamp and nothing else. An answer fixed before keeps the time it
        was first fixed, since the stored entries are kept over the new ones.
        """
        now = timezone.now()
        stamp = now.isoformat()
        Response.objects.filter(pk=self.pk).update(
            completed_sections=_MergeJson(
                F("completed_sections"), Value({section_id: stamp}, output_field=models.JSONField())
            ),
            fixed_answers=_MergeJson(
                Value({block_id: stamp for block_id in fixed_block_ids}, output_field=models.JSONField()), F("fixed_answers")
            ),
            updated_at=now,
        )

    def reopen_section(self, section_id):
        """✨ Take back the participant's own act of completing a section, leaving every answer as it is.

        Only this section's record goes: what they completed before or after it is theirs, and reopening
        one section never discards another. Reopening one that was never complete does nothing.
        """
        Response.objects.filter(pk=self.pk).update(
            completed_sections=_WithoutKey(F("completed_sections"), Value(section_id)),
            updated_at=timezone.now(),
        )


class Result(models.Model):
    """✨ The scores computed from one sort answer, kept against its response and so its pathway version.

    Computed once, when the sort is submitted, and never recomputed: a later version with different scoring
    leaves it alone. The scores carry the name of the method that produced them.
    """

    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="results")
    block_id = models.CharField(max_length=64)
    scores = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["response", "block_id"], name="one_result_per_sort_per_response"),
        ]


class _MergeJson(Func):
    """✨ PostgreSQL's jsonb `||`: the right-hand object's keys replace the left's, and every other key is kept."""

    arg_joiner = " || "
    template = "%(expressions)s"
    output_field = models.JSONField()


class _WithoutKey(Func):
    """✨ PostgreSQL's jsonb `-`: one key removed in a single UPDATE, every other key left as it was."""

    arg_joiner = " - "
    template = "%(expressions)s"
    output_field = models.JSONField()
