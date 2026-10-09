"""✨ Managing groups from "Your organisations": an organisation admin creates a group, and an admin replaces a group's
join link when it has travelled further than intended."""

import re

import pytest

from organisations.models import Group, Membership, Permission
from tests.journeys.pages import main_of, text_of
from tests.journeys.test_your_groups import a_group
from tests.journeys.test_your_organisations import YOUR_ORGANISATIONS, an_account, groups_on, join_link


def new_group_form(client):
    """✨ Where the page's "New group" form posts, or None when the page offers none."""
    page = main_of(client.get(YOUR_ORGANISATIONS).content.decode())
    form = re.search(r'<form method="post" action="([^"]+)"[^>]*>(?:(?!</form>).)*name="name"', page, re.S)
    return form.group(1) if form else None


@pytest.mark.django_db
def test_an_organisation_admin_creates_a_team_that_appears_at_once_with_its_own_link(client, django_user_model):
    cohort = a_group("Example Church", "Autumn cohort")
    admin = an_account(client, django_user_model, "admin")
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, organisation=cohort.organisation)

    created = client.post(new_group_form(client), {"name": "Worship team", "type": "team"})

    assert created.status_code == 303
    team = Group.objects.get(name="Worship team")
    assert team.organisation == cohort.organisation
    groups = groups_on(client)
    assert set(groups) == {"Autumn cohort", "Worship team"}
    assert "Team" in groups["Worship team"]
    assert join_link(team) in groups["Worship team"] and team.join_token != cohort.join_token


@pytest.mark.django_db
def test_a_group_admin_is_not_offered_and_is_refused_a_new_group(client, django_user_model):
    cohort = a_group("Example Church", "Autumn cohort")
    admin = an_account(client, django_user_model, "admin")
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, group=cohort)

    assert new_group_form(client) is None

    refused = client.post(
        f"/organisations/{cohort.organisation.pk}/groups/new/", {"name": "Worship team", "type": "team"}
    )

    assert refused.status_code == 403
    assert not Group.objects.filter(name="Worship team").exists()


def replace_link(client, group_name):
    """✨ Follows the group's "Replace link" to its confirmation, and confirms."""
    section = groups_on(client)[group_name]
    confirmation = re.search(r'<a href="([^"]+)"[^>]*>Replace link</a>', section).group(1)
    page = client.get(confirmation).content.decode()
    action = re.search(r'<form method="post" action="([^"]+)"', main_of(page)).group(1)
    return client.post(action)


@pytest.mark.django_db
def test_replacing_a_link_stops_the_old_one_and_the_new_one_works_with_members_kept(client, django_user_model):
    cohort = a_group("Example Church", "Autumn cohort")
    member = django_user_model.objects.create_user(username="member")
    Membership.objects.create(participant=member, group=cohort)
    admin = an_account(client, django_user_model, "admin")
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, organisation=cohort.organisation)
    old_link = join_link(cohort)

    replaced = replace_link(client, "Autumn cohort")

    assert replaced.status_code == 303
    cohort.refresh_from_db()
    assert join_link(cohort) != old_link
    assert join_link(cohort) in groups_on(client)["Autumn cohort"]
    assert "This link no longer works" in text_of(client.get(old_link).content.decode())
    assert "Join Example Church, Autumn cohort?" in text_of(client.get(join_link(cohort)).content.decode())
    assert Membership.objects.filter(participant=member, group=cohort).exists()


@pytest.mark.django_db
def test_a_group_admin_can_replace_their_own_groups_link_but_not_anothers(client, django_user_model):
    cohort = a_group("Example Church", "Autumn cohort")
    team = a_group("Example Church", "Worship team", Group.Type.TEAM)
    admin = an_account(client, django_user_model, "admin")
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, group=cohort)
    cohort_link, team_link = join_link(cohort), join_link(team)

    assert replace_link(client, "Autumn cohort").status_code == 303
    refused = client.post(f"/groups/{team.pk}/replace-link/")

    cohort.refresh_from_db()
    team.refresh_from_db()
    assert join_link(cohort) != cohort_link
    assert refused.status_code == 403
    assert join_link(team) == team_link
