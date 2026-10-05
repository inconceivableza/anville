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
