"""✨ `seed_cohort` gives a developer Example Church, an Autumn cohort of twelve fake members spread across the pathway,
and an organisation admin to sign in as, all marked as test data.
"""

import re
from io import StringIO
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import Client

from organisations.models import Group, Organisation, Permission

DOCUMENT = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do.json"


def seed():
    out = StringIO()
    call_command("seed_cohort", stdout=out)
    return out.getvalue()


@pytest.fixture
def published():
    call_command("load_pathway", str(DOCUMENT), stdout=StringIO())


@pytest.fixture
def seeded(published, settings):
    """✨ The command's output, once it has run against the Whatever You Do pathway."""
    settings.DEBUG = True
    return seed()


@pytest.mark.django_db
def test_it_refuses_unless_debug_is_on_and_creates_nothing(published, settings):
    settings.DEBUG = False

    with pytest.raises(CommandError, match="DEBUG"):
        seed()

    assert not Organisation.objects.exists()
    assert not get_user_model().objects.exists()


@pytest.mark.django_db
def test_it_refuses_without_a_published_pathway(settings):
    settings.DEBUG = True

    with pytest.raises(CommandError, match="No pathway is published"):
        seed()

    assert not Organisation.objects.exists()


@pytest.mark.django_db
def test_it_creates_example_church_an_autumn_cohort_of_twelve_and_an_organisation_admin(seeded):
    church = Organisation.objects.get()
    cohort = Group.objects.get()
    admin = Permission.objects.get()

    assert church.name == "Example Church"
    assert (cohort.organisation, cohort.name, cohort.type) == (church, "Autumn cohort", Group.Type.COHORT)
    assert cohort.memberships.count() == 12
    assert (admin.capability, admin.organisation, admin.group) == (Permission.Capability.MANAGE, church, None)


@pytest.mark.django_db
def test_it_prints_the_admins_email_a_password_that_signs_in_and_the_cohorts_join_link(seeded):
    admin = Permission.objects.get().holder
    password = re.search(r"^Password: (\S+)$", seeded, re.MULTILINE).group(1)

    assert admin.email in seeded
    assert Client().login(username=admin.email, password=password)
    assert f"/join/{Group.objects.get().join_token}/" in seeded
