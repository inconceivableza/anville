# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The homepage's "Stay in touch" list (ticket 74, ADR 0023): one email field, its addresses kept in the app and
exported from the admin. Since ticket 111 (ADR 0027) it asks what the visitor wants, at least one of their church on the
waitlist, news by email and to be contacted, and keeps each choice with when it was ticked."""

import csv
import io
import re

import pytest
from django.utils import timezone

from engine.models import SignUp, SignUpChoice
from engine.stay_in_touch import NO_ADDRESS, NO_CHOICE, NOT_AN_ADDRESS, TRAP, WORDING_VERSION

HTMX = {"HTTP_HX_REQUEST": "true"}
CHOICES = ["waitlist", "news", "contact"]


def stay_in_touch(page):
    """✨ The "Stay in touch" section of a page, or the section htmx sent back on its own."""
    found = re.search(r'<section\b[^>]*\bid="stay-in-touch".*?</section>', page, re.S)
    assert found, "no Stay in touch section"
    return found.group(0)


def ticked(section):
    """✨ The choices the section's form shows ticked."""
    boxes = re.findall(r'<input\b[^>]*\bname="choice"[^>]*>', section)
    assert boxes, "no choices in the form"
    return {re.search(r'\bvalue="([^"]*)"', box).group(1) for box in boxes if re.search(r"\bchecked\b", box)}


def takes_the_focus(section):
    """✨ Whether the section's address field is set to take the focus as the page or the section arrives."""
    field = re.search(r'<input\b[^>]*\bname="email"[^>]*>', section)
    assert field, "no address field"
    return bool(re.search(r"\sautofocus[\s/>]", field.group(0)))


def stored():
    """✨ Every choice kept, as (address, choice), whatever the order they were kept in."""
    return set(SignUpChoice.objects.values_list("sign_up__email", "choice"))


@pytest.mark.django_db
@pytest.mark.parametrize("headers", [{}, HTMX], ids=["without JavaScript", "with htmx"])
def test_each_choice_ticked_is_stored_with_the_address_its_time_and_the_wordings_version_and_thanked_in_place(
    client, headers
):
    before = timezone.now()

    response = client.post("/", {"email": " sam@example.com ", "choice": ["waitlist", "contact", "spam"]}, **headers)

    assert response.status_code == 200
    sign_up = SignUp.objects.get()
    assert sign_up.email == "sam@example.com"
    assert before <= sign_up.signed_up_at <= timezone.now()
    assert sign_up.wording_version == WORDING_VERSION
    assert stored() == {("sam@example.com", "waitlist"), ("sam@example.com", "contact")}, "only the three are kept"
    for choice in SignUpChoice.objects.all():
        assert before <= choice.chosen_at <= timezone.now()
        assert choice.wording_version == WORDING_VERSION
    page = response.content.decode()
    shown = stay_in_touch(page)
    assert "<form" not in shown
    assert 'class="stay-thanks"' in shown
    if headers:
        assert "<main" not in page, "htmx is sent the section alone, not a new page"
    else:
        assert '<header class="panel hero"' in page, "without JavaScript the homepage comes back"


@pytest.mark.django_db
def test_a_repeat_address_in_any_case_adds_the_choices_it_had_not_made_and_never_removes_one(client):
    client.post("/", {"email": "sam@example.com", "choice": ["news"]})
    first = SignUp.objects.get()
    news = SignUpChoice.objects.get()

    again = client.post("/", {"email": "Sam@Example.com", "choice": ["waitlist"]}, **HTMX)
    client.post("/", {"email": "SAM@example.com", "choice": ["news", "contact"]}, **HTMX)

    assert again.status_code == 200
    assert 'class="stay-thanks"' in stay_in_touch(again.content.decode()), "the same thanks, telling nobody"
    assert list(SignUp.objects.values_list("pk", "email", "signed_up_at")) == [
        (first.pk, "sam@example.com", first.signed_up_at)
    ]
    assert stored() == {("sam@example.com", choice) for choice in CHOICES}
    assert SignUpChoice.objects.get(choice="news").chosen_at == news.chosen_at, "the first time it was ticked is kept"


@pytest.mark.django_db
@pytest.mark.parametrize("posted", [{}, {"choice": ["spam"]}], ids=["none ticked", "none of the three"])
@pytest.mark.parametrize("headers", [{}, HTMX], ids=["without JavaScript", "with htmx"])
def test_a_press_with_no_choice_is_refused_beside_the_button_storing_nothing_and_keeping_what_was_typed(
    client, posted, headers
):
    arrival = stay_in_touch(client.get("/").content.decode())
    assert NO_CHOICE not in arrival, "nothing is refused before the press"

    response = client.post("/", {"email": "sam@example.com", **posted}, **headers)

    assert response.status_code == 400
    shown = stay_in_touch(response.content.decode())
    assert NO_CHOICE in shown
    assert shown.index('type="submit"') < shown.index(NO_CHOICE), "the refusal follows the button"
    assert 'value="sam@example.com"' in shown
    assert ticked(shown) == set()
    assert not SignUp.objects.exists()
    assert not SignUpChoice.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "link, choice",
    [
        (r'<a\s[^>]*href="([^"]*)"[^>]*>\s*Join the waitlist', "waitlist"),
        (r'<a\s[^>]*href="([^"]*)"[^>]*>Contact us<', "contact"),
    ],
    ids=["Join the waitlist", "Contact us"],
)
def test_join_the_waitlist_and_contact_us_open_the_box_with_their_own_choice_ticked_without_javascript(
    client, link, choice
):
    """✨ The link asks the server for its choice, so it is ticked with or without JavaScript, and lands at the box: by
    the address's autofocus, which a fragment naming an element would stop the browser applying (17 Nov)."""
    page = client.get("/").content.decode()
    assert ticked(stay_in_touch(page)) == set(), "nothing is ticked on arrival"
    href = re.search(link, page).group(1)

    opened = client.get(href)

    assert href == f"/?stay={choice}", "no fragment, or the browser would not focus the address"
    assert takes_the_focus(stay_in_touch(opened.content.decode()))
    assert opened.status_code == 200
    assert ticked(stay_in_touch(opened.content.decode())) == {choice}


@pytest.mark.django_db
def test_a_link_naming_a_choice_opens_the_form_with_only_that_box_ticked_and_the_address_set_to_take_the_focus(client):
    """✨ So the visitor can type their address at once, with JavaScript or without (sprint-3d-r1-fix-4)."""
    for choice in CHOICES:
        opened = stay_in_touch(client.get("/", {"stay": choice}).content.decode())

        assert ticked(opened) == {choice}
        assert takes_the_focus(opened)


@pytest.mark.django_db
def test_a_form_no_link_opened_with_a_choice_does_not_take_the_focus(client):
    """✨ A plain visit would otherwise scroll to the box and raise a phone's keyboard; a refusal leaves the focus on
    the button that was pressed."""
    plain = client.get("/")
    naming_nothing = client.get("/", {"stay": "spam"})
    refused = client.post("/", {"choice": ["news"]}, **HTMX)

    assert refused.status_code == 400
    for response in (plain, naming_nothing, refused):
        assert not takes_the_focus(stay_in_touch(response.content.decode()))


@pytest.mark.django_db
def test_with_the_thanks_showing_htmx_asking_by_a_link_is_sent_the_form_alone_fresh_with_that_choice_ticked(client):
    """✨ How "Join the waitlist" and "Contact us" bring the form back in place of the thanks (sprint-3d-r1-fix-4):
    following the link would load the page again, restarting the hero video. The server keeps nothing of the sign-up
    the thanks answered, so what comes back is what any visit by the link shows."""
    client.post("/", {"email": "sam@example.com", "choice": ["news", "contact"]}, **HTMX)

    for choice in ("waitlist", "contact"):
        response = client.get("/", {"stay": choice}, **HTMX)

        assert response.status_code == 200
        page = response.content.decode()
        assert "<main" not in page, "htmx is sent the section alone, not a new page"
        shown = stay_in_touch(page)
        assert ticked(shown) == {choice}
        assert 'value=""' in shown
        assert takes_the_focus(shown)
        assert "HX-Request" in response["Vary"], "a cache must not hand the section alone to a visit for the page"


@pytest.mark.django_db
def test_a_press_that_fills_the_hidden_field_is_thanked_and_stores_nothing(client):
    response = client.post("/", {"email": "bot@example.com", "choice": ["news"], TRAP: "https://spam.example"})

    assert 'class="stay-thanks"' in stay_in_touch(response.content.decode())
    assert not SignUp.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "typed, refusal", [("", NO_ADDRESS), ("not an address", NOT_AN_ADDRESS), ("sam@", NOT_AN_ADDRESS)]
)
@pytest.mark.parametrize("headers", [{}, HTMX], ids=["without JavaScript", "with htmx"])
def test_an_address_that_is_not_one_is_refused_after_the_press_storing_nothing(client, typed, refusal, headers):
    arrival = stay_in_touch(client.get("/").content.decode())
    assert refusal not in arrival, "nothing is refused before the press"

    response = client.post("/", {"email": typed, "choice": ["news"]}, **headers)

    assert response.status_code == 400
    shown = stay_in_touch(response.content.decode())
    assert refusal in shown
    assert "<form" in shown
    assert f'value="{typed}"' in shown
    assert ticked(shown) == {"news"}
    assert not SignUp.objects.exists()


@pytest.mark.django_db
def test_the_admin_lists_the_sign_ups_with_their_choices_and_exports_them_with_no_cell_read_as_a_formula(
    client, admin_user
):
    """✨ The list is opened in a spreadsheet, where a cell beginning "=" would run as a formula; such an address is
    one mail can carry. A sign-up kept before there were choices (wording version 1, on staging) has none, and still
    lists and exports."""
    before = SignUp.objects.create(email="early@example.com", wording_version=1)
    client.post("/", {"email": "sam@example.com", "choice": ["waitlist", "contact"]})
    client.post("/", {"email": "=1+1@example.com", "choice": ["news"]})
    client.force_login(admin_user)

    listed = client.get("/admin/engine/signup/").content.decode()
    exported = client.post(
        "/admin/engine/signup/",
        {"action": "export_as_csv", "_selected_action": list(SignUp.objects.values_list("pk", flat=True))},
    )

    assert "sam@example.com" in listed and "early@example.com" in listed
    assert exported.status_code == 200
    assert exported["Content-Type"].startswith("text/csv")
    header, *rows = list(csv.reader(io.StringIO(exported.content.decode())))
    assert header[:3] == ["Email address", "Signed up at", "Wording version"]
    assert len(header) == 3 + len(CHOICES)
    by_address = {row[0]: row for row in rows}
    assert set(by_address) == {"early@example.com", "sam@example.com", "'=1+1@example.com"}
    assert by_address["early@example.com"][1:] == [before.signed_up_at.isoformat(), "1", "", "", ""]
    for address, choices in (("sam@example.com", {"waitlist", "contact"}), ("=1+1@example.com", {"news"})):
        row = by_address[address if address[0] != "=" else "'" + address]
        assert row[2] == str(WORDING_VERSION)
        made = {made.choice: made for made in SignUpChoice.objects.filter(sign_up__email=address)}
        assert set(made) == choices
        assert row[3:] == [made[choice].chosen_at.isoformat() if choice in made else "" for choice in CHOICES]
