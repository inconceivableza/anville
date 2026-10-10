# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import pytest

from access.models import Account
from engine.models import Response
from tests.documents import pathway_document
from tests.journeys.test_access import require_the_code, sign_up
from tests.journeys.test_consent import give_consent


def onboarding_pathway():
    document = pathway_document()
    onboarding = document["content"]["sections"][0]
    onboarding["blocks"].insert(
        0,
        {
            "id": "reason",
            "type": "single_select",
            "prompt": "What’s bringing you here?",
            "options": [
                {"id": "exploring", "label": "Exploring my calling"},
                {"id": "changing", "label": "Thinking about a change"},
            ],
        },
    )
    onboarding["blocks"].extend(
        {
            "id": f"bl-{name}",
            "type": "agreement_scale",
            "prompt": f"Baseline statement {name}",
            "min_label": "Not at all",
            "max_label": "Completely",
        }
        for name in ("bible", "gifts", "call", "plan", "peace")
    )
    return document


@pytest.fixture
def new_participant(client, settings, load_pathway):
    require_the_code(settings)
    load_pathway(onboarding_pathway())
    sign_up(client)
    give_consent(client)
    return client


@pytest.mark.django_db
def test_a_new_participant_is_sent_through_onboarding_after_consent(new_participant):
    response = new_participant.get("/hub/")

    assert (response.status_code, response.url) == (302, "/onboarding/")
    page = new_participant.get(response.url).content.decode()
    assert "Step 1 of 4" in page
    assert "What’s bringing you here?" in page
    assert "Exploring my calling" in page


@pytest.mark.django_db
def test_the_reason_and_all_five_authored_scales_are_saved_as_pathway_answers(new_participant):
    reason = new_participant.post("/onboarding/", {"step": "0", "action": "continue", "reason": "exploring"})

    assert (reason.status_code, reason.url) == (303, "/onboarding/?step=1")
    response = Response.objects.get()
    assert response.answers["reason"] == "exploring"
    assert Account.objects.get().reason == "exploring"

    baseline = new_participant.post(
        "/onboarding/",
        {
            "step": "1",
            "action": "continue",
            "bl-bible": "2",
            "bl-gifts": "4",
            "bl-call": "6",
            "bl-plan": "8",
            "bl-peace": "10",
        },
    )

    assert (baseline.status_code, baseline.url) == (303, "/onboarding/?step=2")
    response.refresh_from_db()
    assert [
        response.answers[f"bl-{name}"] for name in ("bible", "gifts", "call", "plan", "peace")
    ] == [2, 4, 6, 8, 10]
    page = new_participant.get(baseline.url).content.decode()
    assert "Baseline statement peace" in page
    assert 'type="range"' in page


@pytest.mark.django_db
def test_path_and_reminder_are_saved_before_the_hub_opens(new_participant):
    new_participant.post("/onboarding/", {"step": "0", "action": "continue", "reason": "exploring"})
    new_participant.post(
        "/onboarding/",
        {
            "step": "1",
            "action": "continue",
            **{f"bl-{name}": "5" for name in ("bible", "gifts", "call", "plan", "peace")},
        },
    )
    path = new_participant.post("/onboarding/", {"step": "2", "action": "continue", "path": "paper"})

    assert (path.status_code, path.url) == (303, "/onboarding/?step=3")
    account = Account.objects.get()
    assert account.path == "paper"
    assert not account.onboarding_completed

    saved = new_participant.post(
        "/onboarding/", {"step": "3", "action": "continue", "remind": "on"}
    )

    assert (saved.status_code, saved.url) == (303, "/hub/")
    account.refresh_from_db()
    assert account.remind
    assert account.onboarding_completed
    assert new_participant.get("/hub/").status_code == 200


@pytest.mark.django_db
def test_an_invalid_reason_is_not_saved(new_participant):
    invalid_reason = new_participant.post(
        "/onboarding/", {"step": "0", "action": "continue", "reason": "not-an-option"}
    )

    assert invalid_reason.status_code == 400
    assert Account.objects.get().reason == ""
    assert not Response.objects.exists()


@pytest.mark.django_db
def test_an_invalid_path_is_not_saved(new_participant):
    new_participant.post("/onboarding/", {"step": "0", "action": "continue", "reason": "exploring"})
    new_participant.post(
        "/onboarding/",
        {
            "step": "1",
            "action": "continue",
            **{f"bl-{name}": "5" for name in ("bible", "gifts", "call", "plan", "peace")},
        },
    )

    refused = new_participant.post("/onboarding/", {"step": "2", "action": "continue", "path": "remote"})

    assert refused.status_code == 400
    assert Account.objects.get().path == ""


@pytest.mark.django_db
def test_an_existing_account_can_open_the_hub_without_onboarding(new_participant):
    account = Account.objects.get()
    account.onboarding_completed = True
    account.save(update_fields=["onboarding_completed"])

    response = new_participant.get("/hub/")

    assert response.status_code == 200
