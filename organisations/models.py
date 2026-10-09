import secrets

from django.conf import settings
from django.db import models


def new_join_token():
    """✨ The secret in a group's join link. Kept as it is, not hashed, so the link can be copied again."""
    return secrets.token_urlsafe(32)


class Organisation(models.Model):
    """✨ A church or ministry that gathers participants into groups within a deployment (ADR 0012). Not a tenant."""

    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Group(models.Model):
    """✨ A set of participants gathered within an organisation. Its type is a label only: nothing behaves differently
    for a cohort or a team."""

    class Type(models.TextChoices):
        COHORT = "cohort", "Cohort"
        TEAM = "team", "Team"

    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=16, choices=Type.choices)
    join_token = models.CharField(max_length=64, unique=True, default=new_join_token, editable=False)

    def __str__(self):
        return f"{self.name} ({self.organisation})"


class Membership(models.Model):
    """✨ A participant's place in a group. Belonging to an organisation is derived from its groups; leaving deletes the
    row."""

    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["participant", "group"], name="one_membership_per_participant_per_group"),
        ]

    def __str__(self):
        return f"{self.participant} in {self.group}"


class Permission(models.Model):
    """✨ A right the operator grants an account over an organisation, and so all its groups including later ones, or
    over one group. Either capability lets its holder see members' progress (`organisations.visibility`). Observers and
    coaches have no account, so hold none.

    Not Django's own `auth.Permission`, which is about editing models in the admin.
    """

    class Capability(models.TextChoices):
        MANAGE = "manage", "Manage"
        SEE_PROGRESS = "see_progress", "See progress"

    holder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organisation_permissions"
    )
    capability = models.CharField(max_length=16, choices=Capability.choices)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, null=True, blank=True, related_name="permissions"
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name="permissions")

    class Meta:
        constraints = [
            # ✨ Two keys rather than a scope type and id, so the database keeps referential integrity; the scope type is
            # whichever is set.
            models.CheckConstraint(
                condition=models.Q(organisation__isnull=False, group__isnull=True)
                | models.Q(organisation__isnull=True, group__isnull=False),
                name="a_permission_names_an_organisation_or_a_group",
            ),
        ]

    def __str__(self):
        return f"{self.get_capability_display()} on {self.organisation or self.group} for {self.holder}"
