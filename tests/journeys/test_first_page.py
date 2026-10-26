# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The wizard's first page (ADR 0021): the engine's, before the pathway's own wizard pages. The participant's first
name, "I am 18 or over" and consent, all required, and nothing of the pathway is shown or stored before it is passed.
"""

import re
from datetime import timedelta
from html import unescape

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from access.consent import current_text_version, withdraw
from access.first_page_form import FirstPageForm
from access.models import Account, Consent
from tests.documents import pathway_document
from tests.journeys.pages import version_on
from tests.journeys.test_access import require_the_code, sign_up

FIRST_PAGE = "/about-you/"
CONSENT = "/consent/"


def name_on(page):
    """✨ The first name the page fills in, as the browser would send it back untouched."""
    return unescape(re.search(r'name="display_name"[^>]*value="([^"]*)"', page).group(1))


def pass_the_first_page(client, **given):
    """✨ Continue from the first page with the name it fills in and both ticks, as a browser sends them, an unticked box
    left out; `given` replaces any of them, None leaving it out."""
    page = client.get(FIRST_PAGE).content.decode()
    form = {"display_name": name_on(page), "is_adult": "on", "consents": "on", "version": version_on(page)} | given
    return client.post(FIRST_PAGE, {key: value for key, value in form.items() if value is not None})


def refusal(field):
    return FirstPageForm.base_fields[field].error_messages["required"]


@pytest.fixture
def signed_up(client, settings, load_pathway):
    """✨ A participant who has just signed up and done nothing else."""
    require_the_code(settings)
    load_pathway(pathway_document())
    sign_up(client)
    return client


# ✨ That every page of the pathway leads here until this page is passed, storing nothing, is test_consent.py's
# test_every_page_of_the_pathway_waits_for_consent.


@pytest.mark.django_db
@pytest.mark.parametrize(
    "left_out, field",
    [({"display_name": "  "}, "display_name"), ({"is_adult": None}, "is_adult"), ({"consents": None}, "consents")],
    ids=["no name", "not 18 or over", "no consent"],
)
def test_continue_without_a_name_or_either_tick_is_refused_and_stores_nothing(signed_up, left_out, field):
    unpressed = signed_up.get(FIRST_PAGE).content.decode()

    refused = pass_the_first_page(signed_up, **left_out)

    assert refusal(field) not in unpressed, "a refusal shows only after the press"
    assert refused.status_code == 400
    assert refusal(field) in unescape(refused.content.decode())
    assert not Consent.objects.exists()
    assert Account.objects.get().adult_confirmed_at is None
    assert Account.objects.get().display_name == "Sam"
    assert signed_up.get("/hub/").url == FIRST_PAGE


@pytest.mark.django_db
def test_passing_keeps_the_name_when_18_or_over_was_ticked_and_consent_then_goes_on_to_the_first_step(signed_up):
    assert name_on(signed_up.get(FIRST_PAGE).content.decode()) == "Sam", "filled in from the account"
    before = timezone.now()

    passed = pass_the_first_page(signed_up, display_name="Samuel")

    account = Account.objects.get()
    assert account.display_name == "Samuel"
    assert before <= account.adult_confirmed_at <= timezone.now()
    assert Consent.objects.get().text_version == current_text_version()
    assert passed.status_code == 303
    assert signed_up.get(passed.url, follow=True).request["PATH_INFO"] == "/sections/onboarding/"


@pytest.mark.django_db
def test_a_new_text_version_is_refused_rather_than_agreed_to_unread(signed_up):
    refused = pass_the_first_page(signed_up, version=str(current_text_version() - 1))

    assert refused.status_code == 400
    assert not Consent.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("decision", ["agree", "decline"])
def test_the_consent_page_sends_anyone_who_has_not_passed_the_first_page_to_it_and_stores_nothing(signed_up, decision):
    """✨ Agreeing there would step round "I am 18 or over"."""
    sent = signed_up.post(CONSENT, {"decision": decision, "version": str(current_text_version())})

    assert sent.url == FIRST_PAGE
    assert signed_up.get(CONSENT).url == FIRST_PAGE
    assert not Consent.objects.exists()


@pytest.fixture
def passed(signed_up):
    pass_the_first_page(signed_up)
    return signed_up


@pytest.mark.django_db
@pytest.mark.parametrize("how", ["withdrawn", "out of date"])
def test_once_passed_consent_is_asked_again_on_the_consent_page_and_never_the_first_page(passed, how):
    participant = get_user_model().objects.get()
    if how == "withdrawn":
        withdraw(participant)
    else:
        Consent.objects.update(text_version=current_text_version() - 1)

    assert passed.get("/hub/").url == CONSENT
    assert passed.get(FIRST_PAGE).url == "/hub/"
    assert 'name="decision" value="agree"' in passed.get(CONSENT).content.decode()


@pytest.mark.django_db
def test_an_account_that_consented_before_the_first_page_existed_is_asked_on_the_consent_page(signed_up):
    """✨ It ticked 18 or over at sign-up, where the time was not kept."""
    participant = get_user_model().objects.get()
    Consent.objects.create(participant=participant, text_version=2, given_at=timezone.now() - timedelta(days=1))

    assert signed_up.get("/hub/").url == CONSENT
