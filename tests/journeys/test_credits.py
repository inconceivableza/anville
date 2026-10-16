# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The credits page, which carries the copyright notice of each translation the site quotes (ticket 39).

Both publishers ask for their notice on the work's copyright page, which for a website is one page every page
links to. The document's translation's notice covers every passage "unless otherwise indicated", and a passage from
another translation names it beside its reference, so that translation's marked notice points at it. The homepage's
verse is the homepage's own, so its notice is too, whatever pathway is published.
"""

import pytest

from tests.documents import ESV_NOTICE, NIV_NOTICE, pathway_document, sort_pathway, translated
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


# ✨ Photos' credits (ticket 49b)

REQUIRED = "Photograph by Ada Example, CC BY 4.0."
COURTESY = "Photograph of grass from Unsplash."


def with_photos(document, *, courtesy_shown):
    """✨ The pathway with a photo for each of its three sections, one credit of each kind."""
    document["photos"] = {
        "onboarding": {"file": "grass.jpg", "credit": {"kind": "required", "text": REQUIRED}},
        "calling": {"file": "grass.jpg", "credit": {"kind": "courtesy", "text": COURTESY}},
        "strengths": {"file": "grass.jpg", "credit": {"kind": "none"}},
    }
    document["show_courtesy_credits"] = courtesy_shown
    return document


@pytest.mark.django_db
@pytest.mark.parametrize("courtesy_shown", [True, False])
def test_a_required_credit_is_always_listed_a_courtesy_one_only_while_the_setting_is_on_and_none_needs_nothing(
    client, load_pathway, courtesy_shown
):
    """✨ The setting can never hide a credit a photo's licence requires (developer's call, 15 Oct)."""
    load_pathway(with_photos(sort_pathway(), courtesy_shown=courtesy_shown))

    page = client.get(CREDITS).content.decode()

    assert REQUIRED in page
    assert (COURTESY in page) is courtesy_shown
    assert page.count('class="credits-photo"') == (2 if courtesy_shown else 1)
