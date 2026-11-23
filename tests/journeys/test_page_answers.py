# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Every answer on a page goes with every press on it (sprint-3d-r1-fix-6). Without JavaScript the page's one Save,
and its way on, send all of its answers, which the press stores before anything else, so choosing several ratings and
pressing once loses none; with JavaScript each answer still saves on its own. Each press is sent as the page draws it:
to the address its button names, each answer under the name its field has there. Messages and prompts are read from
the pathway document."""

import re
from html import unescape

import pytest

from engine.models import Response, SealedLetter
from tests.journeys.pages import gate_checklist, version_on
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_letter_sealed import date_field
from tests.journeys.test_messages_after_a_press import gate_message, participant  # noqa: F401  (participant: fixture)
from tests.journeys.test_onboarding_wizard import RATINGS, RATINGS_PAGE, through_the_first_page
from tests.journeys.test_whatever_you_do import QUESTIONS_PAGE, the_pathway, through_to_the_questions

QUESTIONS = ("pl-bible", "pl-gifts", "pl-call", "pl-plan", "pl-peace")


def field_of(page, block_id):
    """✨ The name a rating's points are sent under, as the page draws them."""
    return re.search(rf'<input [^>]*id="answer-{block_id}-1"[^>]* name="([^"]+)"', page).group(1)


def address_of(page, label):
    """✨ Where the press labelled `label` sends the page's form: its button's own address, or else the form's."""
    tag = re.search(rf"<button\b([^>]*)>\s*{re.escape(label)}\s*</button>", page).group(1)
    own = re.search(r'formaction="([^"]+)"', tag)
    sent_by = re.search(r'form="([^"]+)"', tag).group(1)
    return own.group(1) if own else re.search(rf'<form id="{sent_by}"[^>]* action="([^"]+)"', page).group(1)


def press(client, page_url, label, chosen, **extra):
    """✨ The press labelled `label` on a page, sending the page's form with each rating in `chosen` ({block: point})
    chosen, as a browser without JavaScript sends it."""
    page = client.get(page_url).content.decode()
    sent = {field_of(page, block_id): point for block_id, point in chosen.items()}
    return client.post(address_of(page, label), {**sent, "version": version_on(page), **extra})


def stored():
    return Response.objects.get().answers


def prompt_of(block_id):
    """✨ A block's prompt, as the document words it."""
    blocks = (block for section in the_pathway()["content"]["sections"] for block in section["blocks"])
    return next(block["prompt"] for block in blocks if block["id"] == block_id)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "page_url, ratings",
    [(RATINGS_PAGE, RATINGS), (QUESTIONS_PAGE, QUESTIONS)],
    ids=["Before we begin's ratings", "the letter's closing ratings"],
)
def test_without_javascript_the_pages_one_save_stores_every_rating_chosen_on_it(participant, page_url, ratings):
    """✨ The bug: each rating was a form of its own, so its Save stored it alone and every other choice was lost."""
    if page_url == RATINGS_PAGE:
        through_the_first_page(participant)
    else:
        through_to_the_questions(participant)
    chosen = dict(zip(ratings, ("3", "5", "8")))

    saved = press(participant, page_url, "Save", chosen)

    assert (saved.status_code, saved.url) == (303, f"{page_url}#completion")
    assert {rating: stored().get(rating) for rating in ratings} == {
        rating: int(chosen[rating]) if rating in chosen else None for rating in ratings
    }


@pytest.mark.django_db
def test_without_javascript_finishing_stores_the_ratings_sent_and_lists_only_what_is_still_missing(participant):
    """✨ "Continue →" on Before we begin's ratings page finishes it. The ratings it sends are stored before the gate is
    checked, so its refusal lists only what is still missing, and nothing chosen is lost."""
    through_the_first_page(participant)
    chosen = dict.fromkeys(RATINGS[:3], "7")

    refused = press(participant, RATINGS_PAGE, "Continue →", chosen)

    assert refused.status_code == 400
    assert {rating: stored().get(rating) for rating in RATINGS} == {
        **dict.fromkeys(RATINGS),
        **dict.fromkeys(chosen, 7),
    }
    assert gate_checklist(refused.content.decode()) == {gate_message("onboarding", RATINGS[3]): False}
    assert "onboarding" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_a_press_sending_an_answer_it_cannot_store_stores_the_rest_and_names_it_at_the_refusal(participant):
    """✨ Never refused silently: the press is refused, and the page opens where it was pressed, saying which answer
    was not saved. Here a point no scale has, as only a page altered by hand could send."""
    through_the_first_page(participant)
    chosen = {**dict.fromkeys(RATINGS[:4], "7"), RATINGS[4]: "11"}
    page = participant.get(RATINGS_PAGE).content.decode()
    anchor = address_of(page, "Continue →").partition("#")[2]

    refused = press(participant, RATINGS_PAGE, "Continue →", chosen)

    assert refused.status_code == 400
    assert {rating: stored().get(rating) for rating in RATINGS} == {**dict.fromkeys(RATINGS[:4], 7), RATINGS[4]: None}
    at_the_refusal = unescape(refused.content.decode().partition(f'id="{anchor}"')[2])
    assert prompt_of(RATINGS[4]) in at_the_refusal
    assert all(prompt_of(rating) not in at_the_refusal for rating in RATINGS[:4])


@pytest.mark.django_db
def test_with_javascript_an_answers_own_save_stores_only_that_answer(participant):
    """✨ Each answer saves on its own as it changes, saying so beside it: even sent with the whole page's form, as htmx
    sends a field's form, its save stores that answer alone."""
    through_the_first_page(participant)
    page = participant.get(RATINGS_PAGE).content.decode()
    address = re.search(rf'<form id="block-{RATINGS[0]}".*?hx-post="([^"]+)"', page, re.S).group(1)
    whole_page = {field_of(page, rating): "6" for rating in RATINGS}

    saved = participant.post(address, {**whole_page, "version": version_on(page)}, headers={"HX-Request": "true"})

    assert saved.status_code == 200
    assert {rating: stored().get(rating) for rating in RATINGS} == {**dict.fromkeys(RATINGS), RATINGS[0]: 6}


@pytest.mark.django_db
def test_without_javascript_the_save_on_the_page_that_seals_the_letter_keeps_the_date_picked(participant):
    """✨ The date is no answer, but the page drawn again after its Save offered the default in its place, losing the
    one picked (sprint-3d-r1-fix-3 keeps it the same way on going back)."""
    through_to_the_questions(participant)
    picked = date_field(participant.get(QUESTIONS_PAGE).content.decode())["max"]

    press(participant, QUESTIONS_PAGE, "Save", {QUESTIONS[0]: "4"}, opens_on=picked)

    assert date_field(participant.get(QUESTIONS_PAGE).content.decode())["value"] == picked


@pytest.fixture
def sealing_alone(signed_in_client, load_pathway):  # noqa: F811
    """✨ *Whatever You Do* with the closing ratings taken off Section 6's second page, so the page that seals the
    letter has no answer of its own to send."""
    document = the_pathway()
    [letter] = [section for section in document["content"]["sections"] if section["id"] == "letter"]
    letter["blocks"] = [block for block in letter["blocks"] if block["type"] != "agreement_scale"]
    letter["gate"]["clauses"] = [clause for clause in letter["gate"]["clauses"] if clause["block"] == "lt-message"]
    load_pathway(document)
    return signed_in_client


@pytest.mark.django_db
def test_on_a_page_sealing_the_letter_beside_no_answer_enter_in_the_date_presses_its_save_never_the_seal(
    sealing_alone,
):
    """✨ Enter in a field presses its form's first button: with no Save drawn, that was the seal, which can't be undone
    (code review of 23 Nov)."""
    through_to_the_questions(sealing_alone)
    page = sealing_alone.get(QUESTIONS_PAGE).content.decode()

    buttons = re.findall(r"<button\b([^>]*)>(.*?)</button>", page, re.S)
    first = next((tag, label.strip()) for tag, label in buttons if 'form="page-answers"' in tag)

    assert first[1] == "Save" and "save-fallback" in first[0]
    picked = date_field(page)["max"]
    saved = sealing_alone.post(address_of(page, "Save"), {"opens_on": picked, "version": version_on(page)})
    assert saved.status_code == 303 and not SealedLetter.objects.exists()
    assert date_field(sealing_alone.get(QUESTIONS_PAGE).content.decode())["value"] == picked
