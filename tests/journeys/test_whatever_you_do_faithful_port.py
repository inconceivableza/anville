"""✨ The faithful port of *Whatever You Do*, read as a participant meets it.

Every other journey test builds its own small document. These read `pathways/whatever-you-do-faithful-port.json`
itself, because what is being checked here is the content: the wording migrated from the original prototype,
the gates it asks for, and the locks that follow from its `requires` lists. Nothing here is engine
behaviour that `test_sections.py` does not already cover; it is the slice-1 document doing its job.
"""

import json
import re
from pathlib import Path

import pytest
from django.test import Client
from django.utils.html import escape

from engine.document.blocks import pages_of
from engine.models import Contact, Publication, Response
from tests.journeys.pages import gate_checklist, main_of
from tests.journeys.test_consent import give_consent
from tests.journeys.test_hub import a_fresh_participant, signed_in_client  # noqa: F401  (a fixture, used by name)

DOCUMENT = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do-faithful-port.json"

BASELINE_STATEMENTS = {
    "bl-bible": "I have a detailed understanding of what the Bible teaches about 'work' and 'calling'",
    "bl-gifts": "I have a detailed understanding of what my God-given talents/gifts and limitations are",
    "bl-call": "I have a strong sense of what God's specific 'call' and purpose is for my life",
    "bl-plan": (
        "I have a clear, practical plan for how to pursue God's purpose for my life, "
        "in terms of 'work' / 'calling'"
    ),
}
ANSWER_ALL_FOUR = "Answer all four to continue"
# ✨ The prototype's reasons for taking the course, from its account screen, in its order.
REASONS = {
    "post-secondary": "Considering post-secondary options",
    "graduating": "About to graduate third-level education",
    "job-change": "Considering a job change",
    "redundancy": "Facing redundancy",
    "retirement": "Approaching retirement",
    "exploring": "Generally exploring calling",
    "other": "Other",
}
# ✨ The prototype said only "– please choose" beside the question, and left its button disabled until then.
CHOOSE_A_REASON = "Choose what's bringing you to the course to continue."
# ✨ The prototype left "Save and continue →" disabled until five were added, beside "I'll do this later →".
ADD_FIVE = "Add at least 5 people, or leave the list empty to do this later."
SLOTS = ("bible", "gifts", "call", "plan")  # ✨ each rating's id after its `bl-` or `pl-` prefix
A_STATEMENT = "God seems to have designed me to make difficult things clear."
A_LETTER = "Dear me, remember what you found here."


def the_pathway():
    """✨ The faithful port, fresh each time so a test may edit its copy."""
    return json.loads(DOCUMENT.read_text(encoding="utf-8"))


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(the_pathway())
    return signed_in_client


def version():
    return Publication.current_version().pk


def answer(client, block_id, value):
    return client.post(f"/answers/{block_id}/", {"value": value, "version": version()})


def complete(client, section_id):
    return client.post(f"/sections/{section_id}/complete/")


def move_past(client, page):
    """✨ "Continue →" from one page of onboarding to the next."""
    return client.post(f"/sections/onboarding/pages/{page}/continue/")


def answer_the_baseline(client, prefix="bl"):
    for slot in SLOTS:
        answer(client, f"{prefix}-{slot}", "7")


def answer_onboarding(client):
    """✨ Everything onboarding requires: the reason for taking the course and the baseline, then on to the page
    of the people who know the participant best, where onboarding is completed."""
    answer(client, "reason", "exploring")
    answer_the_baseline(client)
    move_past(client, 1)


def onboarding_pages(document):
    """✨ Onboarding's blocks page by page, by identifier."""
    return [[block["id"] for block in page] for page in pages_of(document["content"]["sections"][0])]


def through_to_the_calling_statement(client):
    """✨ A participant who has done onboarding and opened the calling activity."""
    answer_onboarding(client)
    complete(client, "onboarding")
    answer(client, "s2a-reading", "true")
    return client


def through_to_the_letter(client):
    through_to_the_calling_statement(client)
    answer(client, "cl-statement", A_STATEMENT)
    complete(client, "calling")
    return client


# The reason for taking the course


def reason_options(page):
    select = re.search(r'<select id="answer-reason".*?</select>', page, re.S).group(0)
    return re.findall(r'<option value="([^"]+)">([^<]*)</option>', select)


@pytest.mark.django_db
def test_the_reason_is_asked_first_with_the_prototypes_options_in_its_order(participant):
    page = participant.get("/sections/onboarding/").content.decode()

    assert escape("What's bringing you to the course?") in page
    assert reason_options(page) == [(value, escape(label)) for value, label in REASONS.items()]
    assert page.index('id="answer-reason"') < page.index(escape(BASELINE_STATEMENTS["bl-bible"]))


@pytest.mark.django_db
def test_the_reason_is_the_first_thing_asked_once_consent_is_given(client, django_user_model, load_pathway):
    """✨ The prototype asks it on its account screen; here it comes straight after consent instead, since
    nothing about a participant is kept before they have agreed."""
    load_pathway(the_pathway())
    client.force_login(django_user_model.objects.create_user(username="new", email="new@example.com"))

    landed = client.get(give_consent(client).url, follow=True)

    assert landed.request["PATH_INFO"] == "/sections/onboarding/"
    assert 'id="answer-reason"' in landed.content.decode()


@pytest.mark.django_db
def test_going_back_to_select_asks_for_a_reason_again(participant):
    answer_onboarding(participant)

    answer(participant, "reason", "")

    refused = complete(participant, "onboarding")
    assert refused.status_code == 400
    # ✨ Completed from the contacts' page, which also says what is left unmet on the page before it.
    assert gate_checklist(refused.content.decode()) == {ADD_FIVE: True, CHOOSE_A_REASON: False}


@pytest.mark.django_db
def test_onboarding_ends_with_the_prototypes_continue_and_leads_to_the_hub(participant):
    """✨ The prototype's baseline button reads "Continue →" once all four are answered. Its first run went on into
    Section 1, but completing any section, onboarding included, now leads to the hub (ticket 41b)."""
    assert ">Continue →</button>" in participant.get("/sections/onboarding/").content.decode()
    answer_onboarding(participant)

    assert complete(participant, "onboarding").url == "/hub/"


@pytest.mark.django_db
def test_onboarding_is_not_complete_without_a_reason(participant):
    answer_the_baseline(participant)

    refused = move_past(participant, 1)

    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode()) == {CHOOSE_A_REASON: False, ANSWER_ALL_FOUR: True}
    assert complete(participant, "onboarding").url == "/sections/onboarding/"
    assert "onboarding" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_the_reason_can_be_corrected_after_onboarding_is_complete(participant):
    """✨ Unlike the baseline ratings, which are fixed on completion so the closing ratings have something to meet."""
    answer_onboarding(participant)
    complete(participant, "onboarding")

    assert answer(participant, "reason", "job-change").status_code == 303
    assert Response.objects.get().answers["reason"] == "job-change"


# The four baseline ratings


@pytest.mark.django_db
def test_the_four_baseline_statements_are_asked_with_the_prototypes_wording(participant):
    page = participant.get("/sections/onboarding/").content.decode()

    for statement in BASELINE_STATEMENTS.values():
        assert escape(statement) in page


@pytest.mark.django_db
def test_each_baseline_statement_is_rated_from_one_to_ten_between_its_anchors(participant):
    page = participant.get("/sections/onboarding/").content.decode()

    assert page.count("Strongly disagree") == 4
    assert page.count("Strongly agree") == 4
    for point in range(1, 11):
        assert f'value="{point}"' in page


@pytest.mark.django_db
def test_all_four_baseline_ratings_are_needed_before_the_participant_may_continue(participant):
    for slot in ("bible", "gifts", "call"):
        answer(participant, f"bl-{slot}", "5")

    refused = move_past(participant, 1)

    assert refused.status_code == 400
    assert ANSWER_ALL_FOUR in refused.content.decode()
    assert "onboarding" not in Response.objects.get().moved_past_by_section()


@pytest.mark.django_db
def test_the_four_missing_ratings_are_one_sentence_and_not_four(participant):
    """✨ Four `has_answer` clauses share one message, so the participant reads it once."""
    page = participant.get("/sections/onboarding/").content.decode()

    assert page.count(ANSWER_ALL_FOUR) == 1


@pytest.mark.django_db
def test_the_way_on_opens_once_all_four_are_answered(participant):
    answer_onboarding(participant)

    page = participant.get("/sections/onboarding/").content.decode()
    assert gate_checklist(page) == {CHOOSE_A_REASON: True, ANSWER_ALL_FOUR: True}

    assert complete(participant, "onboarding").status_code == 303


@pytest.mark.django_db
def test_the_four_baseline_ratings_are_fixed_once_onboarding_is_complete(participant):
    """✨ The original prototype's baseline screen cannot be returned to after "Continue", so its ratings stand."""
    answer_onboarding(participant)
    complete(participant, "onboarding")

    for slot in SLOTS:
        assert answer(participant, f"bl-{slot}", "2").status_code == 409


@pytest.mark.django_db
def test_the_four_end_ratings_are_fixed_once_the_letter_is_sent(participant):
    """✨ The original prototype offers its closing questions only until they are answered, then moves on for good."""
    client = through_to_the_letter(participant)
    answer(client, "lt-message", A_LETTER)
    answer_the_baseline(client, prefix="pl")
    complete(client, "letter")

    for slot in SLOTS:
        assert answer(client, f"pl-{slot}", "2").status_code == 409


# The people who know the participant best


def add_people(client, count):
    """✨ Save a contact list of `count` people, with fake details as the prototype's pre-filled rows have."""
    return client.post(
        "/answers/contacts/",
        {
            "name": [f"Person {number}" for number in range(count)],
            "email": [f"person{number}@example.com" for number in range(count)],
            "version": version(),
        },
    )


CONTACTS_PAGE = "/sections/onboarding/pages/2/"


def test_onboarding_is_the_prototypes_baseline_screen_then_its_contacts_screen():
    """✨ Two pages, with the reason on the first as the account screen's question is kept with the baseline."""
    assert onboarding_pages(the_pathway()) == [
        ["reason", "baseline-intro", "bl-bible", "bl-gifts", "bl-call", "bl-plan"],
        ["contacts-intro", "contacts"],
    ]


@pytest.mark.django_db
def test_onboarding_asks_who_knows_the_participant_best_on_a_page_after_the_baseline(participant):
    assert "Who knows you best?" not in participant.get("/sections/onboarding/").content.decode()
    answer_onboarding(participant)

    page = participant.get(CONTACTS_PAGE).content.decode()

    assert escape(BASELINE_STATEMENTS["bl-plan"]) not in page
    assert page.index("Who knows you best?") < page.index('id="block-contacts"')
    assert "We need at least 5 people whose opinion you trust" in page


@pytest.mark.django_db
def test_the_contact_list_opens_with_the_prototypes_five_rows(participant):
    answer_onboarding(participant)

    page = participant.get(CONTACTS_PAGE).content.decode()
    form = re.search(r'<form id="block-contacts".*?</form>', page, re.S).group(0)

    assert len(re.findall(r'<input[^>]*\bname="email"', form)) == 5
    assert "+ Add another person" in form


@pytest.mark.django_db
def test_onboarding_can_be_completed_without_adding_anyone_as_with_the_prototypes_i_will_do_this_later(participant):
    answer_onboarding(participant)

    assert complete(participant, "onboarding").status_code == 303


@pytest.mark.django_db
def test_once_anyone_is_added_onboarding_needs_five_as_the_prototype_did(participant):
    answer_onboarding(participant)
    add_people(participant, 4)

    refused = complete(participant, "onboarding")

    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode()) == {ADD_FIVE: False}
    add_people(participant, 5)
    assert complete(participant, "onboarding").status_code == 303


@pytest.mark.django_db
def test_the_contact_list_can_be_corrected_after_onboarding_is_complete(participant):
    answer_onboarding(participant)
    add_people(participant, 5)
    complete(participant, "onboarding")

    assert add_people(participant, 6).status_code == 303
    assert Contact.objects.count() == 6


# The calling-statement section


@pytest.mark.django_db
def test_the_calling_section_reads_the_passages_and_the_task_migrated_from_the_prototype(participant):
    answer_onboarding(participant)
    complete(participant, "onboarding")

    page = participant.get("/sections/calling/").content.decode()

    assert "First articulate your specific calling" in page
    assert "Matthew 28:18" in page
    assert "Psalm 37:3" in page
    assert escape("I've read these passages and I'm ready to continue") in page


@pytest.mark.django_db
def test_the_statement_activity_waits_for_the_reading_to_be_confirmed(participant):
    answer_onboarding(participant)
    complete(participant, "onboarding")

    page = participant.get("/sections/calling/").content.decode()
    assert "Now write it in your own words." not in page

    answer(participant, "s2a-reading", "true")
    assert "Now write it in your own words." in participant.get("/sections/calling/").content.decode()


@pytest.mark.django_db
def test_the_calling_gate_asks_for_a_statement_of_at_least_ten_characters(participant):
    client = through_to_the_calling_statement(participant)
    answer(client, "cl-statement", "too short")

    refused = complete(client, "calling")

    assert refused.status_code == 400
    assert "Write your calling statement to continue." in refused.content.decode()


@pytest.mark.django_db
def test_a_long_enough_statement_completes_the_calling_section(participant):
    client = through_to_the_calling_statement(participant)

    answer(client, "cl-statement", A_STATEMENT)

    shown = gate_checklist(client.get("/sections/calling/").content.decode())
    assert shown == {"Write your calling statement to continue.": True}
    assert complete(client, "calling").status_code == 303
    assert "calling" in Response.objects.get().completed_sections


# The Strengths assessment, and Section 1 which links to it

SECTION_1 = "/sections/designed/"
STRENGTHS = "/sections/strengths/"
STRENGTHS_LINK = f'href="{STRENGTHS}"'
GIFTS_REFLECTION = "summarise: what gifts and talents has God given you?"
COMPLETE_THE_ASSESSMENT = "Complete the Strengths Assessment to continue."
VIEW_THE_COMPARISON = "View the 'Compare with how others see you' results to continue."
COMPLETE_THE_REFLECTIONS = "Complete the gifts reflections to continue."
A_REFLECTION = "Teaching, and patience with people. Not administration."


def a_whole_sort():
    """✨ Every item placed in "Good at this" at that bucket's seed, as untouched sliders leave it."""
    return {item["id"]: {"bucket": "good-at-this", "value": 65} for item in the_pathway()["instrument"]["items"]}


def submit_the_sort(client):
    return answer(client, "strengths-sort", json.dumps(a_whole_sort()))


def visit_the_comparison(client):
    """✨ The results page's "Compare with how others see you →", which records the visit and leads to the comparison.
    With no observers, as here, that is its below-minimum explanation."""
    return client.post("/results/strengths-sort/comparison/visit/")


def onboarded(client):
    answer_onboarding(client)
    complete(client, "onboarding")
    return client


def through_to_section_1s_activity(client):
    """✨ A participant who has done the baseline and confirmed Section 1's reading."""
    answer(onboarded(client), "gifts-reading", "true")
    return client


@pytest.mark.django_db
def test_the_strengths_assessment_is_its_own_section_opened_by_onboarding_and_section_1s_reading(participant):
    assert participant.get(STRENGTHS).status_code == 302

    page = through_to_section_1s_activity(participant).get(STRENGTHS).content.decode()

    assert 'data-sort="sort-strengths-sort"' in page


@pytest.mark.django_db
def test_the_sort_is_shut_until_section_1s_passages_are_read(participant):
    """✨ As the prototype opens it only from Section 1 (ticket 41b), where ticket 09 had accepted it opening with
    onboarding. A track without Section 1, such as the offline one, still opens it by its own requirements."""
    client = onboarded(participant)

    shut = client.get(STRENGTHS)
    assert (shut.status_code, shut.get("Location")) == (302, "/hub/")
    assert submit_the_sort(client).status_code == 403
    assert "strengths-sort" not in Response.objects.get().answers


@pytest.mark.django_db
def test_a_finished_sort_leads_to_its_results_and_offers_no_retake(participant):
    client = through_to_section_1s_activity(participant)
    submit_the_sort(client)

    page = client.get(STRENGTHS).content.decode()

    assert 'href="/results/strengths-sort/"' in page
    assert "data-sort=" not in page


@pytest.mark.django_db
def test_section_1_reads_the_prototypes_question_and_passages(participant):
    page = onboarded(participant).get(SECTION_1).content.decode()

    assert "The big question" in page
    assert escape("A teaching gift looks different in a school vs in kids' work, but it's still a teaching gift.") in page
    assert "Romans 12:6–8" in page
    assert "the one who does acts of mercy, with cheerfulness." in page
    assert "1 Corinthians 12:8–10, 28–30" in page
    assert "to another the interpretation of tongues." in page
    assert "Do all speak with tongues? Do all interpret?" in page
    assert "1 Peter 4:9–11" in page
    assert "To him belong glory and dominion for ever and ever. Amen." in page
    assert "As you read, reflect: what gifts do you see in yourself?" in page
    assert escape("I've read these passages and I'm ready to continue") in page


@pytest.mark.django_db
def test_section_1s_activity_waits_for_the_reading_to_be_confirmed(participant):
    page = main_of(onboarded(participant).get(SECTION_1).content.decode())

    assert STRENGTHS_LINK not in page
    assert GIFTS_REFLECTION not in page


@pytest.mark.django_db
def test_after_the_reading_section_1_links_to_the_strengths_assessment_by_the_prototypes_button(participant):
    page = main_of(through_to_section_1s_activity(participant).get(SECTION_1).content.decode())

    assert "you sort and rate your strengths across 36 areas" in page
    assert re.search(rf"{STRENGTHS_LINK}[^>]*>\s*Open Strengths Assessment →\s*</a>", page)
    assert "Sort your strengths into buckets, fine-tune the intensity of each" in page
    assert "status-chip status-not-started" in page


@pytest.mark.django_db
def test_section_1s_reflection_waits_for_the_sort_as_in_the_prototype(participant):
    client = through_to_section_1s_activity(participant)
    assert GIFTS_REFLECTION not in client.get(SECTION_1).content.decode()

    submit_the_sort(client)

    page = client.get(SECTION_1).content.decode()
    assert page.index(STRENGTHS_LINK) < page.index(GIFTS_REFLECTION)


@pytest.mark.django_db
def test_section_1s_reflection_cannot_be_written_before_the_sort_is_in(participant):
    refused = answer(through_to_section_1s_activity(participant), "gifts-summary", A_REFLECTION)

    assert refused.status_code == 403
    assert "gifts-summary" not in Response.objects.get().answers


@pytest.mark.django_db
def test_section_1s_reflection_box_carries_the_prototypes_ghost_text(participant):
    client = through_to_section_1s_activity(participant)
    submit_the_sort(client)

    page = client.get(SECTION_1).content.decode()

    assert 'placeholder="Draw on the scripture, your assessment results, and what others have told you..."' in page


@pytest.mark.django_db
def test_the_link_in_section_1_shows_how_far_the_strengths_assessment_has_got(participant):
    client = through_to_section_1s_activity(participant)
    submit_the_sort(client)

    assert "status-chip status-complete" in main_of(client.get(SECTION_1).content.decode())


@pytest.mark.django_db
def test_section_1_cannot_be_completed_before_the_sort_is_in(participant):
    """✨ Nothing after the link is open yet, so, as behind an unconfirmed reading, the page offers no gate messages
    and no way on; the server refuses all the same."""
    refused = complete(through_to_section_1s_activity(participant), "designed")

    assert refused.status_code == 400
    assert "Mark complete" not in refused.content.decode()
    assert "designed" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_section_1_cannot_be_completed_without_the_reflection(participant):
    client = through_to_section_1s_activity(participant)
    submit_the_sort(client)

    refused = complete(client, "designed")

    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode()) == {
        COMPLETE_THE_ASSESSMENT: True,
        VIEW_THE_COMPARISON: False,
        COMPLETE_THE_REFLECTIONS: False,
    }


@pytest.mark.django_db
def test_section_1_cannot_be_completed_before_the_comparison_is_visited(participant):
    client = through_to_section_1s_activity(participant)
    submit_the_sort(client)
    answer(client, "gifts-summary", A_REFLECTION)

    refused = complete(client, "designed")

    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode()) == {
        COMPLETE_THE_ASSESSMENT: True,
        VIEW_THE_COMPARISON: False,
        COMPLETE_THE_REFLECTIONS: True,
    }
    assert "designed" not in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_loading_the_comparison_by_its_address_alone_is_not_a_visit(participant):
    """✨ A browser may load an address before it is opened (Chrome's address bar preloads), so only the participant's
    own press of the button counts, as only their own press completes a section."""
    client = through_to_section_1s_activity(participant)
    submit_the_sort(client)
    answer(client, "gifts-summary", A_REFLECTION)

    assert client.get("/results/strengths-sort/comparison/").status_code == 200
    assert complete(client, "designed").status_code == 400


@pytest.mark.django_db
def test_section_1_is_completed_once_the_sort_is_in_the_comparison_visited_and_the_reflection_written(participant):
    """✨ Visiting the below-minimum explanation counts, or nobody could go on until three observers had answered."""
    client = through_to_section_1s_activity(participant)
    submit_the_sort(client)
    visit_the_comparison(client)
    answer(client, "gifts-summary", A_REFLECTION)

    assert complete(client, "designed").status_code == 303
    assert "designed" in Response.objects.get().completed_sections


@pytest.mark.django_db
def test_completing_section_1_does_not_complete_the_strengths_assessment(participant):
    """✨ Each section is completed by its own explicit act."""
    client = through_to_section_1s_activity(participant)
    submit_the_sort(client)
    visit_the_comparison(client)
    answer(client, "gifts-summary", A_REFLECTION)
    complete(client, "designed")

    assert "strengths" not in Response.objects.get().completed_sections


# The hub: every section, and locks the server enforces


@pytest.mark.django_db
def test_every_section_appears_on_the_hub_with_the_strengths_assessment_after_section_1(participant):
    page = participant.get("/hub/").content.decode()

    assert escape("Section 1: How you've been designed") in page
    assert "Strengths assessment" in page
    assert "Section 2: The shape of your life" in page
    assert "Section 3: Putting your calling into words" in page
    assert "Section 4: Growth plan" in page
    assert "Section 5: A letter to your future self" in page
    assert (
        page.index(escape("Section 1: How you've been designed"))
        < page.index("Strengths assessment")
        < page.index("Section 2: The shape of your life")
    )


@pytest.mark.django_db
def test_the_sections_with_no_activity_yet_still_say_what_they_are_for(participant):
    """✨ Sections 2 and 4 carry their prototype hint and nothing else until their activities are built."""
    onboarded(participant)

    assert "Map out your life, then lay those things over the top" in participant.get(
        "/sections/shape/"
    ).content.decode()


@pytest.mark.django_db
def test_progress_counts_what_the_participant_does_and_not_the_prose_or_the_link(participant):
    page = participant.get("/hub/").content.decode()

    # ✨ the reason, four ratings and the contact list; Section 1's reading and reflection; the sort; the calling
    # reading and statement; the letter and four more
    assert "0 of 16 answered" in page


@pytest.mark.django_db
def test_the_sections_after_the_calling_statement_are_locked_until_it_is_complete(participant):
    answer_onboarding(participant)
    complete(participant, "onboarding")

    for section_id in ("growth", "letter"):
        assert participant.get(f"/sections/{section_id}/").status_code == 302


@pytest.mark.django_db
def test_those_locks_lift_when_the_calling_statement_is_complete(participant):
    through_to_the_letter(participant)

    for section_id in ("growth", "letter"):
        assert participant.get(f"/sections/{section_id}/").status_code == 200


@pytest.mark.django_db
def test_a_locked_sections_content_is_refused_however_the_request_arrives(participant):
    """✨ The lock is decided on the request, so neither the page nor the answer is available early."""
    refused = answer(participant, "lt-message", A_LETTER)

    assert refused.status_code == 403
    assert not Response.objects.exists()


# Section 5: the letter, and the four ratings asked again


@pytest.mark.django_db
def test_the_letter_section_asks_for_the_letter_and_then_the_four_statements_again(participant):
    client = through_to_the_letter(participant)

    page = client.get("/sections/letter/").content.decode()

    assert escape("Write to yourself as you will be in twelve months' time") in page
    assert "Your letter" in page
    for statement in BASELINE_STATEMENTS.values():
        assert escape(statement) in page


@pytest.mark.django_db
def test_the_letter_box_opens_with_the_prototypes_ghost_text(participant):
    page = through_to_the_letter(participant).get("/sections/letter/").content.decode()

    assert re.search(r'<textarea id="answer-lt-message"[^>]*placeholder="Dear me,"', page)


@pytest.mark.django_db
def test_the_letter_cannot_be_sent_without_the_letter_itself(participant):
    client = through_to_the_letter(participant)
    answer_the_baseline(client, prefix="pl")

    refused = complete(client, "letter")

    assert refused.status_code == 400
    assert "Write at least one part of your letter before sealing it." in refused.content.decode()


@pytest.mark.django_db
def test_the_letter_cannot_be_sent_without_all_four_after_ratings(participant):
    client = through_to_the_letter(participant)
    answer(client, "lt-message", A_LETTER)
    for slot in ("bible", "gifts", "call"):
        answer(client, f"pl-{slot}", "8")

    refused = complete(client, "letter")

    assert refused.status_code == 400
    assert refused.content.decode().count(ANSWER_ALL_FOUR) == 1


@pytest.mark.django_db
def test_the_letter_is_sent_once_it_is_written_and_all_four_are_answered(participant):
    client = through_to_the_letter(participant)
    answer(client, "lt-message", A_LETTER)
    answer_the_baseline(client, prefix="pl")

    assert complete(client, "letter").status_code == 303
    assert "letter" in Response.objects.get().completed_sections


# Progress, which belongs to the participant rather than the browser


@pytest.mark.django_db
def test_progress_survives_a_reload(participant):
    answer_the_baseline(participant)

    page = participant.get("/sections/onboarding/").content.decode()

    assert page.count('value="7" checked') == 4


@pytest.mark.django_db
def test_progress_follows_the_participant_to_a_second_device(participant, django_user_model):
    through_to_the_calling_statement(participant)
    answer(participant, "cl-statement", A_STATEMENT)

    second_device = Client()
    second_device.force_login(django_user_model.objects.get(username="participant"))

    assert A_STATEMENT in second_device.get("/sections/calling/").content.decode()
    assert "Complete" in second_device.get("/hub/").content.decode()


# Editing the document: the file is the app's content


@pytest.mark.django_db
def test_editing_a_prompt_in_the_document_changes_the_app_for_a_fresh_participant(client, load_pathway):  # noqa: F811
    load_pathway(the_pathway())
    first = a_fresh_participant(client, "first@example.com")
    answer_onboarding(first)
    complete(first, "onboarding")
    assert "Read these passages before continuing" in first.get("/sections/calling/").content.decode()

    edited = the_pathway()
    calling = next(s for s in edited["content"]["sections"] if s["id"] == "calling")
    next(b for b in calling["blocks"] if b["id"] == "s2a-reading")["heading"] = "Sit with these before you write"
    load_pathway(edited)

    second = a_fresh_participant(client, "second@example.com")
    answer_onboarding(second)
    complete(second, "onboarding")
    page = second.get("/sections/calling/").content.decode()
    assert "Sit with these before you write" in page
    assert "Read these passages before continuing" not in page


@pytest.mark.django_db
def test_a_participant_already_in_progress_stays_on_the_version_they_started(participant, load_pathway):  # noqa: F811
    """✨ Pinning is the behaviour, not a bug: an edit is checked on a participant who has not begun."""
    answer(participant, "bl-bible", "6")

    edited = the_pathway()
    onboarding = edited["content"]["sections"][0]
    next(b for b in onboarding["blocks"] if b["id"] == "baseline-intro")["body"] = "Rewritten after they began."
    load_pathway(edited)

    assert "Rewritten after they began." not in participant.get("/sections/onboarding/").content.decode()
