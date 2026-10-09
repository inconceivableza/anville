"""✨ Whether one account may see something of a participant: progress only, only with the participant's current
consent, and only through a permission on a group they are a member of or on that group's organisation (ADR 0012).
"""

import pytest

from access.consent import current_text_version, withdraw
from access.models import Consent
from organisations.models import Group, Membership, Organisation, Permission
from organisations.visibility import PROGRESS, can_see


def person(django_user_model, name):
    return django_user_model.objects.create_user(username=name, email=f"{name}@example.com")


def consented(django_user_model, name):
    participant = person(django_user_model, name)
    Consent.objects.create(participant=participant, text_version=current_text_version())
    return participant


def group_in(organisation, name="Autumn cohort"):
    return Group.objects.create(organisation=organisation, name=name, type=Group.Type.COHORT)


@pytest.fixture
def church():
    return Organisation.objects.create(name="Example Church")


@pytest.fixture
def admin(django_user_model):
    return person(django_user_model, "admin")


@pytest.mark.django_db
@pytest.mark.parametrize("capability", [Permission.Capability.MANAGE, Permission.Capability.SEE_PROGRESS])
def test_an_organisation_admin_sees_members_of_a_group_made_after_their_permission(
    church, admin, django_user_model, capability
):
    Permission.objects.create(holder=admin, capability=capability, organisation=church)
    later_group = group_in(church)
    member = consented(django_user_model, "member")
    Membership.objects.create(participant=member, group=later_group)

    assert can_see(admin, member, PROGRESS) is True


@pytest.mark.django_db
def test_a_group_admin_sees_members_of_their_group_only(church, admin, django_user_model):
    theirs = group_in(church, "Autumn cohort")
    sibling = group_in(church, "Worship team")
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, group=theirs)
    in_theirs = consented(django_user_model, "in-theirs")
    in_sibling = consented(django_user_model, "in-sibling")
    Membership.objects.create(participant=in_theirs, group=theirs)
    Membership.objects.create(participant=in_sibling, group=sibling)

    assert can_see(admin, in_theirs, PROGRESS) is True
    assert can_see(admin, in_sibling, PROGRESS) is False


@pytest.mark.django_db
def test_no_permission_over_the_members_group_sees_nothing(church, admin, django_user_model):
    member = consented(django_user_model, "member")
    Membership.objects.create(participant=member, group=group_in(church))
    other_church = Organisation.objects.create(name="Other Church")
    outsider = person(django_user_model, "outsider")
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, organisation=other_church)

    assert can_see(outsider, member, PROGRESS) is False
    assert can_see(admin, member, PROGRESS) is False


@pytest.mark.django_db
def test_an_organisation_admin_does_not_see_a_participant_in_none_of_its_groups(church, admin, django_user_model):
    group_in(church)
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, organisation=church)
    not_a_member = consented(django_user_model, "not-a-member")

    assert can_see(admin, not_a_member, PROGRESS) is False


@pytest.mark.django_db
@pytest.mark.parametrize("consent", ["missing", "withdrawn", "outdated"])
def test_a_member_without_current_consent_is_not_seen(church, admin, django_user_model, monkeypatch, consent):
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, organisation=church)
    if consent == "missing":
        member = person(django_user_model, "member")
    else:
        member = consented(django_user_model, "member")
    Membership.objects.create(participant=member, group=group_in(church))
    if consent == "withdrawn":
        withdraw(member)
    if consent == "outdated":
        monkeypatch.setattr("access.consent.CONSENT_TEXT_VERSION", current_text_version() + 1)

    assert can_see(admin, member, PROGRESS) is False


@pytest.mark.django_db
@pytest.mark.parametrize("what", ["answers", "results"])
def test_nothing_but_progress_is_seen_even_by_an_organisation_admin(church, admin, django_user_model, what):
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, organisation=church)
    member = consented(django_user_model, "member")
    Membership.objects.create(participant=member, group=group_in(church))

    assert can_see(admin, member, what) is False
