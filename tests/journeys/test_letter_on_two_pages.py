# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ *Whatever You Do*'s Section 6 on two pages (ticket 107): the task, the verse and the letter first, whose press
saves the letter and leads on; then "Where are you now?", the date and the seal. Each press is sent as its form sends
it without JavaScript; with it, htmx sends the same form. Messages are read from the pathway document."""

import re

import pytest
from django.utils.html import escape

from engine.models import Response, SealedLetter
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_letter_sealed import date_field
from tests.journeys.test_whatever_you_do import (  # noqa: F401  (participant is a fixture, used by name)
    A_LETTER,
    LETTER_PAGE,
    QUESTIONS_PAGE,
    answer,
    answer_all_five,
    go_on_from_the_letter,
    participant,
    seal,
    the_pathway,
    through_to_the_letter,
    through_to_the_questions,
)

# ✨ Short of the ten characters the letter's gate clause asks for.
TOO_SHORT = "Hello me"


def letter_message():
    """✨ What the gate says while the letter is too short, as the document words it."""
    [letter] = [section for section in the_pathway()["content"]["sections"] if section["id"] == "letter"]
    [clause] = [clause for clause in letter["gate"]["clauses"] if clause["block"] == "lt-message"]
    return clause["message"]


def stored_letter():
    return Response.objects.get().answers.get("lt-message")


def back_from_the_questions(client, opens_on):
    """✨ "← Previous page" on the questions page without JavaScript: a press of the seal's form, sending the date in its
    field as it goes (sprint-3d-r1-fix-3)."""
    page = client.get(QUESTIONS_PAGE).content.decode()
    tag = re.search(r"<button [^>]*>← Previous page</button>", page).group(0)
    button = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
    return client.post(button["formaction"], {"opens_on": opens_on, button["name"]: button.get("value", "")})


def where_unmet_leads(page, message):
    """✨ Where an unmet requirement's message leads, or None where it is not a link."""
    link = re.search(rf'<a [^>]*href="([^"]+)"[^>]*>\s*<span class="gate-message">{re.escape(escape(message))}<', page)
    return link.group(1) if link else None


@pytest.mark.django_db
def test_the_letter_pages_press_stores_the_letter_sent_with_it_and_opens_the_questions(participant):
    """✨ Without JavaScript the letter is saved only by its own Save, so a press that did not carry it would lose
    everything typed since. The way back from the questions returns to the letter, as it was sent."""
    client = through_to_the_letter(participant)

    went_on = go_on_from_the_letter(client, A_LETTER)

    assert (went_on.status_code, went_on.url) == (303, QUESTIONS_PAGE)
    assert stored_letter() == A_LETTER
    back = back_from_the_questions(client, date_field(client.get(QUESTIONS_PAGE).content.decode())["value"])
    assert (back.status_code, back.url) == (303, f"{LETTER_PAGE}#block-lt-message")
    assert escape(A_LETTER) in client.get(back.url).content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("javascript", [False, True], ids=["without JavaScript", "with JavaScript"])
def test_a_date_picked_then_going_back_to_the_letter_and_on_again_is_offered_again(participant, javascript):
    """✨ With JavaScript the date is kept as it is changed, whichever way the participant then leaves the page; without,
    "← Previous page" sends it as it goes (sprint-3d-r1-fix-3)."""
    client = through_to_the_questions(participant)
    field = date_field(client.get(QUESTIONS_PAGE).content.decode())
    picked = field["max"]  # ✨ the latest the letter accepts, not the date first offered
    assert picked != field["value"]

    if javascript:
        client.post(field["hx-post"], {"opens_on": picked}, HTTP_HX_REQUEST="true")
        client.get(LETTER_PAGE)
    else:
        back_from_the_questions(client, picked)
    go_on_from_the_letter(client)

    assert date_field(client.get(QUESTIONS_PAGE).content.decode())["value"] == picked


@pytest.mark.django_db
def test_a_letter_too_short_is_stored_as_sent_but_the_questions_stay_shut(participant):
    client = through_to_the_letter(participant)

    refused = go_on_from_the_letter(client, TOO_SHORT)

    assert refused.status_code == 400
    assert escape(letter_message()) in refused.content.decode()
    assert escape(TOO_SHORT) in refused.content.decode()  # ✨ back in its box, as sent
    assert stored_letter() == TOO_SHORT
    assert client.get(QUESTIONS_PAGE).url == LETTER_PAGE


@pytest.mark.django_db
def test_sealing_with_the_letter_cut_short_is_refused_and_leads_back_to_the_letter(participant):
    """✨ The letter is on the page before the press that seals it, so its refusal leads there."""
    client = through_to_the_questions(participant)
    answer_all_five(client, prefix="pl")
    answer(client, "lt-message", TOO_SHORT)  # ✨ cut short after going back to it

    refused = seal(client)

    assert refused.status_code == 400
    assert where_unmet_leads(refused.content.decode(), letter_message()) == f"{LETTER_PAGE}#block-lt-message"
    assert not SealedLetter.objects.exists()
    assert "letter" not in Response.objects.get().completed_sections

    answer(client, "lt-message", A_LETTER)
    sealed = seal(client)
    assert (sealed.status_code, sealed.url) == (303, f"{LETTER_PAGE}#block-lt-message")  # ✨ to the sealed letter


@pytest.mark.django_db
def test_once_sealed_the_letter_pages_press_changes_nothing_and_leads_on_to_the_questions(participant):
    """✨ Sealed, the letter has no field on its page, so the press sends none (sprint-3d-r1-fix-6)."""
    client = through_to_the_questions(participant)
    answer_all_five(client, prefix="pl")
    seal(client)

    went_on = go_on_from_the_letter(client, None)

    assert (went_on.status_code, went_on.url) == (303, QUESTIONS_PAGE)
    assert stored_letter() == A_LETTER
