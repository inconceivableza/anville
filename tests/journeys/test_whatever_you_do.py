# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ *Whatever You Do* as the content owner now wants it, which adds a fifth rating the original prototype does not have.

After the first demo the content owner asked for a fifth statement, asked at the start and again at the end, to
see whether a participant trusts God's plan more, not less, once they have been through the pathway. The faithful
port keeps the original prototype's four, and the last test here keeps the two documents from drifting apart in
any other way, so each can keep growing and be compared once everything is built.
"""

import json
import re
from pathlib import Path

from datetime import timedelta

import pytest
import time_machine
from django.test import Client
from django.utils import timezone
from django.utils.html import escape

from engine.document.observers import minimum_observers, relationship_question
from engine.hub import COACH_WAIT_WORDING, COMPARISON_READY_SENTENCE, hub_for, track_sections
from engine.models import Contact, ObserverResponse, Response
from tests.journeys.test_coach_checklist import choose, step
from tests.journeys.test_coach_link import answer_as_coach, coach_link_action, link_shown
from tests.journeys.test_navigation import section_in, sidebar_of
from tests.journeys.pages import main_of
from tests.journeys.test_hub import (  # noqa: F401  (signed_in_client is a fixture, used by name)
    hub_entry,
    next_step,
    side_card,
    signed_in_client,
)
from tests.journeys.test_invitations import issue_link
from tests.journeys.test_observer_assessment import send, withdraw
from tests.journeys.test_observer_landing import claim
from tests.prototype import js_string
from tests.journeys.test_whatever_you_do_faithful_port import (
    A_LETTER,
    ADD_FIVE,
    ANSWER_ALL_FOUR,
    BASELINE_STATEMENTS,
    VIEW_THE_COMPARISON,
    add_people,
    answer,
    complete,
    move_past,
    onboarding_pages,
)
from tests.journeys.test_whatever_you_do_faithful_port import SLOTS as PROTOTYPE_SLOTS
from tests.journeys.test_whatever_you_do_faithful_port import the_pathway as the_faithful_port

DOCUMENT = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do.json"

PEACE = "I am at peace with God's plan for my life"
ANSWER_ALL_FIVE = "Answer all five to continue"
# ✨ The prototype's two minimum-length messages, each with how much is needed added.
SAYS_HOW_MUCH = {
    "Write your calling statement to continue.": "Write your calling statement (at least 10 characters) to continue.",
    "Write at least one part of your letter before sealing it.": (
        "Write at least one part of your letter (10 characters or more) before sealing it."
    ),
}
SLOTS = (*PROTOTYPE_SLOTS, "peace")
# ✨ Three people rather than the prototype's five, each with their link (ticket 52), as the list marks three needed
# (ticket 51a). The two side cards' gates, which complete them with nothing to press.
ADD_THREE = "Add at least {min} people."  # ✨ its clause's 3 (ticket 81)
SEND_THE_COACH = "Choose a coach and send them their link."
# ✨ Before we begin's coach and contacts pages became the hub side cards Walk with a coach and Five trusted voices
# (ticket 50).
COACH_PAGE = "/sections/walk-with-a-coach/"
CONTACTS_PAGE = "/sections/trusted-voices/"
RATINGS_PAGE = "/sections/onboarding/pages/2/"


def the_pathway():
    return json.loads(DOCUMENT.read_text(encoding="utf-8"))


def a_whole_sort():
    """✨ Every card placed in "Good at this", sent as the widget sends a sort that skips fine-tuning: buckets
    alone."""
    return {item["id"]: {"bucket": "good-at-this"} for item in the_pathway()["instrument"]["items"]}


def submit_the_sort(client):
    return answer(client, "strengths-sort", json.dumps(a_whole_sort()))


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(the_pathway())
    return signed_in_client


def answer_all_five(client, prefix="bl"):
    for slot in SLOTS:
        answer(client, f"{prefix}-{slot}", "7")


def to_the_ratings(client):
    """✨ The reason for taking the course, then on to Before we begin's second page, the five ratings."""
    answer(client, "reason", "exploring")
    move_past(client, 1)
    return client


def answer_onboarding(client):
    """✨ Everything Before we begin requires: the reason, then all five ratings, on the page it is completed from."""
    to_the_ratings(client)
    answer_all_five(client)


def through_to_the_letter(client):
    """✨ Sections 1 and 2 done with everyone invited and the coach accepted, then Sections 3, 4 and 5 finished in turn,
    which is what opens the letter."""
    through_to_section_3(client)
    coach_accepts(client)
    for section_id in ON_PAPER:
        complete(client, section_id)
    return client


@pytest.mark.django_db
def test_the_fifth_statement_is_asked_after_the_original_prototypes_four(participant):
    page = to_the_ratings(participant).get(RATINGS_PAGE).content.decode()

    for statement in BASELINE_STATEMENTS.values():
        assert escape(statement) in page
    assert page.index(escape(BASELINE_STATEMENTS["bl-plan"])) < page.index(escape(PEACE))
    assert page.count("Strongly disagree") == 5


@pytest.mark.django_db
def test_all_five_ratings_are_needed_before_the_participant_may_continue(participant):
    to_the_ratings(participant)
    for slot in PROTOTYPE_SLOTS:
        answer(participant, f"bl-{slot}", "5")

    refused = complete(participant, "onboarding")

    assert refused.status_code == 400
    assert refused.content.decode().count(ANSWER_ALL_FIVE) == 1
    assert "onboarding" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_the_way_on_opens_once_all_five_are_answered(participant):
    answer_onboarding(participant)

    assert complete(participant, "onboarding").status_code == 303


@pytest.mark.django_db
def test_the_fifth_statement_is_asked_again_at_the_end(participant):
    page = through_to_the_letter(participant).get("/sections/letter/").content.decode()

    assert escape(PEACE) in page
    assert page.count("Strongly disagree") == 5


@pytest.mark.django_db
def test_the_letter_cannot_be_sent_without_the_fifth_after_rating(participant):
    client = through_to_the_letter(participant)
    answer(client, "lt-message", A_LETTER)
    for slot in PROTOTYPE_SLOTS:
        answer(client, f"pl-{slot}", "8")

    refused = complete(client, "letter")

    assert refused.status_code == 400
    assert refused.content.decode().count(ANSWER_ALL_FIVE) == 1

    answer(client, "pl-peace", "8")
    assert complete(client, "letter").status_code == 303


@pytest.mark.django_db
def test_progress_counts_the_six_numbered_sections(participant):
    """✨ Sections 1 to 6 (ticket 87), leaving out the strengths evaluation within Section 1 and the side cards Walk with
    a coach and Five trusted voices (content owner's feedback). The hub opens once Before we begin is done, which is
    not numbered either (ticket 69)."""
    answer_onboarding(participant)
    complete(participant, "onboarding")

    assert "0 of 6 sections complete" in participant.get("/hub/").content.decode()


def cards_complete():
    return {"walk-with-a-coach", "trusted-voices"} & set(Response.objects.get().completed_sections)


@pytest.mark.django_db
def test_walk_with_a_coach_completes_once_the_coach_has_a_link_and_five_trusted_voices_once_three_people_have(
    participant,
):
    """✨ Neither has anything to press (ticket 52): choosing the coach makes their link (ticket 51b), and adding a
    person theirs (ticket 51a). Neither is counted among the sections (ticket 87)."""
    answer_onboarding(participant)
    complete(participant, "onboarding")
    participant.get("/hub/")
    assert cards_complete() == set()

    choose(participant)
    participant.get("/hub/")
    assert cards_complete() == {"walk-with-a-coach"}

    add_people(participant, 2)
    participant.get("/hub/")
    assert cards_complete() == {"walk-with-a-coach"}
    add_people(participant, 3)
    assert "0 of 6 sections complete" in participant.get("/hub/").content.decode()
    assert cards_complete() == {"walk-with-a-coach", "trusted-voices"}


@pytest.mark.django_db
def test_the_contact_list_opens_with_three_rows_needed_and_two_optional(participant):
    """✨ Three needed (ticket 51a), as its gate and its introduction ask (ticket 52)."""
    answer_onboarding(participant)
    complete(participant, "onboarding")

    page = participant.get(CONTACTS_PAGE).content.decode()

    assert page.count('name="email"') == 5
    assert (page.count(">Needed<"), page.count(">Optional<")) == (3, 2)
    assert "We need at least 3 people whose opinion you trust" in page


@pytest.mark.django_db
def test_all_five_start_ratings_are_fixed_once_onboarding_is_complete(participant):
    """✨ Before we begin is once-only (ticket 69), so a save to it leads to the hub rather than being refused there."""
    answer_onboarding(participant)
    complete(participant, "onboarding")

    for slot in SLOTS:
        assert answer(participant, f"bl-{slot}", "2").url == "/hub/"
    assert {Response.objects.get().answers[f"bl-{slot}"] for slot in SLOTS} == {7}


@pytest.mark.django_db
def test_all_five_end_ratings_are_fixed_once_the_letter_is_sent(participant):
    client = through_to_the_letter(participant)
    answer(client, "lt-message", A_LETTER)
    answer_all_five(client, prefix="pl")
    complete(client, "letter")

    for slot in SLOTS:
        assert answer(client, f"pl-{slot}", "2").status_code == 409
    assert {Response.objects.get().answers[f"pl-{slot}"] for slot in SLOTS} == {7}


def test_every_section_but_sections_1_and_2_says_how_long_it_takes():
    """✨ Which sections say how long they take, not the figures, which are the pathway's and are listed with their
    sources in the spec's time estimates. Section 1 has none: it cannot be finished without the sort, so its own few
    minutes would read as less than the strengths evaluation it leads to. Nor has Section 2, which waits on other
    people's answers (ticket 87). None is a placeholder ("? min")."""
    sections = the_pathway()["content"]["sections"]

    assert [section["id"] for section in sections if section.get("estimate")] == [
        "onboarding",
        "strengths",
        "shape",
        "calling",
        "growth",
        "letter",
    ]
    assert not any("?" in section.get("estimate", "") for section in sections)


def test_no_activity_says_how_long_it_takes_on_its_own():
    """✨ The letter section is the only one with two activities, and neither carries a "This part" of its own: the
    letter's went in fix-11, the closing ratings' after it, so only whole sections say how long they take."""
    estimated = {
        (section["id"], block["id"]): block["estimate"]
        for section in the_pathway()["content"]["sections"]
        for block in section["blocks"]
        if block.get("estimate")
    }

    assert estimated == {}


COACH_PROTOTYPE = (DOCUMENT.parents[1] / "Prototypes for reference" / "coach-selection-prototype.html").read_text(
    encoding="utf-8"
)
# ✨ The mock-up's names for each question's parts, and the document's.
COACH_FIELDS = {
    "q": "question",
    "note": "note",
    "why": "why",
    "coachNote": "coach_note",
    "coachWhy": "coach_why",
    "commit": "commitment",
}


def the_mock_ups_questions():
    """✨ The six questions as the coach mock-up's script holds them, in the document's field names."""
    script = re.search(r"const QUESTIONS = \[(.*?)\n\];", COACH_PROTOTYPE, re.S).group(1)
    questions = []
    for entry in re.findall(r"\{(.*?)\}", script, re.S):
        question = {
            "id": re.search(r"id:'(\w+)'", entry).group(1),
            "critical": re.search(r"critical:(true|false)", entry).group(1) == "true",
        }
        for field, text in re.findall(r'(\w+):"((?:[^"\\]|\\.)*)"', entry):
            question[COACH_FIELDS[field]] = js_string(text)
        questions.append(question)
    return questions


def the_coach_step(document):
    return next(
        block
        for section in document["content"]["sections"]
        for block in section["blocks"]
        if block["type"] == "coach_checklist"
    )


def test_the_coach_step_asks_the_mock_ups_six_questions_word_for_word():
    """✨ Their wording, which three are critical, why each matters, and the coach's side of each for ticket 13."""
    questions = the_coach_step(the_pathway())["questions"]

    assert len(questions) == 6
    assert questions == the_mock_ups_questions()
    assert [question["id"] for question in questions if question["critical"]] == ["faith", "objectivity", "coaching"]


def test_the_onboarding_wizard_header_shows_the_new_logo_not_the_old_mark(participant):
    """✨ Fix-5: the wizard's own header, which the participant header does not replace, draws the new logo."""
    page = participant.get("/sections/onboarding/").content.decode()
    header = re.search(r'<header class="ob-top">.*?</header>', page, re.S).group(0)

    assert '<use href="#logo"' in header
    assert '<use href="#mark"' not in header


def test_before_we_begin_is_a_wizard_of_the_reason_then_the_ratings_and_the_coach_and_contacts_are_side_cards():
    """✨ The hackathon's wizard asked the reason, then the ratings; the original prototype's mentor and contacts
    screens became the hub side cards Walk with a coach and Five trusted voices (ticket 50)."""
    document = the_pathway()
    side_cards = {
        section["id"]: [block["id"] for block in section["blocks"]]
        for section in document["content"]["sections"]
        if "side_card" in section
    }

    assert document["content"]["sections"][0]["wizard"] is True
    assert onboarding_pages(document) == [
        ["reason"],
        ["baseline-intro", "bl-bible", "bl-gifts", "bl-call", "bl-plan", "bl-peace"],
    ]
    assert side_cards == {"walk-with-a-coach": ["coach"], "trusted-voices": ["contacts-intro", "contacts"]}


def to_the_coach_page(client):
    """✨ Before we begin done, which opens Walk with a coach."""
    answer_onboarding(client)
    complete(client, "onboarding")
    return client


@pytest.mark.django_db
def test_a_refused_coach_leaves_the_way_on_as_it_was(participant):
    to_the_coach_page(participant)

    refused = choose(participant, confirmed=False).content.decode()

    assert "hx-swap-oob" not in refused


def test_the_coach_step_is_introduced_as_the_mock_up_introduces_it():
    coach = the_coach_step(the_pathway())

    assert coach["heading"] == "Walking with a coach"
    assert coach["lead"] == "This choice matters more than any other you'll make in the course."
    assert coach["name_prompt"] == "Who are you thinking of asking?"
    assert coach["name_placeholder"] == "Their first name"
    assert coach["name_hint"] == (
        "Just a first name for now. Six quick questions follow — answer them honestly rather than generously."
    )


@pytest.mark.django_db
def test_onboarding_can_be_completed_without_choosing_a_coach(participant):
    answer_onboarding(participant)

    assert complete(participant, "onboarding").status_code == 303
    assert not Contact.objects.filter(role=Contact.Role.COACH).exists()


@pytest.mark.django_db
def test_a_chosen_coach_is_kept_on_the_coach_page_and_apart_from_the_contacts(participant):
    to_the_coach_page(participant)

    saved = choose(participant, htmx=False)

    assert saved.url == COACH_PAGE  # ✨ the checklist is the page's first block: back at the top, no anchor (ticket 82)
    assert "You've chosen Sam" in participant.get(COACH_PAGE).content.decode()
    assert "sam@example.com" not in participant.get(CONTACTS_PAGE).content.decode()


@pytest.mark.django_db
def test_the_coach_page_is_reached_at_its_top(participant):
    """✨ Ticket 82: the sidebar's way to the coach page names no anchor, which would open it scrolled to its card."""
    to_the_coach_page(participant)

    assert the_coach_page(participant) == COACH_PAGE


def test_observers_are_not_asked_how_they_know_the_participant():
    """✨ The faithful port's relationship question (ticket 15b) is not asked here, so nothing is kept of it."""
    assert relationship_question(the_pathway(), "Sam") is None


def test_the_observers_privacy_notice_keeps_nothing_of_how_they_know_the_participant():
    notice = the_pathway()["observers"]["privacy_notice"]

    assert "What we keep: your answers." in notice
    assert "how you know" not in notice


# ✨ The observers' notice's one sentence about the coach (ticket 27), whom the faithful port never asks for.
SHOWN_TO_THE_COACH = " {name} may also choose to show this to a trusted third party."


def without_the_coach_step(document):
    """✨ Only this pathway asks for a coach the mock-up's way; the faithful port's own mentor screen is ticket 10b.
    The coach page goes with it, so the break that opened that page goes too, and so does the privacy notice's sentence
    saying the participant may show their coach what they see. So does the sort's coach brief (ticket 25a), as the
    faithful port has no coach to read it."""
    observers = document["observers"]
    observers["privacy_notice"] = observers["privacy_notice"].replace(SHOWN_TO_THE_COACH, "")
    for section in document["content"]["sections"]:
        for block in section["blocks"]:
            block.pop("coach_brief", None)
        blocks = [block for block in section["blocks"] if block["type"] != "coach_checklist"]
        section["blocks"] = [
            block
            for block, after in zip(blocks, [*blocks[1:], None])
            if not (block["type"] == "page_break" and after and after["type"] == "page_break")
        ]
    return document


def without_estimates(document):
    """✨ The faithful port has no estimates, since the prototype gave none."""
    for section in document["content"]["sections"]:
        section.pop("estimate", None)
        for block in section["blocks"]:
            block.pop("estimate", None)
    return document


def without_the_tie_break(document):
    """✨ The tie-break is not in the original prototype, so the faithful port takes neither its settings and statements,
    nor the generalist's wording (ticket 30a), nor the pair screen's (ticket 30b)."""
    document["measurement"].pop("tie_break", None)
    document["presentation"].pop("generalist", None)
    document["presentation"].pop("tie_break", None)
    return document


NEW_WORDS = [
    # ✨ Sprint 3c (ticket 85): the prototype's "assessment" is the strengths evaluation, and an observer sends an
    # evaluation.
    ("Open Strengths Assessment", "Open the strengths evaluation"),
    ("the Strengths Assessment – a tool where you", "the strengths evaluation, where you"),
    ("the Strengths Assessment", "the strengths evaluation"),
    ("to assess you too", "to evaluate you too"),
    ("completed the assessment", "completed the strengths evaluation"),
    ("your assessment results", "your strengths evaluation results"),
    ("send your assessment now", "send your evaluation now"),
    ("Send my assessment", "Send my evaluation"),
    # ✨ Sprint 3c (ticket 87): Section 1's passages.
    ("Read these passages before continuing", "Scripture on gifts"),
]


def in_the_new_words(node):
    """✨ `node` with the faithful port's old words for the strengths evaluation put into the new ones, as this
    pathway words them and the port, which keeps the prototype's, does not."""
    if isinstance(node, dict):
        return {key: in_the_new_words(value) for key, value in node.items()}
    if isinstance(node, list):
        return [in_the_new_words(value) for value in node]
    if node == "Strengths assessment":
        return "Strengths evaluation"
    if isinstance(node, str):
        for old, new in NEW_WORDS:
            node = node.replace(old, new)
    return node


def test_the_pathway_is_the_faithful_port_with_a_fifth_rating_and_nothing_else():
    """✨ The fifth rating is added to the faithful port here and the result compared whole, so a change made to
    one document and not the other fails, and so does a slip in the fifth rating itself (its place, its anchors,
    its gate clause, or a message still saying four). The minimum-length messages are reworded the same way,
    the time estimates, checked above, the hub's section numbers, next-step wording and photos and Section 1's results
    are set aside, and so are the downloads in place of Sections 3–5's own blocks, Section 1's split in two (ticket
    87), Section 2's way to the comparison and the two-round prototype's cards."""
    expected = the_faithful_port()
    for section in expected["content"]["sections"]:
        for clause in section.get("gate", {}).get("clauses", []):
            clause["message"] = SAYS_HOW_MUCH.get(clause["message"], clause["message"])
    for section_id, prefix in (("onboarding", "bl"), ("letter", "pl")):
        section = next(section for section in expected["content"]["sections"] if section["id"] == section_id)
        blocks = section["blocks"]
        plan = next(index for index, block in enumerate(blocks) if block["id"] == f"{prefix}-plan")
        blocks.insert(plan + 1, {**blocks[plan], "id": f"{prefix}-peace", "prompt": PEACE})
        clauses = section["gate"]["clauses"]
        for clause in clauses:
            if clause["message"] == ANSWER_ALL_FOUR:
                clause["message"] = ANSWER_ALL_FIVE
        plan_clause = next(index for index, clause in enumerate(clauses) if clause.get("block") == f"{prefix}-plan")
        clauses.insert(plan_clause + 1, {"type": "has_answer", "block": f"{prefix}-peace", "message": ANSWER_ALL_FIVE})
    three_people_each_with_their_link(expected)
    a_download_in_place_of_each_of_sections_2_to_4(expected)
    in_six_sections(expected)
    no_relationship_question(expected)
    expected = in_the_new_words(without_the_cards(expected))

    assert without_what_finishing_takes(
        without_the_comparison_signpost(
            without_the_next_step_and_photos(
                without_numbers(
                    without_the_tie_break(
                        without_the_coach_step(without_estimates(without_the_wizard(without_the_cards(the_pathway()))))
                    )
                )
            )
        )
    ) == (without_numbers(expected))


def without_the_cards(document):
    """✨ The cards, buckets and sort without fine-tuning are the two-round prototype's (held to it in
    `tests/core/test_two_round_cards.py`), and so is Section 1's activity saying what sorting them takes."""
    document.pop("instrument")
    document.pop("sorts_skip_fine_tuning", None)
    for section in document["content"]["sections"]:
        for block in section["blocks"]:
            if block["id"] == "gifts-activity":
                block.pop("body")
    return document


def without_what_finishing_takes(document):
    """✨ What finishing each section takes, as its lock notes name it, is this pathway's alone (ticket 79), and so is
    Section 1's "I've finished Section 1" and the letter's "I've finished Section 6": the faithful port's notes name the
    sections by title, and its Section 1 and letter have the engine's own button."""
    for section in document["content"]["sections"]:
        section.pop("to_finish", None)
        if section["id"] in ("designed", "letter"):
            section.pop("complete_label")
    return document


def without_the_comparison_signpost(document):
    """✨ The way to the comparison, in Section 2 (ticket 87), is this pathway's alone (ticket 67a): the faithful port
    reaches the comparison from the results page only, as the original prototype does. Nor does anything in the
    faithful port wait on the comparison (ticket 68), as this pathway's first workbook does."""
    for section in document["content"]["sections"]:
        section["blocks"] = [block for block in section["blocks"] if block["type"] != "comparison_signpost"]
        for block in section["blocks"]:
            block.pop("after_comparison", None)
    return document


def without_the_wizard(document):
    """✨ Before we begin is a wizard of two pages here, the reason and then the ratings, and its coach and contacts
    pages became the hub side cards Walk with a coach and Five trusted voices (ticket 50). The faithful port keeps the
    original prototype's one section, so the contacts and their gate clause go back into it on a page of their own,
    and the coach goes, as without the coach step. Nor is it once-only there, so it stays listed once complete (ticket
    69). Nor has it the wizard's verses, words and welcome (sprint-3c-r3-fix-7)."""
    sections = document["content"]["sections"]
    onboarding = sections[0]
    del onboarding["wizard"]
    del onboarding["once_only"]
    del onboarding["wizard_steps"]
    del onboarding["welcome"]
    onboarding["blocks"] = [block for block in onboarding["blocks"] if block["id"] != "to-ratings"]
    voices = next(section for section in sections if section["id"] == "trusted-voices")
    onboarding["blocks"] += [{"id": "to-contacts", "type": "page_break"}, *voices["blocks"]]
    onboarding["gate"]["clauses"] += voices["gate"]["clauses"]
    sections[:] = [section for section in sections if "side_card" not in section]
    return document


def without_the_next_step_and_photos(document):
    """✨ The hub's next-step wording, its photos and their credits' setting are this pathway's alone (ticket 49b): the
    faithful port takes none. Nor does it take messages only after a press (ticket 83), keeping its checklist, nor
    quiet ratings (sprint-3c-r3-fix-15), its ratings still saying "Saved"."""
    document.pop("photos", None)
    document.pop("show_courtesy_credits", None)
    document.pop("messages_after_a_press", None)
    document.pop("ratings_save_quietly", None)
    for section in document["content"]["sections"]:
        section.pop("next_step", None)
    return document


def without_numbers(document):
    """✨ The hub's section numbers are this pathway's alone (ticket 49a): the faithful port takes none, and keeps
    "Section 1: " and the like at the start of its titles, which this pathway drops beside its numbers."""
    for section in document["content"]["sections"]:
        section.pop("number", None)
        section["title"] = re.sub(r"^Section \d+: ", "", section["title"])
    return document


def a_download_in_place_of_each_of_sections_2_to_4(document):
    """✨ Sections 3–5 are done on paper here, each from its part of the content owner's workbook, so this pathway keeps
    the faithful port's sections, their ids, titles and order, and offers a PDF in each in place of its in-app blocks
    (ticket 58). What each holds and requires is new, with nothing in the faithful port to compare it with, so it is
    taken as it is; the tests below say what it does. Section 1 is completed on the participant's own work, without the
    comparison visited (ticket 52); Section 3 opens once Section 1 and both side cards are complete, Section 4 once
    Sections 1–3 are finished (ADR 0019; ticket 87), Section 5 once Section 4 is, and the letter, Section 6, waits for
    Section 5."""
    sections = document["content"]["sections"]
    ours = {
        section["id"]: section
        for section in without_what_finishing_takes(without_estimates(the_pathway()))["content"]["sections"]
    }
    for index, section in enumerate(sections):
        if section["id"] in ON_PAPER:
            sections[index] = {**ours[section["id"]], "title": section["title"]}
    designed = next(section for section in sections if section["id"] == "designed")
    designed["gate"]["clauses"] = [
        clause for clause in designed["gate"]["clauses"] if clause["message"] != VIEW_THE_COMPARISON
    ]
    next(section for section in sections if section["id"] == "letter")["requires"] = ["growth"]


def in_six_sections(document):
    """✨ Section 1 splits in two here (ticket 87): its passages, with nothing to confirm, so the strengths evaluation
    opens with it, and the evaluation, which is all it needs to be finished; then Section 2, "Your gifts, seen
    together". Section 2 is new, with nothing in the faithful port to compare it with, so it is taken as it is, less
    its way to the comparison, as without the comparison signpost. The faithful port's reflection goes: Section 2
    offers the first workbook in its place."""
    sections = document["content"]["sections"]
    designed = next(section for section in sections if section["id"] == "designed")
    designed["title"] += " – your strengths"
    blocks = {block["id"]: block for block in designed["blocks"]}
    reading = blocks["gifts-reading"]
    reading["type"] = "scripture_passages"
    del reading["confirm_label"]
    del blocks["strengths-link"]["holds_what_follows"]
    designed["blocks"] = [block for block in designed["blocks"] if block["id"] != "gifts-summary"]
    designed["gate"]["clauses"] = [clause for clause in designed["gate"]["clauses"] if clause["block"] != "gifts-summary"]
    ours = next(section for section in the_pathway()["content"]["sections"] if section["id"] == "others")
    others = {key: value for key, value in ours.items() if key not in ("next_step", "to_finish")}
    without_the_comparison_signpost({"content": {"sections": [others]}})
    sections.insert(sections.index(designed) + 2, others)  # ✨ after Section 1's part, the strengths evaluation


def no_relationship_question(document):
    """✨ The faithful port asks observers how they know the participant (ticket 15b); this pathway does not, so its
    privacy notice keeps only their answers."""
    observers = document["observers"]
    del observers["relationship"]
    observers["privacy_notice"] = observers["privacy_notice"].replace(
        "What we keep: your answers, and how you know {name}.", "What we keep: your answers."
    )


def three_people_each_with_their_link(document):
    """✨ The faithful port asks for the prototype's five people, or none for now; this pathway asks for three, each with
    their link (ticket 52), in each place it says so: onboarding's list, which became Five trusted voices, and Section
    1's Strengths assessment card. Its list says that more people can be added (ticket 70)."""
    for block in document["content"]["sections"][1]["blocks"]:
        if block["id"] == "strengths-link":
            block["body"] = block["body"].replace("at least 5 trusted people", "at least 3 trusted people")
    onboarding = document["content"]["sections"][0]
    for block in onboarding["blocks"]:
        if block["type"] == "contact_list":
            block.update(needed=3, optional=2, more_note="Five is a good number, but you can add more.")
        if block["id"] == "contacts-intro":
            block["body"] = block["body"].replace("at least 5 people", "at least 3 people")
    onboarding["gate"]["clauses"] = [
        {"type": "links_issued", "block": "contacts", "min": 3, "message": ADD_THREE} if clause["message"] == ADD_FIVE
        else clause
        for clause in onboarding["gate"]["clauses"]
    ]


# Sections 3–5, each a part of the workbook to download (tickets 40 and 58)

# ✨ The sections done on paper, in order, each with its title on the hub, its number and its download's address.
ON_PAPER = ("shape", "calling", "growth")
TITLES = {
    "designed": "How you've been designed – your strengths",
    "others": "Your gifts, seen together",
    "shape": "The shape of your life",
    "calling": "Putting your calling into words",
    "growth": "Growth plan",
}
NUMBERS = {"designed": "01", "others": "02", "shape": "03", "calling": "04", "growth": "05", "letter": "06"}
PDFS = {section_id: f"/downloads/{section_id}-pdf/" for section_id in ON_PAPER}
# ✨ The content owner's four workbooks, sent 29 Oct: the first is Section 2's, in place of its reflection, and the
# others Sections 3–5's, by number.
WORKBOOKS = {"others": 1, "shape": 2, "calling": 3, "growth": 4}
SENT = DOCUMENT.parents[1] / "Prototypes for reference" / "Workbook files" / "Workbooks sent 29 Oct"
WORKBOOK_1 = "/downloads/others-pdf/"
SECTION_2 = "/sections/others/"
SECTION_3 = "/sections/shape/"
SECTION_4 = "/sections/calling/"


def through_section_1(client):
    """✨ Onboarding done, then all Section 1 asks, the sort, and Section 1 finished (ticket 87)."""
    answer_onboarding(client)
    complete(client, "onboarding")
    submit_the_sort(client)
    assert complete(client, "designed").status_code == 303
    return client


def through_section_2(client):
    """✨ Section 1 finished, then Section 2."""
    return finish_section_2(through_section_1(client))


def finish_section_2(client):
    """✨ All Section 2 asks: three people's answers and the comparison seen, which opens the first workbook (ADR
    0019), and Section 2 finished."""
    people_answer(client)
    assert press_compare(client).status_code == 303
    assert complete(client, "others").status_code == 303
    return client


def invite_everyone(client):
    """✨ A coach chosen, which makes their link, and three people added, each with their link."""
    choose(client)
    add_people(client, 3)


def through_to_section_3(client):
    """✨ Sections 1 and 2 finished, and a coach and three people given links, which opens Section 3."""
    through_section_2(client)
    invite_everyone(client)
    return client


def signpost_label(block_id, finished=False):
    """✨ A section signpost's button, as the document words it, before or once its section is complete."""
    block = next(block for block in the_pathway_blocks() if block["id"] == block_id)
    return block["finished"]["button_label"] if finished else block["button_label"]


def the_pathway_blocks():
    return [block for section in the_pathway()["content"]["sections"] for block in section["blocks"]]


@pytest.mark.django_db
def test_section_1_opens_the_strengths_evaluation_at_once_and_is_finished_on_it_alone(participant):
    """✨ Its passages have nothing to confirm, so the strengths evaluation opens with the section, and once it is in,
    Section 1 can be finished, with no other person's answer (ticket 87). Its button opens the evaluation until it is
    done, and then the results, as in the faithful port (ticket 61)."""
    answer_onboarding(participant)
    complete(participant, "onboarding")
    button = r'href="{}"[^>]*>\s*{}\s*</a>'
    page = section_1(participant)
    assert 'id="block-gifts-reading"' in page
    assert re.search(button.format("/sections/strengths/", re.escape(signpost_label("strengths-link"))), page)
    assert participant.get("/sections/strengths/").status_code == 200
    complete(participant, "designed")  # ✨ refused until the evaluation is in
    assert "designed" not in Response.objects.get().completed_sections

    submit_the_sort(participant)

    page = section_1(participant)
    assert re.search(button.format("/results/strengths-sort/", re.escape(signpost_label("strengths-link", True))), page)
    assert 'href="/sections/strengths/"' not in page
    assert complete(participant, "designed").status_code == 303
    assert "designed" in Response.objects.get().completed_sections
    assert not ObserverResponse.objects.exists()


@pytest.mark.django_db
def test_once_the_evaluation_is_done_section_1_shows_no_results_and_section_2_the_way_to_the_comparison(
    participant,
):
    """✨ "View my results →" is the way to them, as in the faithful port (fix-5, reversing ticket 57). The way to the
    comparison (ticket 67a) and the first workbook are Section 2's (ticket 87), on the hub too."""
    client = through_section_1(participant)

    page = section_1(client)
    assert "own-results" not in page
    in_section_2 = ("how-others-see-you", "others-pdf")
    for block_id in in_section_2:
        assert f'id="block-{block_id}"' not in page
    page = section_2(client)
    in_order = [page.index(f'id="block-{block_id}"') for block_id in in_section_2]
    assert in_order == sorted(in_order)
    assert "hub-comparison" in hub_entry(client.get("/hub/").content.decode(), TITLES["others"])


COMPARISON_LINK = re.compile(r'(href|action)="/results/strengths-sort/comparison/')


def comparison_row(html, kind):
    """✨ The comparison's row in the hub's or the sidebar's markup (`kind` "hub" or "pathway-nav"), and the markup
    after Section 2's title and before Section 3's, which holds it when it is listed under Section 2."""
    row = re.search(rf'<li class="[^"]*{kind}-comparison.*?</li>', html, re.S).group(0)
    return row, html[html.index(TITLES["others"]) : html.index(TITLES["shape"])]


@pytest.mark.django_db
def test_the_comparisons_row_is_listed_under_section_2_and_locked_with_it(participant, settings):
    """✨ Fix-19: on the hub and in the sidebar, the row is Section 2's, "Locked" with its lock note and leading nowhere
    while Section 2 is locked, and so is every other way to the comparison; once open, the row leads to it (fix-16)."""
    settings.ANVILLE_SIDEBAR = True
    answer_onboarding(participant)
    complete(participant, "onboarding")
    submit_the_sort(participant)
    people_answer(participant)
    hub = main_of(participant.get("/hub/").content.decode())
    sidebar = sidebar_of(participant.get("/sections/designed/").content.decode())

    for html, kind in ((hub, "hub"), (sidebar, "pathway-nav")):
        row, section_2 = comparison_row(html, kind)
        assert row in section_2
        assert "Locked" in row and escape(OPENS_ONCE.format(what_is_left("designed"))) in row
        assert not COMPARISON_LINK.search(html)

    complete(participant, "designed")

    for html, kind in (
        (main_of(participant.get("/hub/").content.decode()), "hub"),
        (sidebar_of(participant.get("/sections/designed/").content.decode()), "pathway-nav"),
    ):
        row, section_2 = comparison_row(html, kind)
        assert row in section_2
        assert "Locked" not in row and COMPARISON_LINK.search(row)
        # ✨ Fix-23: one control, the link or the press, and the arrow at the right like the other open rows
        if kind == "hub":
            assert 'class="srow-arrow"' in row
            assert len(re.findall(r"<a |<button", row)) == 1


@pytest.mark.django_db
def test_once_the_sort_is_in_opening_the_strengths_assessment_opens_the_results(participant):
    """✨ As in the faithful port (fix-13)."""
    answer_onboarding(participant)
    complete(participant, "onboarding")
    submit_the_sort(participant)

    shown = participant.get("/sections/strengths/")

    assert (shown.status_code, shown.url) == (302, "/results/strengths-sort/")


def section_1(client):
    """✨ Section 1's own content, without the sidebar, which lists every section."""
    return main_of(client.get("/sections/designed/").content.decode())


def section_2(client):
    """✨ Section 2's own content, without the sidebar."""
    return main_of(client.get(SECTION_2).content.decode())


@pytest.mark.django_db
def test_section_2_stays_locked_until_section_1_is_finished(participant):
    """✨ Section 2's comparison and first workbook follow Section 1 (ticket 87)."""
    answer_onboarding(participant)
    complete(participant, "onboarding")
    submit_the_sort(participant)
    assert participant.get(SECTION_2).status_code == 302
    assert escape(OPENS_ONCE.format(what_is_left("designed"))) in note_under(participant, "others")

    complete(participant, "designed")

    assert participant.get(SECTION_2).status_code == 200


@pytest.mark.django_db
def test_section_3_stays_locked_until_both_cards_are_complete_and_names_those_still_open(
    participant,
):
    """✨ With Section 1 finished, which Section 3 also requires (ticket 87)."""
    client = through_section_1(participant)
    assert client.get(SECTION_3).status_code == 302
    coach, voices = what_is_left("walk-with-a-coach"), what_is_left("trusted-voices")
    assert escape(OPENS_ONCE.format(f"{coach} and {voices}")) in note_under(client, "shape")

    choose(client)
    assert client.get(SECTION_3).status_code == 302
    assert escape(OPENS_ONCE.format(voices)) in note_under(client, "shape")

    add_people(client, 3)
    assert client.get(SECTION_3).status_code == 200


def do_the_sort(client):
    """✨ The strengths evaluation sent, then Section 1 finished on it (ticket 87)."""
    submit_the_sort(client)
    complete(client, "designed")


# ✨ What Section 3 requires (ticket 87): Section 1 and both side cards, but not Section 2, whose first workbook waits
# on other people's answers (ADR 0019).
SECTION_3_NEEDS = {"Section 1": do_the_sort, "a coach": choose, "three people": lambda client: add_people(client, 3)}


@pytest.mark.django_db
@pytest.mark.parametrize("missing", SECTION_3_NEEDS)
def test_section_3_opens_on_section_1_and_both_cards_with_section_2_unfinished(participant, missing):
    answer_onboarding(participant)
    complete(participant, "onboarding")
    for need, do in SECTION_3_NEEDS.items():
        if need != missing:
            do(participant)
    assert participant.get(SECTION_3).status_code == 302

    SECTION_3_NEEDS[missing](participant)

    assert participant.get(SECTION_3).status_code == 200
    assert "others" not in Response.objects.get().completed_sections


@pytest.mark.django_db
@pytest.mark.parametrize("unfinished", ["others", "shape"])
def test_section_4_is_refused_until_sections_1_2_and_3_are_complete(participant, unfinished):
    """✨ Section 1 is finished first, since Sections 2 and 3 both require it."""
    client = through_section_1(participant)
    people_answer(client)
    press_compare(client)
    invite_everyone(client)
    coach_accepts(client)  # ✨ which Section 4 also waits on (ticket 64)
    for finished in {"others", "shape"} - {unfinished}:
        assert complete(client, finished).status_code == 303
    assert client.get(SECTION_4).status_code == 302

    assert complete(client, unfinished).status_code == 303

    assert client.get(SECTION_4).status_code == 200


def title_of(section_id):
    """✨ A section's title as the document gives it, which is what the hub names it by."""
    return next(section["title"] for section in the_pathway()["content"]["sections"] if section["id"] == section_id)


# ✨ Engine wording around what a lock note names (ticket 79).
OPENS_ONCE = "Opens once you've {}."


def what_is_left(section_id, called=None):
    """✨ What finishing a section takes, as its phrase in the document says it (ticket 79): its title at {title}, at
    {section} `called`, or else what the hub calls it ("Section 1"), and at {min} its links_issued minimum (ticket 81)."""
    section = next(section for section in the_pathway()["content"]["sections"] if section["id"] == section_id)
    called = called or (f"Section {int(section['number'])}" if "number" in section else section["title"])
    issued = [clause["min"] for clause in section.get("gate", {}).get("clauses", []) if clause["type"] == "links_issued"]
    phrase = section["to_finish"].replace("{title}", section["title"]).replace("{section}", called)
    return phrase.replace("{min}", str(issued[0])) if issued else phrase


def note_under(client, section_id):
    """✨ A section's lock note on the hub, its titles' italics left out, so it reads as plain text: the description of
    its "Locked" button (ticket 97), found by its id, as it follows any rows listed within the section."""
    page = client.get("/hub/").content.decode()
    note = re.search(rf'id="lock-note-{section_id}"[^>]*>(.*?)</span>', page, re.S)
    assert note, f"{section_id} has no lock note"
    return re.sub(r"</?em>", "", note.group(1))


@pytest.mark.django_db
def test_each_lock_note_names_exactly_what_is_left_in_the_sections_still_unfinished(participant):
    """✨ Each by its phrase in the document (ticket 79), and Sections 1, 2 and 3 named together (ticket 87)."""
    answer_onboarding(participant)
    complete(participant, "onboarding")

    # ✨ Section 4 also waits on the coach, whom its note names after the sections (ticket 64).
    with_the_coach = opening_condition()["with_sections"].replace("{sections}", "{}")
    section_1, coach, voices = map(what_is_left, ["designed", "walk-with-a-coach", "trusted-voices"])
    assert escape(OPENS_ONCE.format(section_1)) in note_under(participant, "others")
    assert escape(OPENS_ONCE.format(f"{section_1}, {coach} and {voices}")) in note_under(participant, "shape")
    assert escape(with_the_coach.format(what_is_left("designed", "Sections 1, 2 and 3"))) in note_under(
        participant, "calling"
    )
    assert escape(OPENS_ONCE.format(what_is_left("calling"))) in note_under(participant, "growth")

    do_the_sort(participant)
    choose(participant)
    assert escape(OPENS_ONCE.format(voices)) in note_under(participant, "shape")

    add_people(participant, 3)
    complete(participant, "shape")
    assert escape(with_the_coach.format(what_is_left("others"))) in note_under(participant, "calling")

    coach_accepts(participant)
    assert escape(OPENS_ONCE.format(what_is_left("others"))) in note_under(participant, "calling")


def test_the_strengths_evaluation_is_locked_only_as_section_1_is_and_opens_with_it():
    """✨ Section 1's passages have nothing to confirm (ticket 87), so its part never waits on reading them: while
    locked, its note is Section 1's own, and it opens with Section 1, before anything is read (fix-9)."""
    sections = track_sections(the_pathway())

    locked = {state.id: state for state in hub_for(sections, {}, completed=[]).sections}
    opened = {state.id: state for state in hub_for(sections, {}, completed=["onboarding"]).sections}

    assert locked["strengths"].is_locked
    assert locked["strengths"].lock_note == locked["designed"].lock_note
    assert not opened["strengths"].is_locked


@pytest.mark.django_db
def test_a_participant_turned_away_from_section_3_for_want_of_the_side_cards_is_told_what_they_still_need(participant):
    """✨ The side cards' "Add at least 3 people." and "Choose a coach and send them their link." gate no press: with
    messages only after a press (ticket 83), their pages list nothing. What they hold back is Section 3, whose address
    leads to the hub, and its lock note there names both."""
    through_section_1(participant)

    turned_away = participant.get("/sections/shape/")

    coach, voices = map(what_is_left, ["walk-with-a-coach", "trusted-voices"])
    assert turned_away.url == "/hub/"
    assert escape(OPENS_ONCE.format(f"{coach} and {voices}")) in note_under(participant, "shape")


@pytest.mark.django_db
def test_everything_that_opens_section_3_is_done_with_no_observer_answers_at_all(participant):
    """✨ Nothing a participant must do to reach Section 3 waits on an observer (ticket 52): it requires Section 1, which
    is finished on the strengths evaluation alone, and not Section 2, whose first workbook does (ADR 0019;
    ticket 87)."""
    client = through_section_1(participant)
    invite_everyone(client)

    assert client.get(SECTION_3).status_code == 200
    assert not ObserverResponse.objects.exists()


@pytest.mark.django_db
def test_the_hub_lists_six_numbered_sections_and_counts_only_them(participant):
    """✨ Section 1 split in two (ticket 87), then the faithful port's titles where the workbook was (ticket 58), and the
    letter, numbered "01" to "06". The count leaves out the part and the side cards (content owner's feedback)."""
    page = to_the_coach_page(participant).get("/hub/").content.decode()  # ✨ Before we begin done, so the hub opens

    for section_id, title in TITLES.items():
        assert f'<span class="srow-number">{NUMBERS[section_id]}</span>' in hub_entry(page, escape(title))
    titles = [escape(title) for title in TITLES.values()] + ["A letter to your future self"]
    assert [page.index(title) for title in titles] == sorted(page.index(title) for title in titles)
    assert "0 of 6 sections complete" in page
    assert "The Workbook" not in page
    assert participant.get("/sections/workbook/").status_code == 404


def pathway_section(section_id):
    return next(section for section in the_pathway()["content"]["sections"] if section["id"] == section_id)


@pytest.mark.parametrize("section_id", WORKBOOKS)
def test_sections_2_to_5_each_offer_their_workbook_exactly_as_the_content_owner_sent_it(section_id):
    """✨ Copied unchanged into the pathway's files, so the participant downloads the content owner's PDF itself."""
    number = WORKBOOKS[section_id]
    files = [block["file"] for block in pathway_section(section_id)["blocks"] if block["type"] == "download"]

    assert files == [f"whatever-you-do-workbook-{number}.pdf"]
    sent = SENT / f"Whatever You Do workbook - Nov ‘26 - {number}.pdf"
    assert (DOCUMENT.parent / "files" / files[0]).read_bytes() == sent.read_bytes()


def test_section_2_is_the_comparison_then_the_first_workbook_waiting_on_it_with_no_reflection_and_no_gate():
    """✨ Section 2's reflection goes (content owner's feedback), the first workbook in its place. Nothing is answered
    in Section 2 any more, so it has no gate: the participant finishes it with its own button, once the workbook
    opens."""
    others = pathway_section("others")

    assert [(block["id"], block["type"]) for block in others["blocks"]] == [
        ("how-others-see-you", "comparison_signpost"),
        ("others-pdf", "download"),
    ]
    assert others["blocks"][1]["after_comparison"]["sort"] == "strengths-sort"
    assert "gate" not in others


@pytest.mark.django_db
@pytest.mark.parametrize("section_id", ON_PAPER)
def test_each_sections_pdf_is_refused_until_it_is_reached_then_served_from_its_page(participant, section_id):
    """✨ Each just short of its section, then with the section reached: Section 3 by everyone invited, the others by
    the sections before finished."""
    client = through_section_1(participant)
    before = ON_PAPER[: ON_PAPER.index(section_id)]
    if before:
        finish_section_2(client)
        invite_everyone(client)
        coach_accepts(client)  # ✨ Section 4 opens once the coach has accepted (ADR 0019)
        for earlier in before[:-1]:
            complete(client, earlier)
    assert client.get(PDFS[section_id]).status_code == 403

    if before:
        complete(client, before[-1])
    else:
        invite_everyone(client)

    assert f'href="{PDFS[section_id]}"' in client.get(f"/sections/{section_id}/").content.decode()
    served = client.get(PDFS[section_id])
    assert served.status_code == 200
    assert served["Content-Type"] == "application/pdf"
    assert b"".join(served.streaming_content).startswith(b"%PDF")


@pytest.mark.django_db
@pytest.mark.parametrize("section_id", ON_PAPER)
def test_each_sections_pdf_link_opens_a_new_tab_without_handing_it_the_app(participant, section_id):
    """✨ The app's tab stays on the section (ticket 84). The link's own text says so as well, which a screen reader
    reads with it; the wording is a hand check."""
    client = through_to_section_3(participant)
    coach_accepts(client)
    for earlier in ON_PAPER[: ON_PAPER.index(section_id)]:
        complete(client, earlier)
    page = client.get(f"/sections/{section_id}/").content.decode()
    link = re.search(rf'<a\b[^>]*href="{PDFS[section_id]}"[^>]*>(.*?)</a>', page, re.S)
    assert link
    assert 'target="_blank"' in link.group(0)
    assert "noopener" in link.group(0)
    assert "new tab" in link.group(1).lower()


@pytest.mark.django_db
def test_sections_4_and_5_and_the_letter_each_open_once_the_one_before_is_finished(participant):
    """✨ In place of the letter after the whole workbook (ticket 58). None of Sections 3–5 has a gate: the participant
    says when each is done, with its own button, and the hub counts it. The coach has accepted, which Section 4 also
    waits on (ADR 0019)."""
    client = through_to_section_3(participant)
    coach_accepts(client)
    in_order = [*ON_PAPER, "letter"]

    for finished, following in zip(in_order, in_order[1:]):
        assert client.get(f"/sections/{following}/").status_code == 302
        done_before = set(Response.objects.get().completed_sections)
        assert complete(client, finished).status_code == 303
        assert set(Response.objects.get().completed_sections) - done_before == {finished}
        assert client.get(f"/sections/{following}/").status_code == 200
    # ✨ Sections 1–5 of the six numbered sections, which alone are counted (ticket 87).
    assert "5 of 6 sections complete" in client.get("/hub/").content.decode()


# Section 4 waits on the coach's acceptance (ADR 0019)


def reissue_coach_link(client):
    """✨ The coach's link made again on the coach page, as the participant does, and its path as shown to copy."""
    issued = client.post(coach_link_action(client, "issue", section="walk-with-a-coach"), follow=True)
    return link_shown(issued.content.decode())


def coach_accepts(client, answer="accept"):
    """✨ The coach answering on a fresh link of theirs, from their own browser."""
    assert answer_as_coach(Client(), reissue_coach_link(client), answer).status_code == 303


def opening_condition():
    """✨ Section 4's opening condition, as authored."""
    calling = next(section for section in the_pathway()["content"]["sections"] if section["id"] == "calling")
    return calling["opens_when"]


def section_4_is_locked(client):
    """✨ Refused at its address, and locked, with no address, on the hub and in its sidebar."""
    hub = client.get("/hub/").content.decode()
    sidebar = sidebar_of(hub)
    return (
        client.get(SECTION_4).status_code == 302
        and "Locked" in hub_entry(hub, TITLES["calling"])
        and "Locked" in section_in(sidebar, TITLES["calling"])
        and SECTION_4 not in sidebar
    )


def change_the_coach(client, change):
    """✨ What takes a coach's acceptance away: the link revoked or made again, or another coach chosen."""
    if change == "revoked":
        client.post(coach_link_action(client, "revoke", section="walk-with-a-coach"))
    elif change == "reissued":
        reissue_coach_link(client)
    else:
        assert choose(client, name="Alex").status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "coach", ["no link", "unanswered", "declined", "accepted then revoked", "accepted then reissued", "changed"]
)
def test_with_sections_1_to_3_complete_section_4_stays_locked_until_the_coach_has_accepted(participant, coach):
    client = through_to_section_3(participant)
    if coach == "no link":
        step(client, "remove")
    elif coach == "declined":
        coach_accepts(client, "decline")
    elif coach.startswith("accepted"):
        coach_accepts(client)
        change_the_coach(client, coach.split()[-1])
    elif coach == "changed":
        coach_accepts(client)
        change_the_coach(client, coach)

    complete(client, "shape")

    assert section_4_is_locked(client)


@pytest.mark.django_db
def test_an_acceptance_on_the_coachs_current_link_opens_section_4_even_once_that_link_has_expired(participant):
    client = through_to_section_3(participant)
    coach_accepts(client)

    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        client.force_login(Response.objects.get().participant)  # ✨ a session lasts two weeks
        complete(client, "shape")

        assert client.get(SECTION_4).status_code == 200


@pytest.mark.django_db
def test_once_an_accepting_coachs_link_has_expired_the_hub_shows_section_4_open_and_no_coach_wait(participant):
    """✨ The hub reads the coach's answer as Section 4's opening condition does, expired or not (fix-2)."""
    client = through_to_section_3(participant)
    coach_accepts(client)

    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        client.force_login(Response.objects.get().participant)  # ✨ a session lasts two weeks
        complete(client, "shape")
        hub = client.get("/hub/").content.decode()
        panel = next_step_panel(client)

        assert "Locked" not in hub_entry(hub, TITLES["calling"])
        assert not any(escape(heading.format(coach="Sam")) in panel for heading, *_ in COACH_WAIT_WORDING.values())
        assert client.get(SECTION_4).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("change", ["revoked", "reissued", "changed"])
def test_once_section_4_has_opened_it_stays_open_whatever_happens_to_the_coach(participant, change):
    client = through_to_section_3(participant)
    coach_accepts(client)
    complete(client, "shape")
    assert client.get(SECTION_4).status_code == 200

    change_the_coach(client, change)

    assert client.get(SECTION_4).status_code == 200
    assert "Locked" not in hub_entry(client.get("/hub/").content.decode(), TITLES["calling"])


@pytest.mark.django_db
def test_a_section_4_the_acceptance_opened_stays_open_once_the_coach_withdraws_it_at_once(participant):
    """✨ ADR 0024: an opening condition, once met, is not taken back (ADR 0019), even when the coach withdraws, and is
    deleted, before the participant has loaded a page since accepting."""
    client = through_to_section_3(participant)
    complete(client, "shape")
    link = reissue_coach_link(client)
    coach = Client()
    assert answer_as_coach(coach, link, "accept").status_code == 303

    assert coach.post(f"{link}withdraw/").status_code == 200

    assert client.get(SECTION_4).status_code == 200
    assert "Locked" not in hub_entry(client.get("/hub/").content.decode(), TITLES["calling"])


@pytest.mark.django_db
def test_section_4s_lock_note_names_the_unfinished_sections_and_the_coach_then_the_coach_alone(participant):
    client = through_to_section_3(participant)
    authored = opening_condition()
    with_sections = authored["with_sections"].replace("{sections}", what_is_left("shape"))
    assert escape(with_sections) in note_under(client, "calling")

    complete(client, "shape")

    coach_only = authored["clauses"][0]["message"]
    assert escape(coach_only) in hub_entry(client.get("/hub/").content.decode(), TITLES["calling"])


# Section 2's first workbook waits for the comparison (ADR 0019; ticket 87)


def people_answer(client, count=3):
    """✨ Three people on the list, each with a link, then the first `count` of them claiming a fresh one and sending the
    whole sort from their own browser; returns each one's browser."""
    add_people(client, 3)
    browsers = []
    for number in range(count):
        browsers.append(Client())
        claim(browsers[-1], issue_link(client, f"Person {number}"))
        assert send(browsers[-1], a_whole_sort()).status_code == 303
    return browsers


def press_compare(client):
    """✨ "Compare with how others see you →", confirmed through the freeze warning where there is one."""
    return client.post("/results/strengths-sort/comparison/visit/", {"confirmed": "yes"})


def to_section_2(client):
    """✨ Onboarding done, the sort sent and Section 1 finished, so Section 2 is open."""
    answer_onboarding(client)
    complete(client, "onboarding")
    do_the_sort(client)
    return client


def workbook_1_wait():
    """✨ What Section 2 says in place of the first workbook while it waits, as the document words it."""
    workbook = next(block for block in pathway_section("others")["blocks"] if block["id"] == "others-pdf")
    return workbook["after_comparison"]["message"]


def serves_workbook_1(client):
    served = client.get(WORKBOOK_1)
    return served.status_code == 200 and b"".join(served.streaming_content).startswith(b"%PDF")


@pytest.mark.django_db
def test_until_the_comparison_is_viewed_section_2_says_why_in_place_of_the_first_workbook_and_refuses_it(participant):
    """✨ Refused at its address too, not only left off the page, as a section's content is until it is reached."""
    client = to_section_2(participant)
    people_answer(client)

    page = section_2(client)

    assert escape(workbook_1_wait()) in page
    assert f'href="{WORKBOOK_1}"' not in page
    # ✨ Its button shown greyed, so what opens is in sight, as the comparison's greyed press is (29 Oct).
    assert '<span class="pill is-waiting" role="link" aria-disabled="true">Download Workbook 1 (PDF)</span>' in page
    assert client.get(WORKBOOK_1).status_code == 403


@pytest.mark.django_db
def test_once_viewed_the_first_workbook_is_offered_and_served_and_still_is_after_withdrawals_unfreeze_collection(
    participant,
):
    client = to_section_2(participant)
    browsers = people_answer(client)
    assert press_compare(client).status_code == 303

    assert f'href="{WORKBOOK_1}"' in section_2(client)
    assert escape(workbook_1_wait()) not in section_2(client)
    assert serves_workbook_1(client)

    withdraw(browsers[0])
    assert Response.objects.get().collection_frozen_at is None

    assert serves_workbook_1(client)


@pytest.mark.django_db
def test_a_press_below_the_minimum_does_not_open_the_first_workbook(participant):
    client = to_section_2(participant)
    people_answer(client, count=2)
    press_compare(client)

    assert client.get(WORKBOOK_1).status_code == 403


@pytest.mark.django_db
def test_section_2_is_finished_by_its_own_button_once_the_comparison_is_viewed_and_not_before(participant):
    """✨ With no gate, the wait is all that holds it (developer's call, 29 Oct), so Section 4, which requires Section
    2, still waits on the minimum of people answering (ADR 0019)."""
    client = to_section_2(participant)
    people_answer(client)

    complete(client, "others")
    assert "others" not in Response.objects.get().completed_sections

    press_compare(client)

    assert complete(client, "others").status_code == 303
    assert "others" in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_a_press_of_section_2s_own_button_refused_with_javascript_says_why_beneath_it(participant):
    """✨ With htmx, only what sits beneath the button comes back (fix-2), so it must name the wait."""
    client = to_section_2(participant)
    people_answer(client)

    refused = client.post("/sections/others/complete/", headers={"HX-Request": "true"})

    assert refused.status_code == 400
    assert escape(workbook_1_wait()) in refused.content.decode()


@pytest.mark.django_db
def test_while_section_2_waits_only_on_the_comparison_the_hubs_next_step_is_the_next_open_section(participant):
    client = to_section_2(participant)
    invite_everyone(client)

    panel = next_step(client.get("/hub/").content.decode())

    assert f'href="{SECTION_3}"' in panel


@pytest.mark.django_db
def test_with_nothing_else_open_the_next_step_waits_on_answers_with_a_button_to_section_2(participant):
    client = to_section_2(participant)
    invite_everyone(client)
    complete(client, "shape")

    panel = next_step(client.get("/hub/").content.decode())

    assert "Waiting on answers" in panel
    document = the_pathway()
    others = next(section for section in document["content"]["sections"] if section["id"] == "others")
    authored, minimum = others["next_step"]["waiting"], minimum_observers(document)
    assert escape(authored.replace("{section}", "Section 2").replace("{minimum}", str(minimum))) in panel
    assert f'href="{SECTION_2}"' in panel


@pytest.mark.django_db
def test_once_the_comparison_is_viewed_section_2_is_the_next_step_by_its_title(participant):
    """✨ Section 2 carries only its waiting sentence, so as the next step it says its title (ticket 87)."""
    client = to_section_2(participant)
    people_answer(client)
    press_compare(client)

    panel = next_step(client.get("/hub/").content.decode())

    assert f"<h2>{TITLES['others']}</h2>" in panel
    assert f'href="{SECTION_2}"' in panel


def nothing_else_open(client, answered):
    """✨ Section 2 waiting only on the comparison, with nothing else open, and `answered` people's sorts in."""
    to_section_2(client)
    invite_everyone(client)
    complete(client, "shape")
    people_answer(client, count=answered)
    return next_step(client.get("/hub/").content.decode())


@pytest.mark.django_db
def test_once_the_minimum_have_answered_the_next_step_is_the_press_on_to_the_comparison(participant):
    """✨ No longer "Waiting on answers" once there is something to compare (sprint-3c-r3-fix-14): the press, through
    the freeze warning, not a link a browser could load ahead of time."""
    panel = nothing_else_open(participant, answered=minimum_observers(the_pathway()))

    assert "Waiting on answers" not in panel
    assert 'action="/results/strengths-sort/comparison/visit/"' in panel
    assert escape(COMPARISON_READY_SENTENCE.replace("{section}", "Section 2")) in panel


@pytest.mark.django_db
def test_below_the_minimum_the_next_step_still_waits_on_answers_and_offers_no_comparison(participant):
    panel = nothing_else_open(participant, answered=minimum_observers(the_pathway()) - 1)

    assert "Waiting on answers" in panel
    assert f'href="{SECTION_2}"' in panel
    assert "comparison" not in panel


@pytest.mark.django_db
def test_with_the_minimum_in_another_open_section_is_still_the_next_step(participant):
    """✨ Only the wait's panel leads to the comparison; the comparison's own row and the voices card offer it beside."""
    client = to_section_2(participant)
    invite_everyone(client)
    people_answer(client)

    panel = next_step(client.get("/hub/").content.decode())

    assert f'href="{SECTION_3}"' in panel


# The hub while Section 4 waits on the coach (ticket 65)

COACH_CARD = "Walk with a coach"


def next_step_panel(client):
    """✨ The hub's next-step panel, whichever it is."""
    page = client.get("/hub/").content.decode()
    return re.search(r'<(section|div) class="panel next [^"]*">.*?</\1>', page, re.S).group()


def button_to(html, label):
    """✨ Where the button or link with this label leads, or None."""
    found = re.search(rf'href="([^"]*)"[^>]*>\s*{label}\b', html)
    return found.group(1) if found else None


def the_coach_page(client):
    """✨ The coach page's address, as the sidebar's "Your coach" gives it."""
    return button_to(sidebar_of(client.get("/hub/").content.decode()), "Your coach")


def revoke_coach_link(client):
    client.post(coach_link_action(client, "revoke", section="walk-with-a-coach"))


# ✨ Each way Section 4 can wait on the coach, as the coach's answer the panel's wording is chosen by and how to get
# there from a coach given a working link: unanswered, declined, and no working link (none made, expired unanswered,
# revoked).
COACH_WAITS = {
    "unanswered": ("waiting", lambda client: None),
    "declined": ("declined", lambda client: coach_accepts(client, "decline")),
    "no link made": (None, lambda client: step(client, "remove")),
    "expired unanswered": (None, lambda client: None),
    "revoked": (None, revoke_coach_link),
}


@pytest.mark.django_db
@pytest.mark.parametrize("wait", COACH_WAITS)
def test_with_nothing_next_and_section_4_waiting_only_on_the_coach_the_panel_names_the_wait(participant, wait):
    client = through_to_section_3(participant)
    answer, do = COACH_WAITS[wait]
    do(client)
    complete(client, "shape")
    later = timezone.now() + timedelta(days=31) if wait == "expired unanswered" else timezone.now()

    with time_machine.travel(later, tick=False):
        client.force_login(Response.objects.get().participant)  # ✨ a session lasts two weeks
        panel = next_step_panel(client)

        heading, sentence = COACH_WAIT_WORDING[answer]
        assert escape(heading.format(coach="Sam")) in panel
        assert escape(sentence.format(section="Section 4", coach="Sam")) in panel
        assert button_to(panel, "Your coach") == the_coach_page(client)
        assert section_4_is_locked(client)


@pytest.mark.django_db
def test_the_panel_is_as_before_while_something_else_is_next(participant):
    client = through_to_section_3(participant)

    panel = next_step_panel(client)

    assert button_to(panel, "Begin") == SECTION_3
    assert button_to(panel, "Your coach") is None
    assert re.findall(r"<(?:a|button)\b", panel) == ["<a"]  # ✨ one way to start Section 3 (ticket 95)


@pytest.mark.django_db
def test_the_panel_is_as_before_while_section_4_also_waits_on_a_section_unfinished(signed_in_client, load_pathway):
    """✨ Section 4 made to require a section that can never open, as a section stands that the hub passes over while it
    waits on others (ADR 0019): nothing is next, and Section 4 waits on more than the coach."""
    document = the_pathway()
    calling = next(section for section in document["content"]["sections"] if section["id"] == "calling")
    calling["requires"].append("growth")  # ✨ which requires Section 4 in turn
    load_pathway(document)
    client = through_to_section_3(signed_in_client)
    complete(client, "shape")

    panel = next_step_panel(client)

    assert "Nothing is waiting for you right now." in panel
    assert button_to(panel, "Your coach") is None


def coach_card(client):
    """✨ The hub's Walk with a coach card."""
    return side_card(client.get("/hub/").content.decode(), COACH_CARD)


# ✨ Where the coach can stand once the card is unlocked: none chosen, a link unanswered, declined, accepted.
COACH_STATES = {
    "no coach": lambda client: None,
    "unanswered": choose,
    "declined": lambda client: (choose(client), coach_accepts(client, "decline")),
    "accepted": lambda client: (choose(client), coach_accepts(client)),
}


@pytest.mark.django_db
@pytest.mark.parametrize("coach", COACH_STATES)
def test_the_coach_cards_button_leads_to_the_coach_page_saying_whether_one_is_chosen(participant, coach):
    client = to_the_coach_page(participant)
    COACH_STATES[coach](client)

    card = coach_card(client)

    shown, not_shown = ("Choose your coach", "See your coach")
    if coach != "no coach":
        shown, not_shown = not_shown, shown
    assert button_to(card, shown) == the_coach_page(client)
    assert button_to(card, not_shown) is None


@pytest.mark.django_db
def test_once_the_coach_is_removed_the_coach_cards_button_asks_for_one_again(participant):
    client = to_the_coach_page(participant)
    choose(client)
    step(client, "remove")

    assert button_to(coach_card(client), "Choose your coach") == the_coach_page(client)


@pytest.mark.django_db
def test_the_five_trusted_voices_cards_button_invites_people_on_its_page(participant):
    client = to_the_coach_page(participant)

    card = side_card(client.get("/hub/").content.decode(), "Five trusted voices")

    assert button_to(card, "Invite people") == CONTACTS_PAGE


def coach_card_lines(client):
    """✨ The words of the Walk with a coach card's paragraphs, in order."""
    lines = re.findall(r"<p[^>]*>(.*?)</p>", coach_card(client), re.S)
    return [" ".join(re.sub(r"<[^>]+>", "", line).split()) for line in lines]


@pytest.mark.django_db
@pytest.mark.parametrize("coach", COACH_STATES)
def test_the_coach_card_says_what_a_coach_is_for_and_that_one_is_needed_whatever_they_have_said(participant, coach):
    """✨ Its authored lead and sentence alone (ticket 95): what Section 4 waits for is the tag's, the lock note's and
    the next step's to say, not a line of the card's."""
    client = through_to_section_3(participant)
    if coach == "no coach":
        step(client, "remove")
    elif coach != "unanswered":
        coach_accepts(client, "decline" if coach == "declined" else "accept")
    sections = the_pathway()["content"]["sections"]
    authored = next(section for section in sections if section["id"] == "walk-with-a-coach")["side_card"]

    assert coach_card_lines(client) == [escape(authored["lead"]), escape(authored["sentence"])]
