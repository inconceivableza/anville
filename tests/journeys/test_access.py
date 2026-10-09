# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import re

import pytest
from django.contrib.auth import get_user

from tests.journeys.pages import loads_the_built_stylesheet

PASSWORD = "correct-horse-battery-staple"


def require_the_code(settings):
    """✨ Turn the enrolment code on, as a deployment does from its environment, whatever the developer's `.env` says."""
    settings.ANVILLE_ENROLMENT_REQUIRED = True
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"


def sign_up(
    client, *, email="participant@example.com", display_name="Sam", enrolment_code="GRACE-2026", is_adult=True
):
    form = {
        "display_name": display_name,
        "email": email,
        "password1": PASSWORD,
        "password2": PASSWORD,
        "enrolment_code": enrolment_code,
    }
    # ✨ An unticked checkbox is left out of the form a browser sends, rather than sent empty.
    return client.post("/accounts/signup/", {**form, "is_adult": "on"} if is_adult else form)


@pytest.mark.django_db
def test_a_visitor_can_reach_the_login_page(client):
    response = client.get("/accounts/login/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_a_visitor_with_the_enrolment_code_can_sign_up(client, settings):
    require_the_code(settings)

    sign_up(client)

    participant = get_user(client)
    assert participant.is_authenticated
    assert participant.email == "participant@example.com"


@pytest.mark.django_db
def test_signing_up_leads_to_the_hub(client, settings):
    require_the_code(settings)

    response = sign_up(client)

    assert response.status_code == 302
    assert response.url == "/hub/"


@pytest.mark.django_db
def test_a_wrong_enrolment_code_is_refused(client, settings):
    require_the_code(settings)

    response = sign_up(client, enrolment_code="WRONG")

    assert not get_user(client).is_authenticated
    assert "That enrolment code is not recognised." in response.content.decode()


@pytest.mark.django_db
def test_a_missing_enrolment_code_is_refused(client, settings):
    require_the_code(settings)

    response = sign_up(client, enrolment_code="")

    assert not get_user(client).is_authenticated
    assert "Enter the enrolment code you were given." in response.content.decode()


@pytest.mark.django_db
def test_a_visitor_who_does_not_confirm_they_are_18_or_over_gets_no_account(client, settings, django_user_model):
    require_the_code(settings)

    response = sign_up(client, is_adult=False)

    assert not get_user(client).is_authenticated
    assert not django_user_model.objects.exists()
    assert "You need to be 18 or over to take part." in response.content.decode()


@pytest.mark.django_db
def test_sign_up_asks_for_an_18_or_over_confirmation_and_never_a_date_of_birth(client):
    page = client.get("/accounts/signup/").content.decode()

    assert re.search(r'<input type="checkbox" name="is_adult"[^>]*required', page)
    assert re.search(r">I am 18 or over</label>", page)
    assert page.index('name="password2"') < page.index('name="is_adult"'), "the last thing ticked before signing up"
    assert 'type="date"' not in page
    assert "birth" not in page.casefold()


@pytest.mark.django_db
def test_sign_in_offers_remember_me_in_sentence_case_and_without_a_colon(client):
    page = client.get("/accounts/login/").content.decode()

    assert re.search(r">Remember me</label>", page)


@pytest.mark.django_db
def test_text_a_visitor_typed_is_shown_back_escaped_and_unaltered(client, settings):
    require_the_code(settings)

    response = sign_up(client, enrolment_code='<script>alert("x")</script>')

    content = response.content.decode()
    assert '<script>alert("x")</script>' not in content
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in content


@pytest.mark.django_db
def test_a_participant_can_log_out_and_log_back_in(client, settings):
    require_the_code(settings)
    sign_up(client)

    client.post("/accounts/logout/")
    assert not get_user(client).is_authenticated

    client.post("/accounts/login/", {"login": "participant@example.com", "password": PASSWORD})
    assert get_user(client).email == "participant@example.com"


@pytest.mark.django_db
def test_signing_in_lands_on_the_hub(client, settings):
    require_the_code(settings)
    sign_up(client)
    client.post("/accounts/logout/")

    response = client.post("/accounts/login/", {"login": "participant@example.com", "password": PASSWORD})

    assert (response.status_code, response.url) == (302, "/hub/")


@pytest.mark.django_db
@pytest.mark.parametrize("address", ["/accounts/login/", "/accounts/signup/"])
def test_the_sign_in_and_sign_up_pages_load_the_built_stylesheet(client, address):
    assert loads_the_built_stylesheet(client.get(address).content.decode())


@pytest.mark.django_db
def test_the_sign_out_confirmation_loads_the_built_stylesheet(client, settings):
    require_the_code(settings)
    sign_up(client)

    assert loads_the_built_stylesheet(client.get("/accounts/logout/").content.decode())


@pytest.mark.django_db
def test_until_email_can_be_sent_password_reset_is_neither_offered_nor_reachable(client, mailoutbox):
    """✨ Temporary: ticket 28a replaces this with tests of the working flow once email delivery exists.

    Guards against an allauth upgrade quietly bringing back a link whose page crashes without a mail server.
    """
    assert "Forgot your password?" not in client.get("/accounts/login/").content.decode()
    assert client.post("/accounts/password/reset/", {"email": "participant@example.com"}).status_code == 404
    assert mailoutbox == []


@pytest.mark.django_db
def test_a_refused_sign_up_still_says_why_on_the_styled_page(client, settings):
    require_the_code(settings)

    page = sign_up(client, enrolment_code="WRONG").content.decode()

    assert loads_the_built_stylesheet(page)
    assert "That enrolment code is not recognised." in page


# Accounts: the email is the username, and a display name names the participant (ticket 37)


@pytest.mark.django_db
def test_an_email_already_in_use_is_refused_whatever_its_capitals(client, settings, django_user_model):
    require_the_code(settings)
    sign_up(client, email="sam@example.com")
    client.post("/accounts/logout/")

    sign_up(client, email="Sam@Example.com")

    assert not get_user(client).is_authenticated
    assert django_user_model.objects.count() == 1


@pytest.mark.django_db
def test_an_email_too_long_to_be_a_username_is_refused_on_the_form(client, settings, django_user_model):
    require_the_code(settings)
    too_long = "sam@" + ".".join(["a" * 50] * 3) + ".com"  # ✨ 160 characters; each part within an email's limits

    response = sign_up(client, email=too_long)

    assert response.status_code == 200
    assert not get_user(client).is_authenticated
    assert not django_user_model.objects.exists()


@pytest.mark.django_db
def test_with_the_code_off_sign_up_asks_for_none_and_admits_a_visitor_without_one(client, settings):
    settings.ANVILLE_ENROLMENT_REQUIRED = False
    settings.ANVILLE_ENROLMENT_CODE = ""

    page = client.get("/accounts/signup/").content.decode()
    sign_up(client, enrolment_code="")

    assert 'name="enrolment_code"' not in page
    assert get_user(client).is_authenticated


@pytest.mark.django_db
def test_a_new_account_takes_its_email_as_username_and_keeps_its_display_name_on_the_account(client, settings):
    require_the_code(settings)

    sign_up(client, email="sam.jones@example.com", display_name="Ayodele")

    participant = get_user(client)
    assert participant.username == "sam.jones@example.com"
    assert participant.account.display_name == "Ayodele"


@pytest.mark.django_db
@pytest.mark.parametrize("display_name", ["", "   "])
def test_sign_up_without_a_display_name_gets_no_account(client, settings, django_user_model, display_name):
    require_the_code(settings)

    sign_up(client, display_name=display_name)

    assert not get_user(client).is_authenticated
    assert not django_user_model.objects.exists()


@pytest.mark.django_db
def test_two_participants_may_share_a_display_name(client, settings, django_user_model):
    require_the_code(settings)

    sign_up(client, email="sam@example.com", display_name="Sam")
    client.post("/accounts/logout/")
    sign_up(client, email="another.sam@example.com", display_name="Sam")

    assert get_user(client).email == "another.sam@example.com"
    assert django_user_model.objects.count() == 2
