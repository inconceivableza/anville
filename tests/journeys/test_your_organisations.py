"""✨ "Your organisations": an organisation or group admin sees the groups they have rights over, each with its type,
member count and join link to copy."""

import re

import pytest

from organisations.models import Group, Organisation, Permission
from tests.journeys.pages import main_of
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
