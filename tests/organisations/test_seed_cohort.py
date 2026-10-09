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

from access.consent import current_consent
from engine.hub import COMPLETE, hub_for, section_by_id, track_sections
from engine.models import Invitation, ObserverResponse, Publication, Response
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


def how_far(member):
    """✨ Where a member has got to, by the hub's own count of complete sections."""
    response = Response.in_progress(member)
    if response is None:
        return "not started"
    hub = hub_for(
        track_sections(response.version.document),
        response.answers_with_contacts_and_visits(),
        response.completed_sections,
        moved_past=response.moved_past_by_section(),
    )
    complete = sum(1 for section in hub.sections if section.status == COMPLETE)
    if complete == 0:
        return "not started"
    return "finished" if complete == len(hub.sections) else "part-way"


@pytest.mark.django_db
def test_members_are_spread_across_the_pathway_and_exactly_one_has_no_current_consent(seeded):
    members = [membership.participant for membership in Group.objects.get().memberships.all()]
    finished = [Response.in_progress(member) for member in members if how_far(member) == "finished"]
    closing_ratings = [
        block["id"]
        for block in section_by_id(Publication.current_version().document, "letter")["blocks"]
        if block["type"] == "agreement_scale"
    ]

    assert {how_far(member) for member in members} == {"not started", "part-way", "finished"}
    for response in finished:
        assert response.results.exists()
        assert Invitation.objects.filter(contact__response=response, claimed_at__isnull=False).count() >= 3
        assert response.observer_responses.filter(submitted_at__isnull=False).count() >= 3
        assert all(response.answers.get(block_id) for block_id in closing_ratings)
    assert sum(current_consent(member) is None for member in members) == 1


@pytest.mark.django_db
def test_every_account_is_at_example_com_and_every_response_is_test_data(seeded):
    assert all(email.endswith("@example.com") for email in get_user_model().objects.values_list("email", flat=True))
    assert Response.objects.exists() and not Response.objects.filter(is_test_data=False).exists()
    assert ObserverResponse.objects.exists() and not ObserverResponse.objects.filter(is_test_data=False).exists()


@pytest.mark.django_db
def test_a_second_run_says_example_church_exists_and_adds_nothing(seeded):
    accounts, responses = get_user_model().objects.count(), Response.objects.count()

    out = seed()

    assert "Example Church already exists" in out
    assert Organisation.objects.count() == 1
    assert Group.objects.count() == 1
    assert (get_user_model().objects.count(), Response.objects.count()) == (accounts, responses)
