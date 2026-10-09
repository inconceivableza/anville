# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A single select: one choice from an authored list, saved as the chosen option's identifier."""

import re

import pytest

from engine.models import Response
from tests.documents import pathway_document
from tests.journeys.test_answers import answer, shown
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)

ONBOARDING = "onboarding"


def with_a_single_select(**fields):
    """✨ The test pathway with a single select at the top of onboarding."""
    document = pathway_document()
    document["content"]["sections"][0]["blocks"].insert(
        0,
        {
            "id": "reason",
            "type": "single_select",
            "prompt": "What's bringing you to the course?",
            "placeholder": "Select...",
            "options": [
                {"id": "job-change", "label": "Considering a job change"},
                {"id": "retirement", "label": "Approaching retirement"},
                {"id": "other", "label": "Other"},
            ],
            **fields,
        },
    )
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(with_a_single_select())
    return signed_in_client


def chosen(page, block_id):
    """✨ The option a participant sees chosen, read from the rendered select, or None."""
    select = re.search(rf'<select id="answer-{block_id}".*?</select>', page, re.S)
    match = re.search(r'<option value="([^"]*)" selected>', select.group(0)) if select else None
    return match.group(1) if match else None


@pytest.mark.django_db
def test_a_single_select_shows_its_prompt_and_every_option_in_the_order_authored(participant):
    page = shown(participant, ONBOARDING)

    assert re.search(r'<label for="answer-reason">What&#x27;s bringing you to the course\?</label>', page)
    labels = re.findall(r'<option value="[^"]+">([^<]*)</option>', page)
    assert labels == ["Considering a job change", "Approaching retirement", "Other"]


@pytest.mark.django_db
def test_nothing_is_chosen_until_the_participant_chooses(participant):
    """✨ A select shows its first option when none is marked, so an unanswered one leads with the empty
    placeholder rather than seeming to have an answer it does not."""
    page = shown(participant, ONBOARDING)

    assert re.search(r'<select id="answer-reason"[^>]*>\s*<option value="">Select...</option>', page)
    assert chosen(page, "reason") is None


@pytest.mark.django_db
def test_a_chosen_option_is_saved_and_shown_chosen_after_a_reload(participant):
    saved = answer(participant, "reason", "retirement", section=ONBOARDING)

    assert saved.status_code == 200
    assert Response.objects.get().answers["reason"] == "retirement"
    assert chosen(shown(participant, ONBOARDING), "reason") == "retirement"


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["redundancy", "Approaching retirement"])
def test_a_choice_that_is_not_one_of_the_options_is_refused_and_nothing_is_stored(participant, value):
    refused = answer(participant, "reason", value, section=ONBOARDING)

    assert refused.status_code == 400
    assert "Choose one of the options." in refused.content.decode()
    assert not Response.objects.filter(answers__has_key="reason").exists()


@pytest.mark.django_db
def test_choosing_the_empty_option_again_takes_the_answer_back(participant):
    """✨ As in the prototype, going back to "Select..." leaves the question unanswered, rather than keeping
    a choice the page no longer shows."""
    answer(participant, "reason", "retirement", section=ONBOARDING)

    cleared = answer(participant, "reason", "", section=ONBOARDING)

    assert cleared.status_code == 200
    assert chosen(shown(participant, ONBOARDING), "reason") is None
    assert "0 of 3 answered" in participant.get("/hub/").content.decode()


@pytest.mark.django_db
def test_an_option_label_is_escaped_like_any_authored_text(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(with_a_single_select(options=[{"id": "tag", "label": "<b>Bold</b>"}]))

    page = shown(signed_in_client, ONBOARDING)

    assert "<b>Bold</b>" not in page
    assert "&lt;b&gt;Bold&lt;/b&gt;" in page


@pytest.mark.django_db
def test_a_single_select_counts_towards_progress(participant):
    assert "0 of 3 answered" in participant.get("/hub/").content.decode()  # ✨ the test pathway's two, and this
