"""✨ What a deployed environment needs of the application (ticket 26, docs/server-approach.md).

A deployed copy sits behind a proxy that ends TLS, and is checked from outside through /healthz. The settings that
turn this on come from the environment; tests/core/test_deployment_settings.py covers how they are read.
"""

import logging
import re

import pytest
from django.db import OperationalError

from config.logs import RedactLinks

from tests.journeys.test_contact_list import (  # noqa: F401  (participant is a fixture, used by name)
    JO,
    participant,
    save_contacts,
    with_a_contact_list,
)
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import (  # noqa: F401  (observer is a fixture, used by name)
    invitation_action,
    issue_link,
    observer,
)

FROM_THE_PROXY_OVER_HTTPS = {"X-Forwarded-Proto": "https"}


@pytest.fixture
def trusting_the_proxy(settings):
    """✨ As DJANGO_HTTPS sets things: the proxy's word is taken for whether a request came over HTTPS."""
    settings.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


@pytest.fixture
def behind_the_proxy(trusting_the_proxy, settings):
    """✨ The rest of what DJANGO_HTTPS sets: anything that did not come over HTTPS is sent there."""
    settings.SECURE_SSL_REDIRECT = True
    settings.SECURE_REDIRECT_EXEMPT = [r"^healthz$"]


# The health check


@pytest.mark.django_db
def test_the_health_check_reports_the_commit_it_was_built_from(client, settings):
    settings.ANVILLE_COMMIT = "0123abc"

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "commit": "0123abc"}


def test_the_health_check_fails_when_the_database_cannot_be_reached(client, monkeypatch):
    class NoDatabase:
        def cursor(self):
            raise OperationalError("connection refused")

    monkeypatch.setattr("config.health.connection", NoDatabase())

    response = client.get("/healthz")

    assert response.status_code == 503
    assert response.json()["status"] == "database unavailable"


@pytest.mark.django_db
def test_the_health_check_needs_nobody_signed_in_and_is_never_cached(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert "no-store" in response["Cache-Control"]


@pytest.mark.django_db
def test_the_health_check_answers_over_plain_http_behind_the_proxy(behind_the_proxy, client):
    # ✨ The cluster asks the pod directly, with no proxy in between to say the request was HTTPS.
    assert client.get("/healthz").status_code == 200


# Behind the proxy


@pytest.mark.django_db
def test_a_plain_http_request_is_sent_to_https(behind_the_proxy, client):
    response = client.get("/accounts/login/")

    assert response.status_code == 301
    assert response["Location"] == "https://testserver/accounts/login/"


@pytest.mark.django_db
def test_a_request_the_proxy_received_over_https_is_served(behind_the_proxy, client):
    assert client.get("/accounts/login/", headers=FROM_THE_PROXY_OVER_HTTPS).status_code == 200


@pytest.mark.django_db
def test_the_observers_cookie_is_marked_secure_behind_the_proxy(trusting_the_proxy, participant, observer):
    participant.defaults["HTTP_X_FORWARDED_PROTO"] = "https"
    save_contacts(participant, JO)
    link = issue_link_shown_over_https(participant, "Jo")

    started = observer.post(f"{link}start/", headers=FROM_THE_PROXY_OVER_HTTPS)

    assert started.status_code == 200
    assert started.cookies["observer"]["secure"] is True


@pytest.mark.django_db
def test_a_forwarded_header_is_not_trusted_without_the_proxy(participant, observer):
    # ✨ In development nothing sits in front, so anyone could send the header themselves.
    save_contacts(participant, JO)
    link = issue_link(participant, "Jo")

    started = observer.post(f"{link}start/", headers=FROM_THE_PROXY_OVER_HTTPS)

    assert started.status_code == 200
    assert not started.cookies["observer"]["secure"]


def issue_link_shown_over_https(client, name):
    """✨ As issue_link, where the page shows the link with the scheme the proxy reported.

    The test client says it is on port 80 whatever the scheme, so the link names that port. A real proxy passes the
    Host header on, which names none.
    """
    issued = client.post(invitation_action(client, name, "issue"), follow=True)
    assert issued.status_code == 200
    return re.search(r"https://testserver(?::80)?(/observe/[A-Za-z0-9_-]+/)", issued.content.decode()).group(1)


# What reaches the log


def test_an_error_is_logged_without_the_observers_secret():
    record = logging.LogRecord(
        "django.request", logging.ERROR, __file__, 1, "%s: %s", ("Internal Server Error", "/observe/s3cr3t-T0ken/start/"), None
    )

    assert RedactLinks().filter(record) is True
    assert record.getMessage() == "Internal Server Error: /observe/[redacted]/start/"


def test_an_error_is_logged_without_the_coachs_token():
    record = logging.LogRecord(
        "django.request", logging.ERROR, __file__, 1, "%s: %s", ("Internal Server Error", "/coaching/c0ach-T0ken/answer/"), None
    )

    assert RedactLinks().filter(record) is True
    assert record.getMessage() == "Internal Server Error: /coaching/[redacted]/answer/"
