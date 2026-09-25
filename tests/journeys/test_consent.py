"""✨ Consent comes before the pathway (ADR 0004): it is its own act, never the enrolment code, and it
records the version of the text agreed to. Declining stores nothing beyond the account.
"""

import pytest
from django.utils import dateformat, timezone

from engine.models import Publication, Response
from tests.documents import pathway_document
from tests.journeys.pages import version_on
from tests.journeys.test_access import sign_up

CONSENT = "/consent/"


def give_consent(client):
    """✨ Agree to the consent text, sending the version of the text the page showed, as the browser does."""
    version = version_on(client.get(CONSENT).content.decode())
    return client.post(CONSENT, {"decision": "agree", **({"version": version} if version else {})})


def decline_consent(client):
    return client.post(CONSENT, {"decision": "decline"})


def answer(client, block_id, value):
    return client.post(f"/answers/{block_id}/", {"value": value, "version": Publication.current_version().pk})


@pytest.fixture
def signed_up(client, settings, load_pathway):
    """✨ A participant who has just signed up with the enrolment code and done nothing else."""
    settings.ANVILLE_ENROLMENT_CODE = "GRACE-2026"
    load_pathway(pathway_document())
    sign_up(client)
    return client


@pytest.mark.django_db
def test_enrolment_alone_never_counts_as_consent(signed_up):
    hub = signed_up.get("/")

    assert hub.status_code == 302
    assert hub.url == CONSENT
    answer(signed_up, "baseline-bible", "7")
    assert not Response.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "method, address",
    [
        ("get", "/"),
        ("get", "/sections/onboarding/"),
        ("get", "/results/strengths-sort/"),
        ("post", "/sections/onboarding/complete/"),
        ("post", "/sections/onboarding/reopen/"),
        ("post", "/answers/baseline-bible/"),
    ],
)
def test_every_page_of_the_pathway_waits_for_consent(signed_up, method, address):
    refused = getattr(signed_up, method)(address, {"value": "7", "version": Publication.current_version().pk})

    assert refused.status_code == 302
    assert refused.url == CONSENT
    assert not Response.objects.exists()


@pytest.mark.django_db
def test_the_consent_page_offers_agreeing_and_declining_as_separate_choices(signed_up):
    page = signed_up.get(CONSENT).content.decode()

    assert 'name="decision" value="agree"' in page
    assert 'name="decision" value="decline"' in page
    assert version_on(page) is not None


@pytest.mark.django_db
def test_agreeing_opens_the_pathway(signed_up):
    agreed = give_consent(signed_up)

    assert agreed.status_code == 303
    assert agreed.url == "/"
    assert "Test Pathway" in signed_up.get("/").content.decode()
    answer(signed_up, "baseline-bible", "7")
    assert Response.objects.get().answers == {"baseline-bible": 7}


@pytest.mark.django_db
def test_consent_is_recorded_with_the_version_of_the_text_and_when_it_was_given(signed_up):
    version = version_on(signed_up.get(CONSENT).content.decode())

    give_consent(signed_up)

    page = signed_up.get(CONSENT).content.decode()
    today = dateformat.format(timezone.localdate(), "j F Y")
    assert f"You agreed to version {version} of this text on {today}." in page


@pytest.mark.django_db
def test_agreeing_to_a_version_of_the_text_that_is_no_longer_current_is_refused(signed_up):
    refused = signed_up.post(CONSENT, {"decision": "agree", "version": "0"})

    assert refused.status_code == 400
    assert "The text has changed since you opened this page. Please read it again." in refused.content.decode()
    assert signed_up.get("/").url == CONSENT


@pytest.mark.django_db
def test_declining_stores_nothing_and_answering_stays_shut(signed_up):
    declined = decline_consent(signed_up)

    assert declined.status_code == 200
    assert "You have not given your consent, so nothing you write here will be stored." in declined.content.decode()
    answer(signed_up, "baseline-bible", "7")
    signed_up.post("/sections/onboarding/complete/")
    assert not Response.objects.exists()
    assert signed_up.get("/").url == CONSENT


@pytest.mark.django_db
def test_a_participant_who_declined_can_still_agree_later(signed_up):
    decline_consent(signed_up)

    give_consent(signed_up)

    assert "Test Pathway" in signed_up.get("/").content.decode()


@pytest.mark.django_db
def test_consent_needs_a_signed_in_participant(client):
    refused = client.get(CONSENT)

    assert refused.status_code == 302
    assert refused.url.startswith("/accounts/login/")
