# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The header on every participant page, and the pathway sidebar it opens (ticket 41a).

The header leads to the hub and lets the participant sign out; the sidebar lists what the hub lists, from the same
derivation as the hub, so its statuses and locks are the hub's by construction (ticket 80). Observers and the coach have no
account, so their pages have neither. Opening and closing the sidebar without JavaScript is a hand check.
"""

import json
import re
from html.parser import HTMLParser

import pytest

from engine.document.blocks import COMPARISON_STATUSES
from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_answers import answer
from tests.journeys.test_coach_checklist import choose, the_coach_checklist
from tests.journeys.test_coach_link import issue_coach_link, with_a_coach_and_contacts, with_a_coach_card
from tests.journeys.test_comparison_on_the_hub import ACTION, hub_row, with_the_card_on_the_hub
from tests.journeys.test_contact_list import JO, PRIYA, save_contacts
from tests.journeys.test_hub import CALLING_NOTE, PEOPLE, add_people_with_links, answer_through, lock_button
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import issue_link
from tests.journeys.test_observer_assessment import press_compare
from tests.journeys.test_observer_landing import claim
from tests.journeys.test_results import submit_sort

SORT, STRENGTHS, CALLING = "strengths-sort", "strengths", "calling"


def with_a_coach_in_section_1():
    """✨ The test pathway with the sort's section, and Whatever You Do's coach checklist in the calling section, which
    stands for Section 1 here: locked until onboarding is complete, like the coach page it holds."""
    document = sort_pathway()
    calling = next(section for section in document["content"]["sections"] if section["id"] == CALLING)
    calling["blocks"].append(the_coach_checklist())
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(with_a_coach_in_section_1())
    return signed_in_client


@pytest.fixture
def under_way(participant):
    """✨ A participant past onboarding with the sort in, so every page the sidebar leads to has something on it."""
    participant.post("/sections/onboarding/complete/")
    answer(participant, SORT, json.dumps(complete_sort()), section=STRENGTHS)
    return participant


def header_of(page):
    """✨ The participant header, or None on a page without one."""
    found = re.search(r'<header class="site-header".*?</header>', page, re.S)
    return found.group(0) if found else None


def the_header(page):
    """✨ The participant header, which the page must have."""
    header = header_of(page)
    assert header is not None, "no header on the page"
    return header


def sidebar_of(page):
    """✨ The pathway sidebar, or None on a page without one."""
    found = re.search(r'<nav class="pathway-nav".*?</nav>', page, re.S)
    return found.group(0) if found else None


def section_in(sidebar, title):
    """✨ The sidebar's entry for one section, found by its title."""
    assert sidebar is not None, "no sidebar on the page"
    entries = re.findall(r'<li class="pathway-nav-section.*?</li>', sidebar, re.S)
    return next(entry for entry in entries if title in entry)


@pytest.mark.django_db
def test_observers_and_the_coachs_pages_have_no_header_sidebar_or_sign_out_even_in_the_participants_browser(
    signed_in_client, load_pathway  # noqa: F811
):
    """✨ The participant's own browser is the likeliest to open their links, and is signed in."""
    load_pathway(with_a_coach_and_contacts())
    choose(signed_in_client)
    coach_link = issue_coach_link(signed_in_client)
    save_contacts(signed_in_client, JO, PRIYA)
    observer_link = issue_link(signed_in_client, "Jo")
    landing = signed_in_client.get(observer_link).content.decode()
    claim(signed_in_client, observer_link)

    for page in (
        signed_in_client.get(coach_link).content.decode(),
        landing,
        signed_in_client.get("/observe/").content.decode(),
    ):
        assert header_of(page) is None
        assert sidebar_of(page) is None
        assert "/accounts/logout/" not in page


@pytest.mark.django_db
def test_a_locked_section_is_listed_but_its_address_is_nowhere_in_the_sidebar(participant):
    sidebar = sidebar_of(participant.get("/sections/onboarding/").content.decode())

    assert "Locked" in section_in(sidebar, "Putting your calling into words")
    assert "Locked" in section_in(sidebar, "Strengths assessment")
    assert f"/sections/{CALLING}/" not in sidebar  # ✨ the coach page is on it, so not that either
    assert f"/sections/{STRENGTHS}/" not in sidebar


@pytest.mark.django_db
def test_a_locked_entrys_status_in_the_sidebar_is_a_button_described_by_the_hubs_lock_note(participant):
    """✨ On the hub's own page too, so neither the hub's note nor the sidebar's is the other's (ticket 97)."""
    page = participant.get("/hub/").content.decode()

    calling = section_in(sidebar_of(page), "Putting your calling into words")
    assert lock_button(page, calling) == ("Locked", CALLING_NOTE)
    assert "aria-describedby" not in section_in(sidebar_of(page), "Before we begin")


@pytest.mark.django_db
def test_after_onboarding_the_sidebar_shows_statuses_marks_the_current_section_and_leads_everywhere_open(under_way):
    sidebar = sidebar_of(under_way.get(f"/sections/{CALLING}/").content.decode())

    assert "Complete" in section_in(sidebar, "Before we begin")
    assert "In progress" in section_in(sidebar, "Strengths assessment")
    calling = section_in(sidebar, "Putting your calling into words")
    assert "Not started" in calling
    assert 'aria-current="page"' in calling
    assert sidebar.count('aria-current="page"') == 1
    for address in (
        f'href="/sections/{CALLING}/"',
        f'href="/results/{SORT}/"',
        f'href="/results/{SORT}/comparison/"',
        'href="/invitations/"',
        f'href="/sections/{CALLING}/#block-coach"',
    ):
        assert address in sidebar


@pytest.mark.django_db
@pytest.mark.parametrize(
    "address",
    ["/hub/", f"/sections/{CALLING}/", f"/results/{SORT}/", f"/results/{SORT}/comparison/"],
)
def test_every_participant_page_carries_the_header_with_sign_out_and_the_sidebar(under_way, address):
    page = under_way.get(address).content.decode()

    header = the_header(page)
    assert re.search(r'<a [^>]*href="/hub/"[^>]*>\s*Test Pathway\s*</a>', header)
    assert re.search(r'<form [^>]*method="post"[^>]*action="/accounts/logout/"', header)
    assert sidebar_of(page) is not None


@pytest.mark.django_db
def test_with_the_sidebar_switched_off_the_header_and_sign_out_remain(under_way, settings):
    settings.ANVILLE_SIDEBAR = False

    page = under_way.get(f"/sections/{CALLING}/").content.decode()

    header = the_header(page)
    assert 'href="/hub/"' in header
    assert 'action="/accounts/logout/"' in header
    assert sidebar_of(page) is None
    assert "pathway-nav" not in page


@pytest.mark.django_db
def test_the_credits_page_carries_the_header_only_for_someone_signed_in(under_way):
    """✨ It is public, and reached from every page's footer: a participant gets their way back, a visitor nothing."""
    assert header_of(under_way.get("/credits/").content.decode()) is not None

    under_way.logout()

    assert header_of(under_way.get("/credits/").content.decode()) is None


@pytest.mark.django_db
def test_signing_out_from_the_header_ends_the_session_and_leads_to_the_homepage(under_way):
    header = the_header(under_way.get("/hub/").content.decode())
    action = re.search(r'<form [^>]*action="([^"]+)"', header).group(1)

    signed_out = under_way.post(action)

    assert signed_out.status_code == 302
    assert signed_out.url == "/"
    assert under_way.get("/hub/").url.startswith("/accounts/login/")


def with_the_hubs_entries():
    """✨ 67b's pathway, with a part, the comparison signpost's row and Five trusted voices, and Walk with a coach added:
    every kind of entry the hub lists, as Whatever You Do has them."""
    document = with_the_card_on_the_hub()
    document["content"]["sections"] += with_a_coach_card()["content"]["sections"][-1:]
    return document


@pytest.fixture
def listing(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(with_the_hubs_entries())
    return signed_in_client


def started(client):
    """✨ Onboarding complete, a coach chosen, three people with links and the sort in: the comparison's row is shown."""
    client.post("/sections/onboarding/complete/")
    choose(client)
    client.links = add_people_with_links(client, *PEOPLE)
    submit_sort(client, complete_sort())
    return client


class _Tree(HTMLParser):
    """✨ The markup as nested nodes, {"tag", "class", "children"}, with the text between them as strings."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self, page):
        super().__init__()
        self.root = {"tag": None, "class": [], "children": []}
        self.open = [self.root]
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "class": (dict(attrs).get("class") or "").split(), "children": []}
        self.open[-1]["children"].append(node)
        if tag not in self.VOID:
            self.open.append(node)

    def handle_endtag(self, tag):
        while len(self.open) > 1 and self.open.pop()["tag"] != tag:
            pass

    def handle_data(self, data):
        self.open[-1]["children"].append(data)


def _nodes(node, skip=lambda node: False):
    """✨ Every node within `node`, in the page's order, leaving out any that `skip` names and all within them."""
    for child in node["children"]:
        if isinstance(child, dict) and not skip(child):
            yield child
            yield from _nodes(child, skip)


def _words(node):
    """✨ What a reader sees of a node, its spacing evened."""
    parts = [child if isinstance(child, str) else _words(child) for child in node["children"]]
    return " ".join(" ".join(parts).split())


def _entries(page, is_entry, is_title, is_status, is_locked):
    """✨ Each entry on the page, as (title, status, locked), its title and status its own, not those of entries in it."""
    found = []
    for node in _nodes(_Tree(page).root):
        if is_entry(node):
            own = list(_nodes(node, is_entry))
            title = next(child for child in own if is_title(child))
            status = next(child for child in own if is_status(child))
            found.append((_words(title), _words(status), is_locked(node, title)))
    return found


def hub_entries(page):
    """✨ The hub's rows and side cards, in its order: the list, then the cards beside it."""
    return _entries(
        page,
        lambda node: (node["tag"] == "li" and "srow" in node["class"])
        or (node["tag"] == "section" and "hub-side-card" in node["class"]),
        lambda node: node["tag"] == "h3",
        lambda node: node["tag"] == "span" and "tag" in node["class"],
        lambda entry, title: "locked" in entry["class"],
    )


def sidebar_entries(sidebar):
    """✨ The sidebar's entries, in its order; a locked one's title is not a link or a press."""
    return _entries(
        sidebar,
        lambda node: node["tag"] == "li" and "pathway-nav-section" in node["class"],
        lambda node: "pathway-nav-title" in node["class"],
        lambda node: "status-chip" in node["class"],
        lambda entry, title: title["tag"] == "span",
    )


@pytest.mark.django_db
def test_the_sidebar_lists_what_the_hub_lists_in_its_order_with_its_statuses_and_locks(listing):
    def both():
        page = listing.get("/hub/").content.decode()
        return hub_entries(page), sidebar_entries(sidebar_of(page))

    hub, sidebar = both()
    assert sidebar == hub
    assert any(locked for _, _, locked in hub)

    started(listing)
    hub, sidebar = both()
    assert sidebar == hub
    assert "How others see you" in [title for title, _, _ in hub]

    answer_through(*listing.links)
    press_compare(listing)
    hub, sidebar = both()
    assert sidebar == hub
    assert ("How others see you", COMPARISON_STATUSES["viewed"], False) in hub


@pytest.mark.django_db
def test_how_others_see_you_is_listed_within_section_1_after_the_assessment_as_the_hubs_press(listing):
    listing.post("/sections/onboarding/complete/")
    assert "How others see you" not in sidebar_of(listing.get("/hub/").content.decode())

    started(listing)
    answer_through(*listing.links)  # ✨ the press from the minimum; below it, both lead to Five trusted voices (fix-3)
    sidebar = sidebar_of(listing.get(f"/sections/{CALLING}/").content.decode())
    parts = re.search(r'<ol class="pathway-nav-parts">.*?</ol>', sidebar, re.S).group(0)

    assert parts.index("Strengths assessment") < parts.index("How others see you")
    assert ACTION.search(parts).group(1) == ACTION.search(hub_row(listing)).group(1)
    assert f'href="/results/{SORT}/comparison/"' not in parts


@pytest.mark.django_db
def test_with_the_side_cards_and_the_row_listed_every_link_below_the_entries_stays(listing):
    """✨ They are quick ways in beside the entries, as before (developer's call, 23 Oct)."""
    sidebar = sidebar_of(started(listing).get(f"/sections/{CALLING}/").content.decode())
    links = re.search(r'<ul class="pathway-nav-links">.*?</ul>', sidebar, re.S).group(0)

    assert re.findall(r">([^<]+)</a>", links) == [
        "Your results",
        "How others experience you",
        "Invite others to assess you",
        "Your coach",
    ]
