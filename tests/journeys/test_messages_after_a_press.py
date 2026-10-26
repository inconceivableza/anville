# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Messages only after a press (ticket 83): in *Whatever You Do* a gate's message shows only once a press it refused
has been made, naming only what is missing, and no button is held disabled to stop a press. Before we begin's way out
signs the participant out. The messages are read from the document, so its wording can change without these."""

import json
import re
from pathlib import Path

import pytest

from engine.models import Publication
from tests.journeys.pages import gate_checklist
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_onboarding_wizard import RATINGS, RATINGS_PAGE, WIZARD, answer, through_the_wizard

DOCUMENT = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do.json"


def the_pathway():
    return json.loads(DOCUMENT.read_text(encoding="utf-8"))


def gate_message(section_id, block_id):
    """✨ The message of a section's gate clause on one block, its {min} filled in as the participant reads it."""
    [section] = [section for section in the_pathway()["content"]["sections"] if section["id"] == section_id]
    [clause] = [clause for clause in section["gate"]["clauses"] if clause["block"] == block_id]
    return clause["message"].replace("{min}", str(clause.get("min", "")))


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(the_pathway())
    return signed_in_client


def continue_button(page):
    return re.search(r"<button [^>]*>Continue →</button>", page).group(0)


@pytest.mark.django_db
def test_the_wizard_says_nothing_on_arrival_and_a_refused_continue_names_what_is_missing(participant):
    choose_a_reason = gate_message("onboarding", "reason")

    arrived = participant.get(WIZARD).content.decode()

    assert gate_checklist(arrived) == {}
    assert " disabled" not in continue_button(arrived)
    refused = participant.post("/sections/onboarding/pages/1/continue/")
    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode()) == {choose_a_reason: False}


@pytest.mark.django_db
def test_a_refused_completion_lists_only_what_is_still_missing(participant):
    answer(participant, "reason", "exploring")
    participant.post("/sections/onboarding/pages/1/continue/")
    for rating in RATINGS[:3]:
        answer(participant, rating, "7")

    assert gate_checklist(participant.get(RATINGS_PAGE).content.decode()) == {}
    refused = participant.post("/sections/onboarding/complete/")
    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode()) == {gate_message("onboarding", RATINGS[3]): False}


@pytest.mark.django_db
def test_five_trusted_voices_does_not_greet_the_participant_with_its_minimum(participant):
    through_the_wizard(participant)

    page = participant.get("/sections/trusted-voices/").content.decode()

    assert gate_message("trusted-voices", "contacts") not in page
    assert gate_checklist(page) == {}


@pytest.mark.django_db
def test_an_opening_question_answered_says_no_saved(participant):
    answer(participant, "reason", "exploring")
    participant.post("/sections/onboarding/pages/1/continue/")

    saved = participant.post(
        f"/answers/{RATINGS[0]}/",
        {"value": "7", "version": Publication.current_version().pk},
        headers={"HX-Request": "true"},
    )

    assert saved.status_code == 200
    assert "Saved" not in saved.content.decode()


@pytest.mark.django_db
def test_log_out_from_before_we_begin_signs_the_participant_out_and_lands_on_the_homepage(participant):
    page = participant.get(WIZARD).content.decode()
    form = re.search(r'<form [^>]*method="post"[^>]*action="([^"]+)"[^>]*>(?:(?!</form>).)*Log out</button>', page, re.S)

    signed_out = participant.post(form.group(1))

    assert (signed_out.status_code, signed_out.url) == (302, "/")
    assert participant.get("/hub/").url.startswith("/accounts/login/")
