"""✨ "Your groups": a participant sees each group they are in and what its admins see, and can leave any of them."""

import re

import pytest

from access.models import Account
from organisations.models import Group, Membership, Organisation, Permission
from organisations.visibility import PROGRESS, can_see
from tests.journeys.pages import main_of, text_of
from tests.documents import pathway_document
from tests.journeys.test_consent import answer, give_consent

YOUR_GROUPS = "/groups/"
WHAT_ADMINS_SEE = (
    "Its admins, and its organisation's admins, see your first name, how far through you are and when you were last "
    "active, and the self-assessment results of the whole group averaged, once at least three members have them, "
    "never yours on their own. They never see your answers. If you leave the group, they no longer see anything "
    "about you through it."
)


def a_group(organisation_name, group_name, group_type=Group.Type.COHORT):
    organisation, _ = Organisation.objects.get_or_create(name=organisation_name)
    return Group.objects.create(organisation=organisation, name=group_name, type=group_type)


def an_admin_of(group, django_user_model, display_name):
    admin = django_user_model.objects.create_user(username=display_name, email=f"{display_name}@example.com")
    Account.objects.create(participant=admin, display_name=display_name)
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, group=group)
    return admin


@pytest.fixture
def participant(client, django_user_model):
    """✨ A signed-in participant who has consented and is in no group yet."""
    person = django_user_model.objects.create_user(username="participant", email="participant@example.com")
    client.force_login(person)
    give_consent(client)
    return person


@pytest.mark.django_db
def test_the_hub_links_your_groups_at_its_foot_beside_your_consent(client, participant):
    hub = main_of(client.get("/hub/").content.decode())

    foot = re.search(r'<p[^>]*>(?:(?!</p>).)*href="/consent/".*?</p>', hub, re.S).group(0)
    assert re.search(rf'<a href="{YOUR_GROUPS}">Your groups</a>', foot)


@pytest.mark.django_db
def test_each_group_is_listed_with_its_organisation_and_what_its_admins_see_but_not_their_names(
    client, participant, django_user_model
):
    cohort = a_group("Example Church", "Autumn cohort")
    team = a_group("Example Mission", "Worship team", Group.Type.TEAM)
    for group in (cohort, team):
        Membership.objects.create(participant=participant, group=group)
    an_admin_of(cohort, django_user_model, "Bartholomew")
    organisation_admin = an_admin_of(team, django_user_model, "Philippa")
    Permission.objects.create(
        holder=organisation_admin, capability=Permission.Capability.SEE_PROGRESS, organisation=team.organisation
    )

    page = text_of(main_of(client.get(YOUR_GROUPS).content.decode()))

    assert "Autumn cohort" in page and "Example Church" in page
    assert "Worship team" in page and "Example Mission" in page
    assert page.count(WHAT_ADMINS_SEE) == 2
    assert "Bartholomew" not in page and "Philippa" not in page


def hub_progress(client):
    return re.search(r"\d+ of \d+ answered", client.get("/hub/").content.decode()).group(0)


@pytest.mark.django_db
def test_leaving_asks_for_confirmation_then_ends_the_membership_and_keeps_the_answers(client, participant, load_pathway):
    load_pathway(pathway_document())
    answer(client, "baseline-bible", "7")
    progress_before = hub_progress(client)
    cohort = a_group("Example Church", "Autumn cohort")
    Membership.objects.create(participant=participant, group=cohort)
    leave = f"/groups/{cohort.pk}/leave/"
    assert f'href="{leave}"' in client.get(YOUR_GROUPS).content.decode()

    confirmation = client.get(leave).content.decode()

    assert "Autumn cohort" in text_of(main_of(confirmation))
    assert f'<form method="post" action="{leave}"' in confirmation
    assert "Autumn cohort" in text_of(main_of(client.get(YOUR_GROUPS).content.decode()))

    left = client.post(leave)

    assert left.status_code == 303 and left.url == YOUR_GROUPS
    assert "Autumn cohort" not in text_of(main_of(client.get(YOUR_GROUPS).content.decode()))
    assert progress_before.startswith("1 of ")
    assert hub_progress(client) == progress_before


@pytest.mark.django_db
def test_after_leaving_the_groups_admin_can_no_longer_see_the_participants_progress(
    client, participant, django_user_model
):
    cohort = a_group("Example Church", "Autumn cohort")
    Membership.objects.create(participant=participant, group=cohort)
    admin = an_admin_of(cohort, django_user_model, "Bartholomew")
    assert can_see(admin, participant, PROGRESS) is True

    client.post(f"/groups/{cohort.pk}/leave/")

    assert can_see(admin, participant, PROGRESS) is False
