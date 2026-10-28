# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The public homepage at the site's root, copied from the prototype (ticket 32a)."""

import re

import pytest


def begin_links(page):
    """✨ Where each of the page's "Begin" buttons leads."""
    return re.findall(r'<a\s[^>]*href="([^"]*)"[^>]*>\s*Begin\b', page)


def addresses(page):
    """✨ Every address the page asks the browser to load or follow."""
    return re.findall(r'\b(?:src|href|poster|srcset)="([^"]*)"', page)


def video_tag(page):
    """✨ The hero's opening <video> tag, with its attributes."""
    video = re.search(r"<video\b[^>]*>", page)
    assert video, "no video on the page"
    return video.group(0)


@pytest.mark.django_db
def test_a_visitor_gets_the_homepage_and_begin_leads_to_sign_up(client):
    response = client.get("/")

    assert response.status_code == 200
    assert set(begin_links(response.content.decode())) == {"/accounts/signup/"}


@pytest.mark.django_db
def test_a_signed_in_participant_gets_the_homepage_and_begin_leads_to_the_hub(client, django_user_model):
    client.force_login(django_user_model.objects.create_user(username="sam@example.com", email="sam@example.com"))

    response = client.get("/")

    assert response.status_code == 200
    assert set(begin_links(response.content.decode())) == {"/hub/"}


@pytest.mark.django_db
def test_the_homepages_top_bar_holds_the_logo_alone(client):
    """✨ Ticket 91: no link or button but the logo, which leads to the top of the page."""
    page = client.get("/").content.decode()

    bar = re.search(r'<nav class="nav"[^>]*>(.*?)</nav>', page, re.S)
    assert bar is not None, "no top bar on the page"
    assert re.findall(r'<a\s[^>]*href="([^"]*)"', bar.group(1)) == ["#top"]
    assert "<button" not in bar.group(1)
    assert '<use href="#logo"' in bar.group(1)


@pytest.mark.django_db
def test_the_new_logo_replaces_the_old_mark_and_name_in_the_bar_and_the_footer(client):
    page = client.get("/").content.decode()
    footer = re.search(r"<footer.*?</footer>", page, re.S).group(0)

    assert '<use href="#logo"' in footer
    assert "<b>Whatever You Do</b>" not in footer
    assert "<span>Whatever You Do</span>" not in page


@pytest.mark.django_db
def test_the_homepage_has_no_fixed_bar_and_the_new_logo_shows_in_the_overview_section_too(client):
    """✨ Fix-5: the logo sits in the hero's nav as before ticket 91, and replaces the old mark in the overview."""
    page = client.get("/").content.decode()
    overview = re.search(r'<section class="panel mission".*?</section>', page, re.S).group(0)

    assert 'class="top-bar"' not in page
    assert '<use href="#logo"' in overview
    assert '<use href="#mark"' not in overview
    assert not re.search(r'<symbol id="[^"]*"[a-zA-Z]', page), "an attribute runs into the one before it"



    assert "For adults aged 18 and over." in client.get("/").content.decode()


def section(page, opening):
    """✨ One panel of the homepage, from its opening tag to its closing one."""
    return re.search(opening + r".*?</(?:section|header)>", page, re.S).group(0)


@pytest.mark.django_db
def test_how_it_works_shows_five_steps_with_title_and_summary_in_the_page_itself(client):
    """✨ Ticket 98: the steps are in the served page, so they read without JavaScript."""
    page = client.get("/").content.decode()
    how = section(page, r'<section class="panel atabs"')

    steps = re.findall(r'<li class="step">(.*?)</li>', how, re.S)
    assert len(steps) == 5
    for step in steps:
        assert re.search(r"<h3>[^<]+</h3>\s*<p>[^<]{40,}</p>", step)
        assert "<ul" not in step
    assert "<h2>How it works</h2>" in how
    assert "Five steps" not in page
    assert "In your workbook" not in page
    assert "In your journey" not in page


@pytest.mark.django_db
def test_the_hero_has_no_coaches_button_and_learn_more_leads_to_the_overview(client):
    page = client.get("/").content.decode()
    hero = section(page, r'<header class="panel hero"')

    assert "For coaches" not in hero
    learn_more = re.search(r'<a\s[^>]*href="#([^"]*)"[^>]*>\s*Learn more', hero)
    assert learn_more, "no Learn more in the hero"
    assert re.search(r'<section class="panel mission"[^>]*\bid="%s"' % learn_more.group(1), page)
    assert hero.index("hero-cta") < hero.index("Learn more")


@pytest.mark.django_db
def test_the_overview_has_the_sign_line_the_paragraph_and_its_own_begin_button(client):
    page = client.get("/").content.decode()
    overview = section(page, r'<section class="panel mission"')

    assert "A calling journey for every season of life" in overview
    assert "At the start and the end, you answer the same questions" in overview
    assert begin_links(overview) == ["/accounts/signup/"]
    assert overview.index("pillars") < overview.index("Along the way") < overview.index("Begin your journey")


@pytest.mark.django_db
def test_space_to_reflect_is_gone(client):
    page = client.get("/").content.decode()

    assert "Space to reflect" not in page
    assert 'class="panel impact"' not in page


@pytest.mark.django_db
def test_nothing_on_the_homepage_points_at_a_placeholder(client):
    """✨ No link to nowhere, no anchor without its section, and no form with nothing behind it."""
    page = client.get("/").content.decode()

    assert 'href="#"' not in page
    assert "<form" not in page
    fragments = set(re.findall(r'href="#([^"]*)"', page))
    targets = set(re.findall(r'\bid="([^"]+)"', page))
    assert fragments <= targets


@pytest.mark.django_db
def test_homepage_does_not_present_impact_percentages_without_context(client):
    page = client.get("/").content.decode()

    assert "71%" not in page
    assert "86%" not in page
    assert "100%" not in page


@pytest.mark.django_db
def test_nothing_on_the_homepage_loads_from_another_site(client):
    page = client.get("/").content.decode()
    video = video_tag(page)
    hero_files = re.findall(r'\b(?:src|poster)="([^"]*)"', page[page.index(video) : page.index("</video>")])

    assert addresses(page)
    assert not [address for address in addresses(page) if re.match(r"(?:[a-z]+:|//)", address, re.I)]
    assert len(hero_files) == 2, "the video and its still frame"
    assert all(address.startswith("/static/") for address in hero_files)


@pytest.mark.django_db
def test_the_homepage_never_promises_anonymity(client):
    assert "anonymous" not in client.get("/").content.decode().casefold()


@pytest.mark.django_db
def test_the_hero_video_is_muted_and_looping_with_a_still_frame(client):
    video = video_tag(client.get("/").content.decode())

    assert re.search(r"\smuted\b", video)
    assert re.search(r"\sloop\b", video)
    assert re.search(r'\sposter="[^"]+"', video)
