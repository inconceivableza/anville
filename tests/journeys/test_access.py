import pytest
from django.contrib.auth import get_user

PASSWORD = "correct-horse-battery-staple"


def sign_up(client, *, email="participant@example.com", enrolment_code="GRACE-2026"):
    return client.post(
        "/accounts/signup/",
        {
            "email": email,
            "password1": PASSWORD,
            "password2": PASSWORD,
            "enrolment_code": enrolment_code,
        },
    )


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
def test_a_participant_can_log_out_and_log_back_in(client, settings):
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"
    sign_up(client)

    client.post("/accounts/logout/")
    assert not get_user(client).is_authenticated

    client.post("/accounts/login/", {"login": "participant@example.com", "password": PASSWORD})
    assert get_user(client).email == "participant@example.com"
