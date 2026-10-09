from django.db.models import Q

from access.consent import current_consent
from organisations.models import Permission

# ✨ The only thing an organisation or group admin may see of a member.
PROGRESS = "progress"


def can_see(viewer, participant, what):
    """✨ Whether `viewer` may see `what` of `participant`: progress only, while the participant holds current consent,
    and only through a permission on a group they are a member of, or on that group's organisation. Someone signed
    out sees nothing."""
    if what != PROGRESS or not viewer.is_authenticated or current_consent(participant) is None:
        return False
    return (
        Permission.objects.filter(
            # ✨ Named rather than left out, so a capability added later sees no progress until it is listed here.
            holder=viewer,
            capability__in=[Permission.Capability.MANAGE, Permission.Capability.SEE_PROGRESS],
        )
        .filter(
            Q(group__memberships__participant=participant)
            | Q(organisation__groups__memberships__participant=participant)
        )
        .exists()
    )
