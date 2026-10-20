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

import pytest
from django.utils.html import escape

from engine.document.observers import relationship_question
from engine.models import Contact, ObserverResponse, Response
from tests.journeys.test_coach_checklist import choose
from tests.journeys.pages import main_of
from tests.journeys.test_hub import hub_entry, signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.prototype import js_string
from tests.journeys.test_whatever_you_do_faithful_port import (
    A_LETTER,
    A_REFLECTION,
    ADD_FIVE,
    ANSWER_ALL_FOUR,
    BASELINE_STATEMENTS,
    VIEW_THE_COMPARISON,
    add_people,
    answer,
    complete,
    move_past,
    onboarding_pages,
    submit_the_sort,
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
ADD_THREE = "Add at least 3 people."
SEND_THE_COACH = "Choose a coach and send them their link."
# ✨ Before we begin's coach and contacts pages became the hub side cards Walk with a coach and Five trusted voices
# (ticket 50).
COACH_PAGE = "/sections/walk-with-a-coach/"
CONTACTS_PAGE = "/sections/trusted-voices/"
RATINGS_PAGE = "/sections/onboarding/pages/2/"


def the_pathway():
    return json.loads(DOCUMENT.read_text(encoding="utf-8"))


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
    """✨ Section 1 done with everyone invited, then Sections 2, 3 and 4 finished in turn, which is what opens the
    letter."""
    through_to_section_2(client)
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
def test_progress_counts_the_pathways_sections(participant):
    """✨ Before we begin, Section 1 with the Strengths assessment within it, Sections 2, 3 and 4 (ticket 58), the
    letter (ticket 49a), and the side cards Walk with a coach and Five trusted voices (ticket 50). The hub opens once
    Before we begin is done."""
    answer_onboarding(participant)
    complete(participant, "onboarding")

    assert "1 of 9 sections complete" in participant.get("/hub/").content.decode()


@pytest.mark.django_db
def test_walk_with_a_coach_completes_once_the_coach_has_a_link_and_five_trusted_voices_once_three_people_have(
    participant,
):
    """✨ Neither has anything to press (ticket 52): choosing the coach makes their link (ticket 51b), and adding a
    person theirs (ticket 51a)."""
    answer_onboarding(participant)
    complete(participant, "onboarding")
    assert "1 of 9 sections complete" in participant.get("/hub/").content.decode()

    choose(participant)
    assert "2 of 9 sections complete" in participant.get("/hub/").content.decode()

    add_people(participant, 2)
    assert "2 of 9 sections complete" in participant.get("/hub/").content.decode()
    add_people(participant, 3)
    assert "3 of 9 sections complete" in participant.get("/hub/").content.decode()


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
    answer_onboarding(participant)
    complete(participant, "onboarding")

    for slot in SLOTS:
        assert answer(participant, f"bl-{slot}", "2").status_code == 409
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


def test_every_section_but_section_1_says_how_long_it_takes():
    """✨ Which sections say how long they take, not the figures, which are the pathway's and are listed with their
    sources in the spec's time estimates. Section 1 has none: it cannot be finished without the sort, so its own few
    minutes would read as less than the Strengths assessment it leads to. None is a placeholder ("? min")."""
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


def test_the_letter_and_the_closing_ratings_each_say_how_long_they_take():
    """✨ The letter section is the only one with two activities, so each carries its own estimate, on the
    block that starts it. A scripture reading leads into an activity rather than being one (the spec)."""
    estimated = {
        (section["id"], block["id"]): block["estimate"]
        for section in the_pathway()["content"]["sections"]
        for block in section["blocks"]
        if block.get("estimate")
    }

    assert list(estimated) == [("letter", "lt-task"), ("letter", "pl-intro")]
    assert not any("?" in estimate for estimate in estimated.values())


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

    assert saved.url == f"{COACH_PAGE}#block-coach"
    assert "You've chosen Sam" in participant.get(COACH_PAGE).content.decode()
    assert "sam@example.com" not in participant.get(CONTACTS_PAGE).content.decode()


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


def test_the_pathway_is_the_faithful_port_with_a_fifth_rating_and_nothing_else():
    """✨ The fifth rating is added to the faithful port here and the result compared whole, so a change made to
    one document and not the other fails, and so does a slip in the fifth rating itself (its place, its anchors,
    its gate clause, or a message still saying four). The minimum-length messages are reworded the same way,
    the time estimates, checked above, the hub's section numbers, next-step wording and photos and Section 1's results
    are set aside, and so are the downloads in place of Sections 2–4's own blocks and Section 1's way to the
    comparison."""
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
    no_relationship_question(expected)

    assert without_the_comparison_link(
        without_the_next_step_and_photos(
            without_numbers(
                without_the_tie_break(without_the_coach_step(without_estimates(without_the_wizard(the_pathway()))))
            )
        )
    ) == (without_numbers(expected))


def without_the_comparison_link(document):
    """✨ The way to the comparison under Section 1's Strengths assessment card is this pathway's alone (ticket 67a): the
    faithful port reaches the comparison from the results page only, as the original prototype does."""
    for section in document["content"]["sections"]:
        section["blocks"] = [block for block in section["blocks"] if block["type"] != "comparison_link"]
    return document


def without_the_wizard(document):
    """✨ Before we begin is a wizard of two pages here, the reason and then the ratings, and its coach and contacts
    pages became the hub side cards Walk with a coach and Five trusted voices (ticket 50). The faithful port keeps the
    original prototype's one section, so the contacts and their gate clause go back into it on a page of their own,
    and the coach goes, as without the coach step."""
    sections = document["content"]["sections"]
    onboarding = sections[0]
    del onboarding["wizard"]
    onboarding["blocks"] = [block for block in onboarding["blocks"] if block["id"] != "to-ratings"]
    voices = next(section for section in sections if section["id"] == "trusted-voices")
    onboarding["blocks"] += [{"id": "to-contacts", "type": "page_break"}, *voices["blocks"]]
    onboarding["gate"]["clauses"] += voices["gate"]["clauses"]
    sections[:] = [section for section in sections if "side_card" not in section]
    return document


def without_the_next_step_and_photos(document):
    """✨ The hub's next-step wording, its photos and their credits' setting are this pathway's alone (ticket 49b): the
    faithful port takes none."""
    document.pop("photos", None)
    document.pop("show_courtesy_credits", None)
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
    """✨ Sections 2–4 are done on paper here, each from its part of the content owner's workbook, so this pathway keeps
    the faithful port's sections, their ids, titles and order, and offers a PDF in each in place of its in-app blocks
    (ticket 58). What each holds and requires is new, with nothing in the faithful port to compare it with, so it is
    taken as it is; the tests below say what it does. Section 1 is completed on the participant's own work, without the
    comparison visited (ticket 52); Section 2 opens once it and both side cards are complete, each section after it
    once the one before is finished, and the letter waits for Section 4."""
    sections = document["content"]["sections"]
    ours = {section["id"]: section for section in without_estimates(the_pathway())["content"]["sections"]}
    for index, section in enumerate(sections):
        if section["id"] in ON_PAPER:
            sections[index] = {**ours[section["id"]], "title": section["title"]}
    designed = next(section for section in sections if section["id"] == "designed")
    designed["gate"]["clauses"] = [
        clause for clause in designed["gate"]["clauses"] if clause["message"] != VIEW_THE_COMPARISON
    ]
    next(section for section in sections if section["id"] == "letter")["requires"] = ["growth"]


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
    1's Strengths assessment card."""
    for block in document["content"]["sections"][1]["blocks"]:
        if block["id"] == "strengths-link":
            block["body"] = block["body"].replace("at least 5 trusted people", "at least 3 trusted people")
    onboarding = document["content"]["sections"][0]
    for block in onboarding["blocks"]:
        if block["type"] == "contact_list":
            block.update(needed=3, optional=2)
        if block["id"] == "contacts-intro":
            block["body"] = block["body"].replace("at least 5 people", "at least 3 people")
    onboarding["gate"]["clauses"] = [
        {"type": "links_issued", "block": "contacts", "min": 3, "message": ADD_THREE} if clause["message"] == ADD_FIVE
        else clause
        for clause in onboarding["gate"]["clauses"]
    ]


# Sections 2–4, each a part of the workbook to download (tickets 40 and 58)

# ✨ The sections done on paper, in order, each with its title on the hub, its number and its download's address.
ON_PAPER = ("shape", "calling", "growth")
TITLES = {"shape": "The shape of your life", "calling": "Putting your calling into words", "growth": "Growth plan"}
NUMBERS = {"shape": "02", "calling": "03", "growth": "04"}
PDFS = {section_id: f"/downloads/{section_id}-pdf/" for section_id in ON_PAPER}
SECTION_2 = "/sections/shape/"


def through_section_1(client):
    """✨ Onboarding done, then everything Section 1 asks: the participant's own work alone, the reading, the sort and
    the reflection (ticket 52)."""
    answer_onboarding(client)
    complete(client, "onboarding")
    answer(client, "gifts-reading", "true")
    submit_the_sort(client)
    answer(client, "gifts-summary", A_REFLECTION)
    return client


def invite_everyone(client):
    """✨ A coach chosen, which makes their link, and three people added, each with their link."""
    choose(client)
    add_people(client, 3)


def through_to_section_2(client):
    """✨ Section 1 completed, and a coach and three people given links, which opens Section 2."""
    through_section_1(client)
    assert complete(client, "designed").status_code == 303
    invite_everyone(client)
    return client


@pytest.mark.django_db
def test_section_1s_button_opens_the_assessment_until_it_is_done_and_then_the_results(participant):
    """✨ As in the faithful port, whose wording this pathway's matches (ticket 61)."""
    answer_onboarding(participant)
    complete(participant, "onboarding")
    answer(participant, "gifts-reading", "true")
    button = r'href="{}"[^>]*>\s*{}\s*</a>'
    assert re.search(button.format("/sections/strengths/", "Open Strengths Assessment →"), section_1(participant))

    submit_the_sort(participant)

    page = section_1(participant)
    assert re.search(button.format("/results/strengths-sort/", "View my results →"), page)
    assert 'href="/sections/strengths/"' not in page


@pytest.mark.django_db
def test_once_the_assessment_is_done_section_1_shows_no_results_below_its_card_but_the_way_to_the_comparison(
    participant,
):
    """✨ "View my results →" is the way to them, as in the faithful port (fix-5, reversing ticket 57). Under the card,
    the way to the comparison (ticket 67a)."""
    answer_onboarding(participant)
    complete(participant, "onboarding")
    answer(participant, "gifts-reading", "true")
    submit_the_sort(participant)

    page = section_1(participant)

    assert "View my results →" in page
    assert "own-results" not in page
    assert page.index('id="block-strengths-link"') < page.index('id="block-how-others-see-you"')
    assert page.index('id="block-how-others-see-you"') < page.index('id="block-gifts-summary"')


@pytest.mark.django_db
def test_once_the_sort_is_in_opening_the_strengths_assessment_opens_the_results(participant):
    """✨ As in the faithful port (fix-13)."""
    answer_onboarding(participant)
    complete(participant, "onboarding")
    answer(participant, "gifts-reading", "true")
    submit_the_sort(participant)

    shown = participant.get("/sections/strengths/")

    assert (shown.status_code, shown.url) == (302, "/results/strengths-sort/")


def section_1(client):
    """✨ Section 1's own content, without the sidebar, which lists every section."""
    return main_of(client.get("/sections/designed/").content.decode())


@pytest.mark.django_db
def test_section_1_completes_without_the_comparison_visited_and_without_any_link(participant):
    """✨ Reversing ticket 16c (ticket 52): Section 1 is completed on the participant's own work."""
    client = through_section_1(participant)

    assert complete(client, "designed").status_code == 303
    assert not Contact.objects.exists()
    assert Response.objects.get().comparisons_visited == {}


@pytest.mark.django_db
def test_section_2_stays_locked_until_section_1_and_both_cards_are_complete_and_names_those_still_open(
    participant,
):
    client = through_section_1(participant)
    complete(client, "designed")
    assert client.get(SECTION_2).status_code == 302
    assert escape("Opens once you've finished Walk with a coach and Five trusted voices.") in hub_entry(
        client.get("/hub/").content.decode(), TITLES["shape"]
    )

    choose(client)
    assert client.get(SECTION_2).status_code == 302
    assert escape("Opens once you've finished Five trusted voices.") in hub_entry(
        client.get("/hub/").content.decode(), TITLES["shape"]
    )

    add_people(client, 3)
    assert client.get(SECTION_2).status_code == 200


@pytest.mark.django_db
def test_section_2_waits_for_section_1_even_once_both_cards_are_complete(participant):
    answer_onboarding(participant)
    complete(participant, "onboarding")
    invite_everyone(participant)

    assert participant.get(SECTION_2).status_code == 302
    assert escape("Opens once you've finished How you've been designed.") in hub_entry(
        participant.get("/hub/").content.decode(), TITLES["shape"]
    )


@pytest.mark.django_db
def test_everything_that_opens_section_2_is_done_with_no_observer_answers_at_all(participant):
    """✨ Nothing a participant must do to reach Section 2 waits on an observer (ticket 52)."""
    client = through_to_section_2(participant)

    assert client.get(SECTION_2).status_code == 200
    assert not ObserverResponse.objects.exists()


@pytest.mark.django_db
def test_the_hub_lists_sections_2_to_4_with_their_numbers_where_the_workbook_was(participant):
    """✨ The faithful port's titles, numbered "02" to "04", between Section 1 and the letter (ticket 58)."""
    page = to_the_coach_page(participant).get("/hub/").content.decode()  # ✨ Before we begin done, so the hub opens

    for section_id in ON_PAPER:
        assert f'<span class="srow-number">{NUMBERS[section_id]}</span>' in hub_entry(page, TITLES[section_id])
    titles = [escape("How you've been designed"), *TITLES.values(), "A letter to your future self"]
    assert [page.index(title) for title in titles] == sorted(page.index(title) for title in titles)
    assert "The Workbook" not in page
    assert participant.get("/sections/workbook/").status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("section_id", ON_PAPER)
def test_each_sections_pdf_is_refused_until_it_is_reached_then_served_from_its_page(participant, section_id):
    """✨ Each just short of its section, then with the section reached: Section 2 by everyone invited, the others by
    the section before finished."""
    client = through_section_1(participant)
    complete(client, "designed")
    before = ON_PAPER[: ON_PAPER.index(section_id)]
    if before:
        invite_everyone(client)
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
def test_sections_3_and_4_and_the_letter_each_open_once_the_one_before_is_finished(participant):
    """✨ In place of the letter after the whole workbook (ticket 58). None of Sections 2–4 has a gate: the participant
    says when each is done, with its own button, and the hub counts it."""
    client = through_to_section_2(participant)
    in_order = [*ON_PAPER, "letter"]

    for finished, following in zip(in_order, in_order[1:]):
        assert client.get(f"/sections/{following}/").status_code == 302
        done_before = set(Response.objects.get().completed_sections)
        assert complete(client, finished).status_code == 303
        assert set(Response.objects.get().completed_sections) - done_before == {finished}
        assert client.get(f"/sections/{following}/").status_code == 200
    assert "8 of 9 sections complete" in client.get("/hub/").content.decode()
