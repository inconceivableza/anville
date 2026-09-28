import re

import pytest
from django.contrib.auth import get_user

from tests.journeys.pages import loads_the_built_stylesheet

PASSWORD = "correct-horse-battery-staple"


def sign_up(client, *, email="participant@example.com", enrolment_code="GRACE-2026", is_adult=True):
    form = {
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
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"

    sign_up(client)

    participant = get_user(client)
    assert participant.is_authenticated
    assert participant.email == "participant@example.com"


@pytest.mark.django_db
def test_signing_up_leads_to_the_hub(client, settings):
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"

    response = sign_up(client)

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_a_wrong_enrolment_code_is_refused(client, settings):
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"

    response = sign_up(client, enrolment_code="WRONG")

    assert not get_user(client).is_authenticated
    assert "That enrolment code is not recognised." in response.content.decode()


@pytest.mark.django_db
def test_a_missing_enrolment_code_is_refused(client, settings):
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"

    response = sign_up(client, enrolment_code="")

    assert not get_user(client).is_authenticated
    assert "Enter the enrolment code you were given." in response.content.decode()


@pytest.mark.django_db
def test_a_visitor_who_does_not_confirm_they_are_18_or_over_gets_no_account(client, settings, django_user_model):
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"

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
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"

    response = sign_up(client, enrolment_code='<script>alert("x")</script>')

    content = response.content.decode()
    assert '<script>alert("x")</script>' not in content
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in content


@pytest.mark.django_db
def test_a_participant_can_log_out_and_log_back_in(client, settings):
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"
    sign_up(client)

    client.post("/accounts/logout/")
    assert not get_user(client).is_authenticated

    client.post("/accounts/login/", {"login": "participant@example.com", "password": PASSWORD})
    assert get_user(client).email == "participant@example.com"


@pytest.mark.django_db
@pytest.mark.parametrize("address", ["/accounts/login/", "/accounts/signup/"])
def test_the_sign_in_and_sign_up_pages_load_the_built_stylesheet(client, address):
    assert loads_the_built_stylesheet(client.get(address).content.decode())


@pytest.mark.django_db
def test_the_sign_out_confirmation_loads_the_built_stylesheet(client, settings):
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"
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
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"

    page = sign_up(client, enrolment_code="WRONG").content.decode()

    assert loads_the_built_stylesheet(page)
    assert "That enrolment code is not recognised." in page
