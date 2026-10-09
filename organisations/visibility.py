from django.db.models import Count, Exists, OuterRef, Q

from access.consent import current_consent
from organisations.models import Group, Organisation, Permission

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


def administered(viewer):
    """✨ The organisations `viewer` holds any permission in, by name, each as `(organisation, groups)`: the groups
    the permission reaches, all of them for one on the organisation and only its own for one on a group. Each
    organisation carries `manages`, whether the viewer holds `manage` on it, which is what creating a group needs.
    Each group carries `member_count`, and `manages`, whether the viewer holds `manage` on it or its organisation,
    which is what copying and replacing its join link need."""
    held = Permission.objects.filter(holder=viewer)
    on_group = held.filter(Q(group=OuterRef("pk")) | Q(organisation=OuterRef("organisation")))
    groups = (
        Group.objects.filter(Exists(on_group))
        .annotate(
            member_count=Count("memberships"),
            manages=Exists(on_group.filter(capability=Permission.Capability.MANAGE)),
        )
        .order_by("name")
    )
    organisations = (
        Organisation.objects.filter(Q(permissions__holder=viewer) | Q(groups__permissions__holder=viewer))
        .annotate(
            manages=Exists(held.filter(organisation=OuterRef("pk"), capability=Permission.Capability.MANAGE))
        )
        .distinct()
        .order_by("name")
    )
    return [
        (organisation, [group for group in groups if group.organisation_id == organisation.pk])
        for organisation in organisations
    ]


def manages_organisation(viewer, organisation):
    """✨ Whether `viewer` holds `manage` on `organisation`, so may create groups in it."""
    return Permission.objects.filter(
        holder=viewer, capability=Permission.Capability.MANAGE, organisation=organisation
    ).exists()


def manages_group(viewer, group):
    """✨ Whether `viewer` holds `manage` on `group` or its organisation, so may copy and replace its join link."""
    return (
        Permission.objects.filter(holder=viewer, capability=Permission.Capability.MANAGE)
        .filter(Q(group=group) | Q(organisation=group.organisation_id))
        .exists()
    )
