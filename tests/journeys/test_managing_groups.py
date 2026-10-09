"""✨ Managing groups from "Your organisations": an organisation admin creates a group, and an admin replaces a group's
join link when it has travelled further than intended."""

import re

import pytest

from organisations.models import Group, Permission
from tests.journeys.pages import main_of
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
