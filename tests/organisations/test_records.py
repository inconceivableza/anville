"""✨ What the database itself refuses: a permission names exactly one of an organisation or a group, and a participant
joins each group only once, though they may be in groups of several organisations (ADR 0012).
"""

import pytest
from django.db import IntegrityError

from organisations.models import Group, Membership, Organisation, Permission


@pytest.fixture
def church():
    return Organisation.objects.create(name="Example Church")


@pytest.fixture
def cohort(church):
    return Group.objects.create(organisation=church, name="Autumn cohort", type=Group.Type.COHORT)


@pytest.fixture
def someone(django_user_model):
    return django_user_model.objects.create_user(username="someone", email="someone@example.com")


@pytest.mark.django_db
@pytest.mark.parametrize("scope", ["both", "neither"])
def test_a_permission_names_exactly_one_of_an_organisation_or_a_group(church, cohort, someone, scope):
    names = {"organisation": church, "group": cohort} if scope == "both" else {}

    with pytest.raises(IntegrityError):
        Permission.objects.create(holder=someone, capability=Permission.Capability.MANAGE, **names)


@pytest.mark.django_db
def test_a_participant_joins_a_group_once_but_may_be_in_groups_of_several_organisations(cohort, someone):
    elsewhere = Organisation.objects.create(name="Other Church")
    team = Group.objects.create(organisation=elsewhere, name="Worship team", type=Group.Type.TEAM)
    Membership.objects.create(participant=someone, group=cohort)
    Membership.objects.create(participant=someone, group=team)

    with pytest.raises(IntegrityError):
        Membership.objects.create(participant=someone, group=cohort)
