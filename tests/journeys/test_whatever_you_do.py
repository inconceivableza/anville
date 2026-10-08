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

from engine.models import Contact, ObserverResponse, Response
from tests.journeys.pages import gate_checklist
from tests.journeys.test_coach_checklist import choose
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_invitations import invitation_action, issue_link
from tests.prototype import js_string
from tests.journeys.test_whatever_you_do_faithful_port import (
    A_LETTER,
    A_REFLECTION,
    ADD_FIVE,
    ANSWER_ALL_FOUR,
    BASELINE_STATEMENTS,
    COMPLETE_THE_ASSESSMENT,
    COMPLETE_THE_REFLECTIONS,
    SECTION_1,
    VIEW_THE_COMPARISON,
    add_people,
    answer,
    complete,
    move_past,
    onboarding_pages,
    submit_the_sort,
    visit_the_comparison,
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
# ✨ Two people rather than the prototype's five, for now, so the pathway can be tried without inventing five
# (the developer's call, 2026-09-29).
ADD_TWO = "Add at least 2 people, or leave the list empty to do this later."
COACH_PAGE = "/sections/onboarding/pages/2/"
CONTACTS_PAGE = "/sections/onboarding/pages/3/"


def the_pathway():
    return json.loads(DOCUMENT.read_text(encoding="utf-8"))


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(the_pathway())
    return signed_in_client


def answer_all_five(client, prefix="bl"):
    for slot in SLOTS:
        answer(client, f"{prefix}-{slot}", "7")


def answer_onboarding(client):
    """✨ Everything onboarding requires: the reason for taking the course and all five ratings, then on past the
    coach page to the page of the people who know the participant best, where onboarding is completed."""
    answer(client, "reason", "exploring")
    answer_all_five(client)
    move_past(client, 1)
    move_past(client, 2)


def through_to_the_letter(client):
    """✨ Section 1 done with everyone invited, then the Workbook finished, which is what opens the letter."""
    through_to_the_workbook(client)
    complete(client, "workbook")
    return client


@pytest.mark.django_db
def test_the_fifth_statement_is_asked_after_the_original_prototypes_four(participant):
    page = participant.get("/sections/onboarding/").content.decode()

    for statement in BASELINE_STATEMENTS.values():
        assert escape(statement) in page
    assert page.index(escape(BASELINE_STATEMENTS["bl-plan"])) < page.index(escape(PEACE))
    assert page.count("Strongly disagree") == 5


@pytest.mark.django_db
def test_all_five_ratings_are_needed_before_the_participant_may_continue(participant):
    for slot in PROTOTYPE_SLOTS:
        answer(participant, f"bl-{slot}", "5")

    refused = move_past(participant, 1)

    assert refused.status_code == 400
    assert refused.content.decode().count(ANSWER_ALL_FIVE) == 1
    assert "onboarding" not in Response.objects.get().moved_past_by_section()


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
def test_progress_counts_the_two_new_ratings(participant):
    # ✨ The faithful port's 16 and two more, less Section 3's reading and statement, which went with it (ticket 40).
    assert "0 of 16 answered" in participant.get("/hub/").content.decode()


@pytest.mark.django_db
def test_once_anyone_is_added_onboarding_needs_only_two_for_now(participant):
    answer_onboarding(participant)
    add_people(participant, 1)

    refused = complete(participant, "onboarding")

    assert refused.status_code == 400
    assert ADD_TWO in refused.content.decode()
    add_people(participant, 2)
    assert complete(participant, "onboarding").status_code == 303


@pytest.mark.django_db
def test_the_contact_list_opens_with_two_rows_and_says_two_are_needed(participant):
    answer_onboarding(participant)

    page = participant.get(CONTACTS_PAGE).content.decode()

    assert page.count('name="email"') == 2
    assert "We need at least 2 people whose opinion you trust" in page


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
    """✨ Taken from the workbook, then the homepage, then the original prototype, then what seems reasonable, as the
    spec's time estimates say: the Workbook says what the booklet itself says, and the Strengths assessment what the
    original prototype says of its sort. Section 1 has none: it cannot be finished without the sort, so its own few
    minutes would read as less than the Strengths assessment it leads to."""
    sections = the_pathway()["content"]["sections"]

    assert {section["id"]: section.get("estimate") for section in sections} == {
        "onboarding": "About 10 minutes",
        "designed": None,
        "strengths": "About 10 minutes",
        "workbook": "Three or four sittings of half an hour",
        "letter": "About 15 minutes",
    }


def test_the_letter_and_the_closing_ratings_each_say_how_long_they_take():
    """✨ The letter section is the only one with two activities, so each carries its own estimate, on the
    block that starts it. A scripture reading leads into an activity rather than being one (the spec)."""
    estimated = [
        (section["id"], block["id"], block["estimate"])
        for section in the_pathway()["content"]["sections"]
        for block in section["blocks"]
        if block.get("estimate")
    ]

    assert estimated == [("letter", "lt-task", "About 10 minutes"), ("letter", "pl-intro", "About 5 minutes")]


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
    return next(block for block in document["content"]["sections"][0]["blocks"] if block["type"] == "coach_checklist")


def test_the_coach_step_asks_the_mock_ups_six_questions_word_for_word():
    """✨ Their wording, which three are critical, why each matters, and the coach's side of each for ticket 13."""
    questions = the_coach_step(the_pathway())["questions"]

    assert len(questions) == 6
    assert questions == the_mock_ups_questions()
    assert [question["id"] for question in questions if question["critical"]] == ["faith", "objectivity", "coaching"]


def test_the_coach_page_comes_between_the_starting_ratings_and_the_contact_list():
    """✨ As the original prototype goes from its baseline screen to its mentor screen, then to its contacts."""
    assert onboarding_pages(the_pathway()) == [
        ["reason", "baseline-intro", "bl-bible", "bl-gifts", "bl-call", "bl-plan", "bl-peace"],
        ["coach"],
        ["contacts-intro", "contacts"],
    ]


def to_the_coach_page(client):
    """✨ The reason and the five ratings, then on to the coach page."""
    answer(client, "reason", "exploring")
    answer_all_five(client)
    move_past(client, 1)
    return client


@pytest.mark.django_db
def test_the_coach_page_needs_nothing_to_go_on_from(participant):
    page = to_the_coach_page(participant).get(COACH_PAGE).content.decode()

    assert "Walking with a coach" in page
    assert f'<button type="submit" class="btn btn-secondary btn-full">{escape(SORT_LATER)}</button>' in page
    assert move_past(participant, 2).url == CONTACTS_PAGE


SORT_LATER = "I'll sort this later →"  # ✨ the original prototype's way past its mentor screen without a mentor
CONTINUE_WITH_SAM = '<button type="submit" class="btn btn-primary btn-full">Continue with Sam →</button>'


@pytest.mark.django_db
def test_the_coach_page_goes_on_with_the_coach_once_chosen_and_says_sort_later_once_removed(participant):
    to_the_coach_page(participant)

    saved = choose(participant).content.decode()
    reloaded = participant.get(COACH_PAGE).content.decode()
    removed = participant.post("/coach/coach/", {"step": "remove"}, HTTP_HX_REQUEST="true").content.decode()

    assert CONTINUE_WITH_SAM in saved  # ✨ sent with the checklist, so the button changes without a reload
    assert '<div id="completion" class="completion" hx-swap-oob="true">' in saved
    assert CONTINUE_WITH_SAM in reloaded
    assert f'<button type="submit" class="btn btn-secondary btn-full">{escape(SORT_LATER)}</button>' in removed


@pytest.mark.django_db
def test_choosing_again_the_way_on_still_names_the_coach_kept_not_a_second_continue(participant):
    """✨ The checklist's own "Continue →" sits above the page's way on, so the two must read apart."""
    to_the_coach_page(participant)
    choose(participant)

    choosing_again = participant.post("/coach/coach/", {"step": "restart"}).content.decode()

    assert CONTINUE_WITH_SAM in choosing_again
    assert choosing_again.count(">Continue →</button>") == 1  # ✨ the checklist's own, to its questions


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
    move_past(participant, 2)
    assert "sam@example.com" not in participant.get(CONTACTS_PAGE).content.decode()


# ✨ The observers' notice's one sentence about the coach (ticket 27), whom the faithful port never asks for.
SHOWN_TO_THE_COACH = " {name} may also choose to show this to a trusted third party."


def without_the_coach_step(document):
    """✨ Only this pathway asks for a coach the mock-up's way; the faithful port's own mentor screen is ticket 10b.
    The coach page goes with it, so the break that opened that page goes too, and the skip label of the break that
    closed it, and the privacy notice's sentence saying the participant may show their coach what they see. So does
    the sort's coach brief (ticket 25a), as the faithful port has no coach to read it."""
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
        for block in section["blocks"]:
            if block["id"] == "to-contacts":
                block.pop("skip_label", None)
    return document


def without_estimates(document):
    """✨ The faithful port has no estimates, since the prototype gave none."""
    for section in document["content"]["sections"]:
        section.pop("estimate", None)
        for block in section["blocks"]:
            block.pop("estimate", None)
    return document


def test_the_pathway_is_the_faithful_port_with_a_fifth_rating_and_nothing_else():
    """✨ The fifth rating is added to the faithful port here and the result compared whole, so a change made to
    one document and not the other fails, and so does a slip in the fifth rating itself (its place, its anchors,
    its gate clause, or a message still saying four). The minimum-length messages are reworded the same way,
    the time estimates, checked above, are set aside, and so is the Workbook in place of Sections 2–4."""
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
    two_contacts_for_now(expected)
    the_workbook_in_place_of_sections_2_to_4(expected)

    assert without_the_coach_step(without_estimates(the_pathway())) == expected


def the_workbook_in_place_of_sections_2_to_4(document):
    """✨ Sections 2–4 are done on paper here, so this pathway leaves them out, keeping them in the faithful port, and
    offers the content owner's workbook in their place (ticket 40). The Workbook is new content with nothing in the
    faithful port to compare it with, so it is taken as it is; the tests above say what it does. Section 1 asks for
    the coach's link and two observers' links, which opens the Workbook, and the letter waits for the Workbook."""
    sections = document["content"]["sections"]
    sections[:] = [section for section in sections if section["id"] not in ("shape", "calling", "growth")]
    workbook = next(s for s in without_estimates(the_pathway())["content"]["sections"] if s["id"] == "workbook")
    strengths = next(index for index, section in enumerate(sections) if section["id"] == "strengths")
    sections.insert(strengths + 1, workbook)
    designed = next(section for section in sections if section["id"] == "designed")
    designed["gate"]["clauses"] += [
        {"type": "links_issued", "block": "coach", "min": 1, "message": SEND_THE_COACH},
        {"type": "links_issued", "block": "contacts", "min": 2, "message": SEND_TWO},
    ]
    next(section for section in sections if section["id"] == "letter")["requires"] = ["workbook"]


def two_contacts_for_now(document):
    """✨ The faithful port asks for the prototype's five people; this pathway asks for two, in each place it says so:
    onboarding's list, and Section 1's Strengths assessment card."""
    for block in document["content"]["sections"][1]["blocks"]:
        if block["id"] == "strengths-link":
            block["body"] = block["body"].replace("at least 5 trusted people", "at least 2 trusted people")
    onboarding = document["content"]["sections"][0]
    for block in onboarding["blocks"]:
        if block["type"] == "contact_list":
            block["min_rows"] = 2
        if block["id"] == "contacts-intro":
            block["body"] = block["body"].replace("at least 5 people", "at least 2 people")
    for clause in onboarding["gate"]["clauses"]:
        if clause["message"] == ADD_FIVE:
            clause.update(min=2, message=ADD_TWO)


# The Workbook, in place of Sections 2–4 (ticket 40)

# ✨ One sentence whether or not a coach has been chosen, since skipping the coach in onboarding put the choice off.
SEND_THE_COACH = "Choose a coach and send them their link to continue."
SEND_TWO = "Send at least 2 people their links to continue."
WORKBOOK_PDF = "/downloads/workbook-pdf/"


def issue_the_coachs_link(client):
    """✨ The coach page's "issue" button, as the participant presses it."""
    page = client.get(COACH_PAGE).content.decode()
    issue = re.search(r'formaction="(/invitations/\d+/issue/)"', page).group(1)
    assert client.post(issue).status_code == 303


def through_section_1_without_inviting(client):
    """✨ Onboarding done, then everything Section 1 asks of the participant themselves: the reading, the sort, the
    comparison visited (with no observer answers, its below-minimum explanation) and the reflection."""
    answer_onboarding(client)
    complete(client, "onboarding")
    answer(client, "gifts-reading", "true")
    submit_the_sort(client)
    visit_the_comparison(client)
    answer(client, "gifts-summary", A_REFLECTION)
    return client


def invite_everyone(client):
    """✨ A coach chosen and their link issued, and two people added and each given a link."""
    choose(client)
    issue_the_coachs_link(client)
    add_people(client, 2)
    issue_link(client, "Person 0")
    issue_link(client, "Person 1")


def through_to_the_workbook(client):
    """✨ Section 1 done with everyone invited and completed, which opens the Workbook."""
    through_section_1_without_inviting(client)
    invite_everyone(client)
    assert complete(client, "designed").status_code == 303
    return client


@pytest.mark.django_db
def test_section_1_is_completed_only_once_the_coach_and_two_people_have_their_links(participant):
    """✨ Skipping the coach in onboarding put the choice off until here, so a coach is needed (ticket 40). Naming
    people is not inviting them: it is their working links that count."""
    client = through_section_1_without_inviting(participant)
    choose(client)
    add_people(client, 2)

    refused = complete(client, "designed")

    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode()) == {
        COMPLETE_THE_ASSESSMENT: True,
        VIEW_THE_COMPARISON: True,
        COMPLETE_THE_REFLECTIONS: True,
        SEND_THE_COACH: False,
        SEND_TWO: False,
    }
    issue_the_coachs_link(client)
    issue_link(client, "Person 0")
    assert gate_checklist(complete(client, "designed").content.decode())[SEND_TWO] is False
    issue_link(client, "Person 1")
    assert complete(client, "designed").status_code == 303


@pytest.mark.django_db
def test_a_participant_with_no_coach_is_asked_for_their_coachs_link(participant):
    client = through_section_1_without_inviting(participant)
    add_people(client, 2)
    issue_link(client, "Person 0")
    issue_link(client, "Person 1")

    refused = complete(client, "designed")

    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode())[SEND_THE_COACH] is False


def gate_links(page):
    """✨ The gate's messages that are links, as {message: where it leads}."""
    linked = re.findall(r'<a [^>]*href="([^"]*)"[^>]*>\s*<span class="gate-message">(.*?)</span>', page, re.S)
    return {message: href for href, message in linked}


@pytest.mark.django_db
def test_section_1s_unmet_links_lead_to_the_coach_page_and_the_invitations_page(participant):
    """✨ Ticket 41b: Section 1 says what it is still waiting on, and leads there."""
    client = through_section_1_without_inviting(participant)

    page = client.get(SECTION_1).content.decode()

    assert gate_links(page) == {SEND_THE_COACH: f"{COACH_PAGE}#block-coach", SEND_TWO: "/invitations/"}


@pytest.mark.django_db
def test_a_revoked_link_no_longer_counts(participant):
    client = through_section_1_without_inviting(participant)
    invite_everyone(client)

    client.post(invitation_action(client, "Person 1", "revoke"))

    refused = complete(client, "designed")
    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode())[SEND_TWO] is False


@pytest.mark.django_db
def test_the_workbook_opens_once_section_1_is_complete_without_waiting_on_any_observer(participant):
    client = through_section_1_without_inviting(participant)
    invite_everyone(client)
    assert client.get("/sections/workbook/").status_code == 302

    complete(client, "designed")

    assert client.get("/sections/workbook/").status_code == 200
    assert not ObserverResponse.objects.exists()


@pytest.mark.django_db
def test_the_workbook_pdf_is_refused_until_the_workbook_is_reached_then_served_from_its_page(participant):
    client = through_section_1_without_inviting(participant)
    invite_everyone(client)
    assert client.get(WORKBOOK_PDF).status_code == 403

    complete(client, "designed")

    assert f'href="{WORKBOOK_PDF}"' in client.get("/sections/workbook/").content.decode()
    served = client.get(WORKBOOK_PDF)
    assert served.status_code == 200
    assert served["Content-Type"] == "application/pdf"
    assert b"".join(served.streaming_content).startswith(b"%PDF")


@pytest.mark.django_db
def test_the_letter_opens_once_the_participant_has_finished_the_workbook(participant):
    """✨ In place of after Section 3. The Workbook has no gate: the participant says when they are done."""
    client = through_to_the_workbook(participant)
    assert client.get("/sections/letter/").status_code == 302

    assert complete(client, "workbook").status_code == 303

    assert client.get("/sections/letter/").status_code == 200


@pytest.mark.django_db
def test_sections_2_to_4_are_neither_on_the_hub_nor_reachable(participant):
    """✨ Their content stays in the faithful port; here they are done on paper, in the Workbook. The hub lists only the
    track's sections, so a section that cannot be reached is not on it either."""
    for section_id in ("shape", "calling", "growth"):
        assert participant.get(f"/sections/{section_id}/").status_code == 404
