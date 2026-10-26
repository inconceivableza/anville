# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import re
import time
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.contrib.auth import get_user
from django.utils.html import escape

from access.adapter import SocialAccountAdapter
from engine.models import Publication, Response
from tests.documents import pathway_document
from tests.journeys.pages import loads_the_built_stylesheet

PASSWORD = "correct-horse-battery-staple"


def require_the_code(settings):
    """✨ Turn the enrolment code on, as a deployment does from its environment, whatever the developer's `.env` says."""
    settings.ANVILLE_ENROLMENT_REQUIRED = True
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"


def sign_up(client, *, email="participant@example.com", display_name="Sam", enrolment_code="GRACE-2026"):
    form = {
        "display_name": display_name,
        "email": email,
        "password1": PASSWORD,
        "password2": PASSWORD,
        "enrolment_code": enrolment_code,
    }
    return client.post("/accounts/signup/", form)


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
def test_sign_up_keeps_the_first_name_and_leaves_18_or_over_to_the_wizard_with_never_a_date_of_birth(client):
    """✨ "I am 18 or over" is asked on the wizard's first page, after the account is made (ADR 0021)."""
    page = client.get("/accounts/signup/").content.decode()

    assert 'name="display_name"' in page
    assert 'name="is_adult"' not in page
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
def test_sign_in_offers_a_password_reset_whose_pages_can_be_reached(client):
    sign_in_page = client.get("/accounts/login/").content.decode()

    assert 'href="/accounts/password/reset/"' in sign_in_page
    assert client.get("/accounts/password/reset/").status_code == 200
    assert client.get("/accounts/password/reset/done/").status_code == 200


@pytest.mark.django_db
def test_a_participant_resets_a_forgotten_password_by_the_emailed_link_and_signs_in_with_it(
    client, settings, mailoutbox
):
    require_the_code(settings)
    sign_up(client)
    client.logout()

    client.post("/accounts/password/reset/", {"email": "participant@example.com"})
    [email] = mailoutbox
    assert email.to == ["participant@example.com"]
    # ✨ allauth's link leads to a page that keeps the key in the session and redirects to the form, so the key is not
    # left in the address the form is posted to.
    link = re.search(r"http://testserver(/accounts/password/reset/key/\S+/)", email.body).group(1)
    form = client.get(link, follow=True)
    new_password = "a-new-and-different-passphrase"
    client.post(form.redirect_chain[-1][0], {"password1": new_password, "password2": new_password})

    assert not client.login(username="participant@example.com", password=PASSWORD)
    client.post("/accounts/login/", {"login": "participant@example.com", "password": new_password})
    assert get_user(client).email == "participant@example.com"


@pytest.mark.django_db
def test_signing_in_and_out_leaves_no_message_for_a_later_page(client, settings):
    """✨ The hub and the homepage, where signing in and out lead, show no messages, so a message added for them waited
    and showed on the next account page instead, such as sign-up after "Begin my journey" (hand-check finding)."""
    require_the_code(settings)
    sign_up(client)
    client.post("/accounts/logout/")
    client.post("/accounts/login/", {"login": "participant@example.com", "password": PASSWORD})
    client.post("/accounts/logout/")

    page = client.get("/accounts/signup/").content.decode()

    assert "Successfully signed in" not in page
    assert "You have signed out." not in page


@pytest.mark.django_db
def test_a_reset_password_is_confirmed_on_the_page_the_reset_leads_to(client, settings, mailoutbox):
    require_the_code(settings)
    sign_up(client)
    client.logout()
    client.post("/accounts/password/reset/", {"email": "participant@example.com"})
    [email] = mailoutbox
    link = re.search(r"http://testserver(/accounts/password/reset/key/\S+/)", email.body).group(1)
    form = client.get(link, follow=True)
    new_password = "a-new-and-different-passphrase"

    done = client.post(
        form.redirect_chain[-1][0], {"password1": new_password, "password2": new_password}, follow=True
    )

    assert "Password successfully changed." in done.content.decode()
    assert "Password successfully changed." not in client.get("/accounts/login/").content.decode()


@pytest.mark.django_db
def test_asking_to_reset_an_unknown_address_looks_the_same_and_sends_nothing(client, settings, mailoutbox):
    require_the_code(settings)
    sign_up(client)
    client.logout()

    known = client.post("/accounts/password/reset/", {"email": "participant@example.com"}, follow=True)
    unknown = client.post("/accounts/password/reset/", {"email": "nobody@example.com"}, follow=True)

    assert unknown.redirect_chain == known.redirect_chain
    assert unknown.content == known.content
    assert [email.to for email in mailoutbox] == [["participant@example.com"]]


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


# Google sign-in (ticket 28b). Google's side is faked at the one call that leaves Anville: exchanging the code it
# hands back for the participant's details.

GOOGLE_CLIENT_ID = "anville-test.apps.googleusercontent.com"
GOOGLE_LOGIN = "/accounts/google/login/"
GOOGLE_CALLBACK = "/accounts/google/login/callback/"


def give_google_a_client(settings, *, client_id=GOOGLE_CLIENT_ID, secret="test-secret"):
    settings.ANVILLE_GOOGLE_CLIENT_ID = client_id
    settings.ANVILLE_GOOGLE_CLIENT_SECRET = secret


def offers_google(page):
    return f'action="{GOOGLE_LOGIN}' in page


def come_back_from_google(client, *, email="sam.google@example.com", **names):
    """✨ Press the Google button, then return to the callback as Google would, with the participant's details in a
    token Anville fetched itself (so, as allauth allows, its signature is not checked). `names` replaces the given
    name Google sends: `given_name` and `name`, either None to leave it out."""
    to_google = client.post(GOOGLE_LOGIN)
    state = parse_qs(urlparse(to_google.url).query)["state"][0]
    claims = {
        "iss": "https://accounts.google.com",
        "aud": GOOGLE_CLIENT_ID,
        "sub": "google-user-1",
        "email": email,
        "email_verified": True,
        "given_name": "Sam",
        "exp": int(time.time()) + 600,
        "iat": int(time.time()),
    }
    claims.update(names)
    claims = {key: value for key, value in claims.items() if value is not None}
    token = {"access_token": "access", "id_token": jwt.encode(claims, "a key Anville never checks, long enough", algorithm="HS256")}
    with patch.object(OAuth2Client, "get_access_token", return_value=token):
        return client.get(GOOGLE_CALLBACK, {"code": "from-google", "state": state})


def finish_google_sign_up(client, *, email="sam.google@example.com", enrolment_code="GRACE-2026"):
    form = {"display_name": "Sam", "email": email, "enrolment_code": enrolment_code}
    return client.post("/accounts/3rdparty/signup/", form)


@pytest.mark.django_db
@pytest.mark.parametrize("client_id, secret", [("", ""), (GOOGLE_CLIENT_ID, ""), ("", "test-secret")])
def test_without_the_whole_client_pair_google_is_neither_offered_nor_reachable(client, settings, client_id, secret):
    give_google_a_client(settings, client_id=client_id, secret=secret)

    assert not offers_google(client.get("/accounts/login/").content.decode())
    assert not offers_google(client.get("/accounts/signup/").content.decode())
    assert client.post(GOOGLE_LOGIN).status_code == 404
    assert client.get(GOOGLE_CALLBACK, {"code": "from-google", "state": "any"}).status_code == 404
    assert client.post("/accounts/google/login/token/").status_code == 404


@pytest.mark.django_db
def test_with_the_client_pair_set_google_is_offered_and_a_google_sign_up_makes_an_account(client, settings):
    require_the_code(settings)
    give_google_a_client(settings)

    assert offers_google(client.get("/accounts/login/").content.decode())
    assert offers_google(client.get("/accounts/signup/").content.decode())
    come_back_from_google(client)
    finish_google_sign_up(client)

    participant = get_user(client)
    assert participant.is_authenticated
    assert participant.email == "sam.google@example.com"
    assert participant.username == "sam.google@example.com"
    assert participant.account.display_name == "Sam"


@pytest.mark.django_db
def test_google_sign_ups_confirming_page_is_in_our_wording_not_allauths(client, settings):
    """✨ allauth's stock sentence names the site by its `Site` record, which no deployment sets (ticket 53c)."""
    require_the_code(settings)
    give_google_a_client(settings)

    confirming = client.get(come_back_from_google(client).url)

    assert confirming.status_code == 200
    assert "You are about to use your Google account to login to" not in confirming.content.decode()


@pytest.mark.django_db
def test_a_google_sign_up_without_the_enrolment_code_makes_no_account(client, settings, django_user_model):
    require_the_code(settings)
    give_google_a_client(settings)

    come_back_from_google(client)
    finish_google_sign_up(client, enrolment_code="")

    assert not get_user(client).is_authenticated
    assert not django_user_model.objects.exists()


@pytest.mark.django_db
def test_google_never_signs_in_to_an_account_already_made_with_its_address(client, settings, django_user_model):
    """✨ Not on the agreed list: added because, broken, anyone holding a Google account with a participant's address
    would be let into that participant's answers."""
    require_the_code(settings)
    give_google_a_client(settings)
    sign_up(client, email="sam.google@example.com")
    client.post("/accounts/logout/")

    come_back_from_google(client)
    finish_google_sign_up(client)

    assert not get_user(client).is_authenticated
    assert django_user_model.objects.count() == 1


# Google sign-up keeps Google's address, always asks which Google account, and says what to do when refused (ticket 77)


@pytest.mark.django_db
def test_a_google_sign_up_sending_another_address_cannot_step_round_a_password_account_at_googles(
    client, settings, django_user_model
):
    require_the_code(settings)
    give_google_a_client(settings)
    sign_up(client, email="sam.google@example.com")
    client.post("/accounts/logout/")

    come_back_from_google(client, email="sam.google@example.com")
    finish_google_sign_up(client, email="someone.else@example.com")

    assert not get_user(client).is_authenticated
    assert django_user_model.objects.count() == 1


@pytest.mark.django_db
def test_a_google_sign_up_sending_another_address_makes_no_account_at_either(client, settings, django_user_model):
    require_the_code(settings)
    give_google_a_client(settings)

    come_back_from_google(client, email="sam.google@example.com")
    finish_google_sign_up(client, email="someone.else@example.com")

    assert not get_user(client).is_authenticated
    assert not django_user_model.objects.exists()


@pytest.mark.django_db
def test_continue_with_google_always_opens_googles_account_chooser(client, settings):
    give_google_a_client(settings)

    to_google = client.post(GOOGLE_LOGIN)

    assert parse_qs(urlparse(to_google.url).query)["prompt"] == ["select_account"]


@pytest.mark.django_db
def test_refusing_an_address_with_a_password_account_sends_the_person_to_sign_in_or_reset(client, settings):
    require_the_code(settings)
    give_google_a_client(settings)
    sign_up(client, email="sam.google@example.com")
    client.post("/accounts/logout/")

    come_back_from_google(client)
    page = finish_google_sign_up(client).content.decode()

    assert escape(SocialAccountAdapter.error_messages["email_taken"]) in page
    assert 'href="/accounts/login/"' in page
    assert 'href="/accounts/password/reset/"' in page


@pytest.mark.django_db
def test_the_google_sign_up_form_shows_googles_address_read_only(client, settings):
    require_the_code(settings)
    give_google_a_client(settings)

    page = client.get(come_back_from_google(client).url).content.decode()

    email_field = re.search(r'<input[^>]*name="email"[^>]*>', page).group()
    assert 'value="sam.google@example.com"' in email_field
    assert "readonly" in email_field


@pytest.mark.django_db
def test_a_new_google_account_meets_the_wizards_first_page_before_any_answer_is_stored(client, settings, load_pathway):
    """✨ The first page asks for consent, beside "I am 18 or over" (ADR 0021)."""
    require_the_code(settings)
    give_google_a_client(settings)
    load_pathway(pathway_document())
    come_back_from_google(client)
    finish_google_sign_up(client)

    hub = client.get("/hub/")
    client.post("/answers/baseline-bible/", {"value": "7", "version": Publication.current_version().pk})

    assert (hub.status_code, hub.url) == (302, "/about-you/")
    assert not Response.objects.exists()


# A Google sign-up goes straight in (ticket 93, ADR 0021)


def leave_the_code_off(settings):
    settings.ANVILLE_ENROLMENT_REQUIRED = False


@pytest.mark.django_db
def test_with_the_code_off_coming_back_from_google_makes_the_account_at_once_and_lands_on_the_wizards_first_page(
    client, settings, django_user_model, load_pathway
):
    leave_the_code_off(settings)
    give_google_a_client(settings)
    load_pathway(pathway_document())

    landed = client.get(come_back_from_google(client).url, follow=True)

    assert get_user(client).email == "sam.google@example.com"
    assert django_user_model.objects.count() == 1
    assert landed.redirect_chain[-1][0] == "/about-you/"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "given_name, name, first_name",
    [
        ("Sam", "Sam Okafor", "Sam"),
        (None, "Sam Okafor", "Sam Okafor"),
        (None, None, "sam.google"),
        ("  ", "", "sam.google"),
    ],
)
def test_a_google_sign_up_takes_googles_given_name_else_its_full_name_else_the_email_before_the_at(
    client, settings, given_name, name, first_name
):
    leave_the_code_off(settings)
    give_google_a_client(settings)

    client.get(come_back_from_google(client, given_name=given_name, name=name).url)

    assert get_user(client).account.display_name == first_name


@pytest.mark.django_db
def test_where_the_code_is_required_a_google_sign_up_asks_only_for_the_code_then_lands_on_the_wizards_first_page(
    client, settings, load_pathway
):
    require_the_code(settings)
    give_google_a_client(settings)
    load_pathway(pathway_document())

    form = client.get(come_back_from_google(client).url).content.decode()
    asked = {
        re.search(r'name="([^"]+)"', field).group(1)
        for field in re.findall(r"<input[^>]*>", form)
        if 'type="hidden"' not in field and "readonly" not in field
    }
    form_sent = {"email": "sam.google@example.com", "enrolment_code": "GRACE-2026"}  # ✨ a read-only box still sends
    landed = client.post("/accounts/3rdparty/signup/", form_sent, follow=True)

    assert asked == {"enrolment_code"}
    assert landed.redirect_chain[-1][0] == "/about-you/"
    assert get_user(client).account.display_name == "Sam"


@pytest.mark.django_db
def test_coming_back_from_google_with_an_address_that_has_a_password_account_is_refused_on_arrival(
    client, settings, django_user_model
):
    """✨ With nothing left to fill in, the refusal ticket 77 settled is shown at once, not after "Sign up"."""
    leave_the_code_off(settings)
    give_google_a_client(settings)
    sign_up(client, email="sam.google@example.com")
    client.post("/accounts/logout/")

    page = client.get(come_back_from_google(client).url).content.decode()

    assert escape(SocialAccountAdapter.error_messages["email_taken"]) in page
    assert 'href="/accounts/login/"' in page
    assert 'href="/accounts/password/reset/"' in page
    assert not get_user(client).is_authenticated
    assert django_user_model.objects.count() == 1


@pytest.mark.django_db
def test_a_participant_who_signed_up_with_google_signs_straight_in_with_it(client, settings, django_user_model):
    leave_the_code_off(settings)
    give_google_a_client(settings)
    client.get(come_back_from_google(client).url)
    client.post("/accounts/logout/")

    signed_in = come_back_from_google(client)

    assert signed_in.url == "/hub/"
    assert get_user(client).email == "sam.google@example.com"
    assert django_user_model.objects.count() == 1
