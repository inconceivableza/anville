"""✨ The credits page, which carries the copyright notice of each translation the site quotes (ticket 39).

Both publishers ask for their notice on the work's copyright page, which for a website is one page every page
links to. The document's translation's notice covers every passage "unless otherwise indicated", and a passage from
another translation names it beside its reference, so that translation's marked notice points at it. The homepage's
verse is the homepage's own, so its notice is too, whatever pathway is published.
"""

import pytest

from tests.documents import ESV_NOTICE, NIV_NOTICE, pathway_document, translated
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)

CREDITS = "/credits/"
HOMEPAGE_VERSE = "New International Version Anglicised"  # ✨ named in the notice for the homepage's Colossians 3:23


@pytest.mark.django_db
def test_anyone_sees_the_homepages_notice_and_that_of_every_translation_the_pathway_declares(client, load_pathway):
    """✨ Open to visitors, since the public homepage quotes scripture too, even before any pathway is published."""
    before = client.get(CREDITS)
    assert before.status_code == 200
    assert HOMEPAGE_VERSE in before.content.decode()

    load_pathway(translated(pathway_document()))

    page = client.get(CREDITS).content.decode()
    assert HOMEPAGE_VERSE in page
    assert ESV_NOTICE in page
    assert NIV_NOTICE in page


@pytest.mark.django_db
def test_the_homepage_a_section_page_and_an_account_page_each_link_to_the_credits_page(  # noqa: F811
    signed_in_client, load_pathway
):
    """✨ The homepage, the engine's pages and the account pages each have their own layout, so each carries the
    link."""
    load_pathway(translated(pathway_document()))

    for address in ("/", "/sections/onboarding/"):
        assert f'href="{CREDITS}"' in signed_in_client.get(address).content.decode(), address
    signed_in_client.logout()
    assert f'href="{CREDITS}"' in signed_in_client.get("/accounts/login/").content.decode()
