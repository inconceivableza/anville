"""✨ "Your organisations": an organisation or group admin sees the groups they have rights over, each with its type,
member count and join link to copy."""

import re

import pytest

from organisations.models import Group, Membership, Organisation, Permission
from tests.journeys.pages import main_of, text_of
from tests.journeys.test_consent import give_consent
from tests.journeys.test_your_groups import a_group

YOUR_ORGANISATIONS = "/organisations/"


def an_account(client, django_user_model, username):
    """✨ A signed-in account that has consented."""
    person = django_user_model.objects.create_user(username=username, email=f"{username}@example.com")
    client.force_login(person)
    give_consent(client)
    return person


def hub_foot(client):
    hub = main_of(client.get("/hub/").content.decode())
    return re.search(r'<p[^>]*>(?:(?!</p>).)*href="/consent/".*?</p>', hub, re.S).group(0)


@pytest.mark.django_db
def test_the_hub_links_your_organisations_only_for_an_account_holding_a_permission(client, django_user_model):
    person = an_account(client, django_user_model, "admin")
    assert YOUR_ORGANISATIONS not in hub_foot(client)

    church = Organisation.objects.create(name="Example Church")
    Permission.objects.create(holder=person, capability=Permission.Capability.SEE_PROGRESS, organisation=church)

    assert re.search(rf'<a href="{YOUR_ORGANISATIONS}">Your organisations</a>', hub_foot(client))


@pytest.mark.django_db
def test_an_account_without_a_permission_is_refused_the_page(client, django_user_model):
    a_group("Example Church", "Autumn cohort")
    an_account(client, django_user_model, "participant")

    page = client.get(YOUR_ORGANISATIONS)

    assert page.status_code == 403
    assert "Autumn cohort" not in page.content.decode()


def groups_on(client):
    """✨ Each group the page shows, by name, as the markup of its own part of the page."""
    page = main_of(client.get(YOUR_ORGANISATIONS).content.decode())
    sections = re.findall(r'<section class="administered-group".*?</section>', page, re.S)
    return {text_of(re.search(r"<h3.*?</h3>", section, re.S).group(0)): section for section in sections}


def join_link(group):
    return f"http://testserver/join/{group.join_token}/"


def members_in(group, django_user_model, count):
    for number in range(count):
        member = django_user_model.objects.create_user(username=f"{group.pk}-{number}")
        Membership.objects.create(participant=member, group=group)


@pytest.mark.django_db
def test_an_organisation_admin_sees_every_group_with_its_type_member_count_and_join_link(client, django_user_model):
    cohort = a_group("Example Church", "Autumn cohort")
    team = a_group("Example Church", "Worship team", Group.Type.TEAM)
    elsewhere = a_group("Example Mission", "Mission cohort")
    members_in(cohort, django_user_model, 3)
    members_in(elsewhere, django_user_model, 1)
    admin = an_account(client, django_user_model, "admin")
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, organisation=cohort.organisation)

    groups = groups_on(client)

    assert set(groups) == {"Autumn cohort", "Worship team"}
    assert "Cohort" in text_of(groups["Autumn cohort"]) and "3 members" in text_of(groups["Autumn cohort"])
    assert "Team" in text_of(groups["Worship team"]) and "0 members" in text_of(groups["Worship team"])
    assert join_link(cohort) in groups["Autumn cohort"] and join_link(team) in groups["Worship team"]
    assert "Example Church" in text_of(main_of(client.get(YOUR_ORGANISATIONS).content.decode()))


@pytest.mark.django_db
def test_a_group_admin_sees_only_their_group(client, django_user_model):
    cohort = a_group("Example Church", "Autumn cohort")
    team = a_group("Example Church", "Worship team", Group.Type.TEAM)
    admin = an_account(client, django_user_model, "admin")
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, group=cohort)

    groups = groups_on(client)
    page = main_of(client.get(YOUR_ORGANISATIONS).content.decode())

    assert set(groups) == {"Autumn cohort"}
    assert join_link(cohort) in groups["Autumn cohort"]
    assert "Worship team" not in page and join_link(team) not in page
