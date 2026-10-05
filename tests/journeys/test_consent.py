"""✨ Consent comes before the pathway (ADR 0004): it is its own act, never the enrolment code, and it
records the version of the text agreed to. Declining stores nothing beyond the account.
"""

import pytest
from django.utils import dateformat, timezone

from access.models import Consent
from engine.models import Publication, Response
from tests.documents import pathway_document
from tests.journeys.pages import version_on
from tests.journeys.test_access import require_the_code, sign_up

CONSENT = "/consent/"


def give_consent(client):
    """✨ Agree to the consent text, sending the version of the text the page showed, as the browser does."""
    version = version_on(client.get(CONSENT).content.decode())
    return client.post(CONSENT, {"decision": "agree", **({"version": version} if version else {})})


def decline_consent(client):
    return client.post(CONSENT, {"decision": "decline"})


def withdraw_consent(client):
    return client.post(CONSENT, {"decision": "withdraw"})


def answer(client, block_id, value):
    return client.post(f"/answers/{block_id}/", {"value": value, "version": Publication.current_version().pk})


@pytest.fixture
def signed_up(client, settings, load_pathway):
    """✨ A participant who has just signed up with the enrolment code and done nothing else."""
    require_the_code(settings)
    load_pathway(pathway_document())
    sign_up(client)
    return client


@pytest.mark.django_db
def test_enrolment_alone_never_counts_as_consent(signed_up):
    hub = signed_up.get("/hub/")

    assert hub.status_code == 302
    assert hub.url == CONSENT
    answer(signed_up, "baseline-bible", "7")
    assert not Response.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "method, address",
    [
        ("get", "/hub/"),
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

    assert agreed.status_code == 303  # ✨ where it leads is pinned by the tests after this one
    assert "Test Pathway" in signed_up.get("/hub/").content.decode()
    answer(signed_up, "baseline-bible", "7")
    assert Response.objects.get().answers == {"baseline-bible": 7}


@pytest.mark.django_db
def test_consent_is_recorded_with_the_version_of_the_text_and_when_it_was_given(signed_up):
    version = version_on(signed_up.get(CONSENT).content.decode())

    give_consent(signed_up)

    page = signed_up.get(CONSENT).content.decode()
    assert f"You agreed to version {version} of this text on {today()}." in page


@pytest.mark.django_db
def test_agreeing_to_a_version_of_the_text_that_is_no_longer_current_is_refused(signed_up):
    refused = signed_up.post(CONSENT, {"decision": "agree", "version": "0"})

    assert refused.status_code == 400
    assert "The text has changed since you opened this page. Please read it again." in refused.content.decode()
    assert signed_up.get("/hub/").url == CONSENT


@pytest.mark.django_db
def test_declining_stores_nothing_and_answering_stays_shut(signed_up):
    declined = decline_consent(signed_up)

    assert declined.status_code == 200
    assert "You have not given your consent, so nothing you write here will be stored." in declined.content.decode()
    answer(signed_up, "baseline-bible", "7")
    signed_up.post("/sections/onboarding/complete/")
    assert not Response.objects.exists()
    assert not Consent.objects.exists(), "not even the decision to decline is recorded"
    assert signed_up.get("/hub/").url == CONSENT


@pytest.mark.django_db
def test_a_participant_who_declined_can_still_agree_later(signed_up):
    decline_consent(signed_up)

    give_consent(signed_up)

    assert "Test Pathway" in signed_up.get("/hub/").content.decode()


@pytest.fixture
def consented(signed_up):
    give_consent(signed_up)
    return signed_up


def today():
    return dateformat.format(timezone.localdate(), "j F Y")


def where_agreeing_leads(client):
    """✨ The page the browser ends up on after agreeing, following every redirect."""
    return client.get(give_consent(client).url, follow=True).request["PATH_INFO"]


@pytest.mark.django_db
def test_agreeing_for_the_first_time_leads_straight_to_the_first_step(signed_up):
    """✨ As the prototype goes from its account screen straight into onboarding, without the hub between."""
    assert where_agreeing_leads(signed_up) == "/sections/onboarding/"


@pytest.mark.django_db
def test_agreeing_again_once_started_leads_to_the_hub(consented):
    answer(consented, "baseline-bible", "7")
    withdraw_consent(consented)

    assert where_agreeing_leads(consented) == "/hub/"


@pytest.mark.django_db
def test_agreeing_with_nothing_to_begin_leads_to_the_hub(signed_up, load_pathway):
    document = pathway_document()
    for section in document["content"]["sections"]:
        section["blocks"] = []
        section.pop("gate", None)
    load_pathway(document)

    assert where_agreeing_leads(signed_up) == "/hub/"


@pytest.mark.django_db
def test_the_hub_leads_to_the_consent_page(consented):
    assert f'href="{CONSENT}"' in consented.get("/hub/").content.decode()


@pytest.mark.django_db
def test_withdrawing_is_offered_only_once_consent_has_been_given(signed_up):
    assert 'value="withdraw"' not in signed_up.get(CONSENT).content.decode()

    give_consent(signed_up)

    assert 'name="decision" value="withdraw"' in signed_up.get(CONSENT).content.decode()


@pytest.mark.django_db
def test_withdrawing_consent_shuts_the_pathway_and_stores_no_further_answer(consented):
    answer(consented, "baseline-bible", "7")

    withdrawn = withdraw_consent(consented)

    assert withdrawn.status_code == 303
    assert withdrawn.url == CONSENT
    assert consented.get("/hub/").url == CONSENT
    answer(consented, "baseline-bible", "3")
    assert Response.objects.get().answers == {"baseline-bible": 7}


@pytest.mark.django_db
def test_a_withdrawal_is_shown_with_its_date_and_consent_can_be_given_again(consented):
    withdraw_consent(consented)

    page = consented.get(CONSENT).content.decode()
    assert f"You withdrew your consent on {today()}." in page
    assert 'name="decision" value="agree"' in page
    give_consent(consented)
    assert "Test Pathway" in consented.get("/hub/").content.decode()


@pytest.mark.django_db
def test_withdrawing_keeps_the_answers_already_stored(consented):
    """✨ For now. What withdrawal does to stored answers is open (spec, "Legalities are parked"); until it is
    decided, withdrawing shuts the pathway and deletes nothing, so agreeing again finds every answer."""
    answer(consented, "baseline-bible", "7")
    withdraw_consent(consented)

    give_consent(consented)

    assert Response.objects.get().answers == {"baseline-bible": 7}


@pytest.mark.django_db
def test_a_new_version_of_the_consent_text_asks_again(consented, monkeypatch):
    """✨ Stands in for a release that raises the version beside a changed text."""
    monkeypatch.setattr("access.consent.CONSENT_TEXT_VERSION", 2)

    assert consented.get("/hub/").url == CONSENT
    page = consented.get(CONSENT).content.decode()
    assert "The text has changed since you agreed to version 1. Please read it again." in page
    assert version_on(page) == "2"
    give_consent(consented)
    assert "Test Pathway" in consented.get("/hub/").content.decode()


@pytest.mark.django_db
def test_consent_needs_a_signed_in_participant(client):
    refused = client.get(CONSENT)

    assert refused.status_code == 302
    assert refused.url.startswith("/accounts/login/")
