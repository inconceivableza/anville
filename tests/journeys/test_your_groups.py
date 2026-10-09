"""✨ "Your groups": a participant sees each group they are in and what its admins see, and can leave any of them."""

import re

import pytest

from tests.journeys.pages import main_of, text_of
from tests.journeys.test_consent import give_consent

YOUR_GROUPS = "/groups/"


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
