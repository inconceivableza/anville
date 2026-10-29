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


@pytest.mark.django_db
def test_the_hero_no_longer_says_who_it_is_for(client):
    """✨ The content owner's feedback (23 Oct): the "For adults aged 18" line goes; the wizard still asks (ADR 0021)."""
    page = client.get("/").content.decode()

    assert "aged 18" not in page


def section(page, opening):
    """✨ One panel of the homepage, from its opening tag to its closing one."""
    return re.search(opening + r".*?</(?:section|header)>", page, re.S).group(0)


@pytest.mark.django_db
def test_how_it_works_shows_five_steps_with_title_and_summary_in_the_page_itself(client):
    """✨ Ticket 98: the steps are in the served page, so they read without JavaScript."""
    page = client.get("/").content.decode()
    how = section(page, r'<section class="panel atabs"')

    steps = re.findall(r'<li class="step step-\d">(.*?)</li>', how, re.S)
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
def test_the_logo_and_its_line_sit_below_the_overviews_button(client):
    """✨ The content owner's 28 Oct tweak: the overview was crowded above its button, so the logo and "A calling
    journey" move below it, and "Along the way" stays above it, on its own."""
    overview = section(client.get("/").content.decode(), r'<section class="panel mission"')
    sign = re.search(r'<div class="sign">.*?</div>', overview, re.S).group(0)

    assert '<use href="#logo"' in sign
    assert "A calling journey for every season of life" in sign
    assert "Along the way" not in sign
    assert overview.index("Begin your journey") < overview.index('<div class="sign">')


@pytest.mark.django_db
def test_space_to_reflect_is_gone(client):
    page = client.get("/").content.decode()

    assert "Space to reflect" not in page
    assert 'class="panel impact"' not in page


@pytest.mark.django_db
def test_nothing_on_the_homepage_points_at_a_placeholder(client):
    """✨ No link to nowhere, no anchor without its section, and no form with nothing behind it: the one form is "Stay in
    touch", which posts to the homepage itself (ticket 74)."""
    page = client.get("/").content.decode()

    assert 'href="#"' not in page
    assert re.findall(r'<form\b[^>]*\baction="([^"]*)"', page) == ["/#stay-in-touch"]
    fragments = set(re.findall(r'href="#([^"]*)"', page))
    targets = set(re.findall(r'\bid="([^"]+)"', page))
    assert fragments <= targets


@pytest.mark.django_db
def test_the_difference_it_makes_follows_the_testimonial_with_its_three_figures(client):
    """✨ Ticket 99: the figures are the spec's unconfirmed ones; this test names them so they are easy to find. The
    content owner's 28 Oct tweak moved the light section below the dark testimonial, so the two light sections, it and
    "For churches", no longer sit together."""
    page = client.get("/").content.decode()
    difference = section(page, r'<section class="panel difference"')

    assert re.search(r"<h2[^>]*>The difference it makes</h2>", difference)
    assert re.findall(r"<b>(\d+)</b>%", difference) == ["71", "86", "100"]
    assert (
        page.index('class="panel churches"')
        < page.index('class="panel story-sec"')
        < page.index('class="panel difference"')
        < page.index('id="stay-in-touch"')
    )


@pytest.mark.django_db
def test_each_figure_carries_its_value_for_the_count_up_and_already_shows_it(client):
    """✨ The count-up (main.js) reads data-v; the page holds the final figure, so it shows with JavaScript off."""
    difference = section(client.get("/").content.decode(), r'<section class="panel difference"')

    assert re.findall(r'<div class="stat" data-v="(\d+)"><span class="num"><b>(\d+)</b>', difference) == [
        ("71", "71"),
        ("86", "86"),
        ("100", "100"),
    ]


@pytest.mark.django_db
def test_every_step_is_in_the_page_with_its_own_photo_class_for_the_no_javascript_list(client):
    page = client.get("/").content.decode()
    steps = re.findall(r'<li class="step (step-\d)"><span class="tp-step">STEP 0\d</span>', page)

    assert steps == ["step-1", "step-2", "step-3", "step-4", "step-5"]


@pytest.mark.django_db
def test_for_churches_has_the_new_copy_and_a_waitlist_button_and_the_articles_are_gone(client):
    page = client.get("/").content.decode()
    churches = section(page, r'<section class="panel churches"')

    assert "Releasing and equipping your members to do whatever they do for the glory of God." in churches
    assert "<b>95%</b>" in churches
    points = re.findall(r"<li><b>([^<]+)</b>", churches)
    assert points == ["Run it together", "Invite trusted voices", "Raise up coaches", "Free for participants"]
    waitlist = re.search(r'<a\s[^>]*href="#([^"]*)"[^>]*>\s*Join the waitlist', churches)
    assert waitlist, "no Join the waitlist button"
    assert re.search(r'\bid="%s"' % waitlist.group(1), page)
    assert "Ideas to explore" not in page
    assert 'class="post' not in page


@pytest.mark.django_db
def test_the_testimonial_is_labelled_impact_and_keeps_its_words(client):
    page = client.get("/").content.decode()
    story = section(page, r'<section class="panel story-sec"')

    assert '<span class="label">Impact</span>' in story
    assert "A story from a parent" not in page
    assert "My son got saved just a couple of years ago" in story
    assert "Parent of a participant, 2025" in story


@pytest.mark.django_db
def test_the_testimonial_is_the_one_quote_alone(client):
    """✨ A large line from the quote above it, for the content owner's 23 Oct feedback, was tried and read no better
    than the quote alone, so it went (29 Oct)."""
    story = section(client.get("/").content.decode(), r'<section class="panel story-sec"')

    assert "story-pull" not in story
    assert len(re.findall(r"<blockquote", story)) == 1


@pytest.mark.django_db
def test_the_five_callings_are_photos_alone_each_naming_its_calling(client):
    """✨ Ticket 99: the photos belong to the cards themselves, so they show with JavaScript off. The content owner's 28
    Oct tweak dropped the captions, as v3's people are photos alone; each card still names its calling to a screen
    reader."""
    page = client.get("/").content.decode()
    meet = section(page, r'<section class="panel meet"')

    cards = re.findall(r'<div class="mc mc-([a-z]+)" role="img" aria-label="([^"]+)"></div>', meet)
    assert cards == [
        ("teacher", "Teacher"),
        ("carpenter", "Electrician"),
        ("parent", "Parent"),
        ("pastor", "Church planter"),
        ("student", "Student"),
    ]
    assert "Seeing the classroom" not in meet
    assert "donat" not in meet.casefold()


@pytest.mark.django_db
def test_the_black_footer_has_the_quote_and_one_column_of_links(client):
    page = client.get("/").content.decode()
    footer = re.search(r"<footer.*?</footer>", page, re.S).group(0)

    links = re.findall(r'<a\s[^>]*href="([^"]*)"[^>]*>([^<]+)</a>', footer)
    assert links == [
        ("#how", "How it works"),
        ("#impact", "Impact"),
        ("#churches", "For churches"),
        ("#stay-in-touch", "Contact us"),
        ("/privacy/", "Privacy"),
        ("/credits/", "Credits"),
    ]
    assert "Whatever you do, work at it with all your heart, as working for the Lord." in footer
    assert "Colossians 3:23 (NIV)" in footer
    assert "© 2026 Whatever You Do" in footer
    for gone in ("<b>Note</b>", "The evaluation", "Writing", "A guided calling journey"):
        assert gone not in footer
    assert re.search(r'\bid="impact"', page)


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
