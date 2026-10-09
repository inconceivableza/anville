"""✨ "Your organisations": an organisation or group admin sees the groups they have rights over, each with its type,
member count and join link to copy."""

import re

import pytest
from django.test import Client

from access.models import Account
from organisations.models import Group, Membership, Organisation, Permission
from tests.documents import pathway_document
from tests.journeys.pages import main_of, text_of
from tests.journeys.test_consent import answer, give_consent, today
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


@pytest.mark.django_db
def test_an_admin_who_has_not_consented_still_gets_the_page(client, django_user_model):
    cohort = a_group("Example Church", "Autumn cohort")
    admin = django_user_model.objects.create_user(username="admin", email="admin@example.com")
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, organisation=cohort.organisation)
    client.force_login(admin)

    page = client.get(YOUR_ORGANISATIONS)

    assert page.status_code == 200
    assert set(groups_on(client)) == {"Autumn cohort"}


@pytest.mark.django_db
def test_the_join_link_has_a_copy_button_run_by_the_pages_script_not_by_htmx(client, django_user_model):
    """✨ The clipboard itself is a manual check; here, that the button names the field holding the link, and that
    nothing on the page asks htmx to run code (ADR 0006)."""
    cohort = a_group("Example Church", "Autumn cohort")
    admin = an_account(client, django_user_model, "admin")
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, group=cohort)

    section = groups_on(client)["Autumn cohort"]
    page = client.get(YOUR_ORGANISATIONS).content.decode()

    copies = re.search(r'<button type="button"[^>]*data-copy="([^"]+)"[^>]*>Copy</button>', section).group(1)
    field = re.search(rf'<input[^>]*id="{copies}"[^>]*>', section).group(0)
    assert f'value="{join_link(cohort)}"' in field and "readonly" in field
    assert "hx-on" not in page and "eval" not in page


def a_member_of(group, django_user_model, display_name):
    """✨ A member with a display name, signed in on a client of their own, which is returned."""
    member = django_user_model.objects.create_user(username=display_name, email=f"{display_name}@example.com")
    Account.objects.create(participant=member, display_name=display_name)
    Membership.objects.create(participant=member, group=group)
    member_client = Client()
    member_client.force_login(member)
    return member_client


def members_of(client, group_name):
    """✨ Each member a group shows, by display name, as the text of their entry."""
    rows = re.findall(r'<li class="member".*?</li>', groups_on(client)[group_name], re.S)
    return {text_of(re.search(r'<span class="member-name".*?</span>', row, re.S).group(0)): text_of(row) for row in rows}


@pytest.fixture
def cohort_and_admin(client, django_user_model, load_pathway):
    """✨ The test pathway published, an Autumn cohort, and its group admin signed in on `client`."""
    load_pathway(pathway_document())
    cohort = a_group("Example Church", "Autumn cohort")
    admin = an_account(client, django_user_model, "admin")
    Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, group=cohort)
    return cohort


@pytest.mark.django_db
def test_a_member_shows_their_display_name_sections_complete_of_their_track_and_the_date_last_active(
    client, django_user_model, cohort_and_admin
):
    dan = a_member_of(cohort_and_admin, django_user_model, "Dan")
    give_consent(dan)
    answer(dan, "baseline-bible", "7")
    dan.post("/sections/onboarding/complete/")

    member = members_of(client, "Autumn cohort")["Dan"]

    assert "1 of 2 sections" in member
    assert today() in member
    assert not re.search(r"\d{1,2}:\d{2}", member)
