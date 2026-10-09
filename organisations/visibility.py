from datetime import datetime
from typing import NamedTuple

from django.db.models import Count, Exists, OuterRef, Q

from access.consent import current_consents
from access.models import name_shown_for
from engine.hub import complete_sections, track_sections
from engine.models import Response
from organisations.models import Group, Membership, Organisation, Permission

# ✨ The only thing an organisation or group admin may see of a member.
PROGRESS = "progress"


def _memberships_seen_by(viewer):
    """✨ `can_see`'s rule, as one query that both it and `members_seen_by` read: the memberships of groups on which
    `viewer` holds a permission that sees progress, on the group or on its organisation. Each carries `consented`,
    whether its member holds current consent, without which nothing of them but their name is seen."""
    sees_progress = Permission.objects.filter(
        # ✨ Named rather than left out, so a capability added later sees no progress until it is listed here.
        holder=viewer,
        capability__in=[Permission.Capability.MANAGE, Permission.Capability.SEE_PROGRESS],
    ).filter(Q(group=OuterRef("group")) | Q(organisation=OuterRef("group__organisation")))
    return Membership.objects.filter(Exists(sees_progress)).annotate(
        consented=Exists(current_consents().filter(participant=OuterRef("participant")))
    )


def can_see(viewer, participant, what):
    """✨ Whether `viewer` may see `what` of `participant`: progress only, while the participant holds current consent,
    and only through a permission on a group they are a member of, or on that group's organisation. Someone signed
    out sees nothing."""
    if what != PROGRESS or not viewer.is_authenticated:
        return False
    return _memberships_seen_by(viewer).filter(participant=participant, consented=True).exists()


class MemberProgress(NamedTuple):
    """✨ One member as an admin sees them. Without consent, only `name`. With it, `complete` of `total` sections of
    their track and the time `last_active`, all None while they have no response, which is not started."""

    name: str
    consented: bool
    complete: int | None = None
    total: int | None = None
    last_active: datetime | None = None


def members_seen_by(viewer, group):
    """✨ `can_see`'s companion for a whole group: each of its members `viewer` may see, by name, as `MemberProgress`.
    The members and whether each has consented come from `can_see`'s own query, so a member is shown progress exactly
    when `can_see` would say so. A viewer with no right over the group gets nobody."""
    if not viewer.is_authenticated:
        return []
    memberships = list(_memberships_seen_by(viewer).filter(group=group).select_related("participant__account"))
    consented = [membership.participant_id for membership in memberships if membership.consented]
    # ✨ Ordered by pk, so each participant is left with their latest response, the one `Response.in_progress` reads.
    responses = {
        response.participant_id: response
        for response in Response.objects.filter(participant__in=consented).select_related("version").order_by("pk")
    }
    members = [
        _progress(membership, responses.get(membership.participant_id))
        if membership.consented
        else MemberProgress(name_shown_for(membership.participant), consented=False)
        for membership in memberships
    ]
    return sorted(members, key=lambda member: member.name.casefold())


def _progress(membership, response):
    """✨ How far a consenting member is through their track, counted as the hub counts complete sections."""
    name = name_shown_for(membership.participant)
    if response is None:
        return MemberProgress(name, consented=True)
    sections = track_sections(response.version.document)
    done = complete_sections(sections, response.answers_with_contacts_and_visits(), response.completed_sections)
    return MemberProgress(
        name,
        consented=True,
        complete=sum(1 for section in sections if section["id"] in done),
        total=len(sections),
        last_active=response.updated_at,
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
