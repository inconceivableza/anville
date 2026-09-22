from django.db import models


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
