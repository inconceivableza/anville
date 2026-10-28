# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The homepage's "Stay in touch" list (ticket 74, ADR 0023): one email field, its addresses kept in the app and
exported from the admin."""

import csv
import io
import re

import pytest
from django.utils import timezone

from engine.models import SignUp
from engine.stay_in_touch import NO_ADDRESS, NOT_AN_ADDRESS, TRAP, WORDING_VERSION

HTMX = {"HTTP_HX_REQUEST": "true"}


def stay_in_touch(page):
    """✨ The "Stay in touch" section of a page, or the section htmx sent back on its own."""
    found = re.search(r'<section\b[^>]*\bid="stay-in-touch".*?</section>', page, re.S)
    assert found, "no Stay in touch section"
    return found.group(0)


@pytest.mark.django_db
@pytest.mark.parametrize("headers", [{}, HTMX], ids=["without JavaScript", "with htmx"])
def test_subscribing_stores_the_address_its_time_and_the_wordings_version_and_thanks_in_place_of_the_form(
    client, headers
):
    before = timezone.now()

    response = client.post("/", {"email": " sam@example.com "}, **headers)

    assert response.status_code == 200
    stored = SignUp.objects.get()
    assert stored.email == "sam@example.com"
    assert before <= stored.signed_up_at <= timezone.now()
    assert stored.wording_version == WORDING_VERSION
    page = response.content.decode()
    shown = stay_in_touch(page)
    assert "<form" not in shown
    assert 'class="stay-thanks"' in shown
    if headers:
        assert "<main" not in page, "htmx is sent the section alone, not a new page"
    else:
        assert '<header class="panel hero"' in page, "without JavaScript the homepage comes back"


@pytest.mark.django_db
def test_a_repeat_address_in_any_case_gets_the_same_thanks_and_stores_nothing_new(client):
    client.post("/", {"email": "sam@example.com"})
    first = SignUp.objects.get()

    again = client.post("/", {"email": "Sam@Example.com"}, **HTMX)

    assert again.status_code == 200
    assert 'class="stay-thanks"' in stay_in_touch(again.content.decode())
    assert list(SignUp.objects.values_list("pk", "email", "signed_up_at")) == [
        (first.pk, "sam@example.com", first.signed_up_at)
    ]


@pytest.mark.django_db
def test_a_press_that_fills_the_hidden_field_is_thanked_and_stores_nothing(client):
    response = client.post("/", {"email": "bot@example.com", TRAP: "https://spam.example"})

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

    response = client.post("/", {"email": typed}, **headers)

    assert response.status_code == 400
    shown = stay_in_touch(response.content.decode())
    assert refusal in shown
    assert "<form" in shown
    assert f'value="{typed}"' in shown
    assert not SignUp.objects.exists()


@pytest.mark.django_db
def test_the_admin_lists_the_sign_ups_and_exports_them_as_csv_with_no_cell_read_as_a_formula(client, admin_user):
    """✨ The list is opened in a spreadsheet, where a cell beginning "=" would run as a formula; such an address is
    one mail can carry."""
    for email in ("sam@example.com", "=1+1@example.com"):
        client.post("/", {"email": email})
    client.force_login(admin_user)

    listed = client.get("/admin/engine/signup/").content.decode()
    exported = client.post(
        "/admin/engine/signup/",
        {"action": "export_as_csv", "_selected_action": list(SignUp.objects.values_list("pk", flat=True))},
    )

    assert "sam@example.com" in listed
    assert exported.status_code == 200
    assert exported["Content-Type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(exported.content.decode())))
    assert rows[0] == ["Email address", "Signed up at", "Wording version"]
    assert sorted(row[0] for row in rows[1:]) == ["'=1+1@example.com", "sam@example.com"]
    assert all(row[2] == str(WORDING_VERSION) for row in rows[1:])
