# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The privacy page (ticket 100): what the app keeps, who sees it and how to withdraw, open to anyone, and reached
from every page's footer and from the consent tick's "privacy notice". Its wording is a hand check.
"""

import pytest

from tests.documents import pathway_document
from tests.journeys.test_entry_page import ENTRY_PAGE, signed_up  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)

PRIVACY = "/privacy/"


@pytest.mark.django_db
def test_anyone_can_open_the_privacy_page_signed_in_or_not(client, django_user_model, load_pathway):
    """✨ Visitors, observers and coaches have no account, so the page asks for none, and a participant who has not
    consented must still be able to read it."""
    load_pathway(pathway_document())
    assert client.get(PRIVACY).status_code == 200

    client.force_login(django_user_model.objects.create_user(username="new", email="new@example.com"))
    assert client.get(PRIVACY).status_code == 200


@pytest.mark.django_db
def test_the_homepage_a_section_page_and_an_account_page_each_link_to_the_privacy_page(  # noqa: F811
    signed_in_client, load_pathway
):
    """✨ The homepage, the engine's pages and the account pages each have their own layout and footer, so each
    carries the link."""
    load_pathway(pathway_document())

    for address in ("/", "/sections/onboarding/"):
        assert f'href="{PRIVACY}"' in signed_in_client.get(address).content.decode(), address
    signed_in_client.logout()
    assert f'href="{PRIVACY}"' in signed_in_client.get("/accounts/login/").content.decode()


@pytest.mark.django_db
def test_the_consent_ticks_privacy_notice_links_to_the_privacy_page(signed_up):  # noqa: F811
    """✨ The tick agrees to storing "as set out in the privacy notice", so the notice is one press away."""
    page = signed_up.get(ENTRY_PAGE).content.decode()

    assert f'<a href="{PRIVACY}">privacy notice</a>' in page
