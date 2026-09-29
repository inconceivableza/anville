"""✨ Choosing a coach, as the content owner's mock-up has it: why the choice matters, the candidate's first name, six
"Do you think …" questions, then an outcome that proceeds, asks for a second thought, or stops.

Nothing from the checklist is kept (ticket 10a). Its answers would record opinions about another person's faith,
which is special category data, and no later step reads them, so they travel only in the form, screen to screen,
and the server works the outcome out from what was posted. A participant who leaves partway starts again.

The block is taken from the Whatever You Do pathway, so these tests also hold its wording to the mock-up's.
"""

import json
import logging
import re
from html import unescape
from pathlib import Path

import pytest

from engine.models import Contact, Response
from tests.documents import pathway_document
from tests.journeys.test_answers import answer, shown
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)

ONBOARDING = "onboarding"
WHATEVER_YOU_DO = Path(__file__).resolve().parents[2] / "pathways" / "whatever-you-do.json"
QUESTION_IDS = ["faith", "knowsYou", "objectivity", "wisdom", "coaching", "time"]
ALL_YES = {question_id: "yes" for question_id in QUESTION_IDS}


def the_coach_checklist():
    document = json.loads(WHATEVER_YOU_DO.read_text(encoding="utf-8"))
    onboarding = document["content"]["sections"][0]
    return next(block for block in onboarding["blocks"] if block["type"] == "coach_checklist")


def with_a_coach_checklist():
    """✨ The test pathway with Whatever You Do's coach checklist at the foot of onboarding, which has no gate."""
    document = pathway_document()
    document["content"]["sections"][0]["blocks"].append(the_coach_checklist())
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(with_a_coach_checklist())
    return signed_in_client


def step(client, to, name="Sam", answers=None, htmx=True, block_id="coach"):
    """✨ Press one of the checklist's buttons, sending what its form holds: the name and any answers so far."""
    form = {"step": to, "name": name, **{f"answer-{key}": value for key, value in (answers or {}).items()}}
    headers = {"HTTP_HX_REQUEST": "true"} if htmx else {}
    return client.post(f"/coach/{block_id}/", form, **headers)


def answered(**changes):
    return {**ALL_YES, **changes}


def checklist_of(page):
    """✨ The checklist's own markup within a page or a swapped-in fragment."""
    return re.search(r'<form id="block-coach".*?</form>', page, re.S).group(0)


def screen(page):
    return re.search(r'<form id="block-coach"[^>]*\sdata-screen="(\w+)"', page).group(1)


def text(response_or_page):
    """✨ What a reader sees: the markup's words with the tags taken out and the spacing evened."""
    page = response_or_page if isinstance(response_or_page, str) else response_or_page.content.decode()
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", page)))


def hidden(page, field):
    found = re.search(rf'<input type="hidden" name="{field}" value="([^"]*)"', checklist_of(page))
    return unescape(found.group(1)) if found else None


def checked(page):
    """✨ The answers the questions screen shows chosen, as {question: value}."""
    return dict(re.findall(r'<input type="radio" name="answer-(\w+)" value="(\w+)" checked', checklist_of(page)))


# The intro


@pytest.mark.django_db
def test_the_intro_says_why_the_choice_matters_and_why_coach_not_mentor(participant):
    page = text(shown(participant, ONBOARDING))

    assert "Walking with a coach" in page
    assert "This choice matters more than any other you'll make in the course." in page
    assert "That only goes somewhere useful if the person walking alongside you is the right one." in page
    assert "It's someone who can't resist solving it for you" in page
    assert "Not what you need Someone who tells you what they'd do in your position" in page
    assert "What you need Someone who asks the questions in the material, listens hard" in page
    assert "We say coach rather than mentor deliberately. A mentor passes on their own experience." in page


@pytest.mark.django_db
def test_the_intro_asks_for_the_candidates_first_name(participant):
    page = shown(participant, ONBOARDING)

    assert screen(page) == "intro"
    assert re.search(r'<input type="text"[^>]*name="name"[^>]*placeholder="Their first name"', checklist_of(page))
    assert "Who are you thinking of asking?" in text(page)
    assert "Just a first name for now. Six quick questions follow" in text(page)
    assert re.search(r'<button type="submit" name="step" value="questions"[^>]*>Continue →</button>', page)


# The questions


@pytest.mark.django_db
def test_continuing_asks_the_six_questions_about_the_candidate_by_name(participant):
    asked = step(participant, "questions", name="Sam")

    assert asked.status_code == 200
    page = asked.content.decode()
    assert screen(page) == "questions"
    assert "About Sam" in text(page)
    assert "There are no right answers here — an honest \"not sure\" is far more useful than an optimistic yes." in text(page)
    assert text(page).count("Do you think Sam…") == 6
    assert "Can ask questions rather than hand out answers?" in text(page)
    assert "Some people genuinely can't resist solving it for you. Be realistic about this one." in text(page)
    assert hidden(page, "name") == "Sam"


@pytest.mark.django_db
def test_each_question_is_answered_yes_not_sure_or_no(participant):
    page = step(participant, "questions").content.decode()

    for question_id in QUESTION_IDS:
        options = re.findall(rf'<input type="radio" name="answer-{question_id}" value="(\w+)"', page)
        assert options == ["yes", "maybe", "no"]
    assert re.findall(r'<input type="radio" name="answer-faith" value="\w+"[^>]*>\s*<span>([^<]*)</span>', page) == [
        "Yes",
        "Not sure",
        "No",
    ]
    assert re.search(r'<button type="submit" name="step" value="outcome"[^>]*>Continue →</button>', page)
    assert "See how it looks" not in page  # ✨ the mock-up's label, addressed to someone trying the mock-up
    assert re.search(r'<button type="submit" name="step" value="intro"[^>]*>Back</button>', page)


@pytest.mark.django_db
def test_the_candidates_name_is_shown_as_typed_never_as_markup(participant):
    page = step(participant, "questions", name="<b>Sam</b>").content.decode()

    assert "<b>Sam</b>" not in page
    assert "About &lt;b&gt;Sam&lt;/b&gt;" in page


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["", "   "])
def test_continuing_without_a_name_is_refused_on_the_intro(participant, name):
    refused = step(participant, "questions", name=name)

    assert refused.status_code == 400
    assert screen(refused.content.decode()) == "intro"
    assert "Add their first name to continue." in text(refused)


@pytest.mark.django_db
def test_back_returns_to_the_intro_keeping_the_name_and_the_answers_so_far(participant):
    back = step(participant, "intro", name="Sam", answers={"faith": "yes", "time": "maybe"}).content.decode()

    assert screen(back) == "intro"
    assert re.search(r'<input type="text"[^>]*name="name"[^>]*value="Sam"', checklist_of(back))
    again = step(participant, "questions", name="Sam", answers={"faith": "yes", "time": "maybe"}).content.decode()
    assert checked(again) == {"faith": "yes", "time": "maybe"}


@pytest.mark.django_db
def test_continuing_before_every_question_is_answered_is_refused_keeping_the_answers(participant):
    partial = {"faith": "yes", "coaching": "no"}

    refused = step(participant, "outcome", answers=partial)

    assert refused.status_code == 400
    assert screen(refused.content.decode()) == "questions"
    assert "Answer all six questions to continue." in text(refused)
    assert checked(refused.content.decode()) == partial


# The outcome


@pytest.mark.django_db
def test_all_yes_says_the_candidate_sounds_like_the_right_person(participant):
    page = step(participant, "outcome", answers=ALL_YES).content.decode()

    assert screen(page) == "proceed"
    assert "Sam sounds like the right person" in text(page)
    assert "You've said yes to all six. That's worth something" in text(page)


@pytest.mark.django_db
def test_one_soft_no_asks_for_a_second_thought_naming_the_answer_and_why_it_matters(participant):
    page = step(participant, "outcome", answers=answered(time="no")).content.decode()

    assert screen(page) == "confirm"
    assert "Worth a second thought" in text(page)
    assert "Most of this looks right, but one thing gave you pause." in text(page)
    assert (
        "Would give you a few unhurried conversations over the next few months — you said no "
        "Good intentions and a full diary produce a coach who cancels twice and then apologises."
    ) in text(page)
    assert "None of this rules Sam out, and it may be worth simply raising it with them." in text(page)
    assert re.search(r'<button type="submit" name="step" value="confident"[^>]*>I’m still confident — ask Sam</button>', page)
    assert re.search(r'<button type="submit" name="step" value="restart"[^>]*>Think about someone else</button>', page)


@pytest.mark.django_db
def test_two_not_sures_are_a_couple_of_things_each_named(participant):
    page = text(step(participant, "outcome", answers=answered(wisdom="maybe", coaching="maybe")))

    assert "Most of this looks right, but a couple of things gave you pause." in page
    assert "Has wisdom you respect — ideally further down the road than you — you weren't sure" in page
    assert "Can ask questions rather than hand out answers — you weren't sure" in page
    assert page.index("Has wisdom you respect") < page.index("Can ask questions rather than hand out answers")


@pytest.mark.django_db
def test_a_critical_no_says_try_someone_else_because_it_is_not_negotiable(participant):
    page = step(participant, "outcome", answers=answered(coaching="no")).content.decode()

    assert screen(page) == "stop"
    assert "Try someone else" in text(page)
    assert (
        "You’ve said no to something that isn’t really negotiable. "
        "That’s no reflection on them — it’s about what this specific process asks for."
    ) in text(page)
    assert "Can ask questions rather than hand out answers — you said no" in text(page)
    assert "This is the commonest way coaching relationships fail." in text(page)
    assert "Think about who else might fit." in text(page)
    assert re.search(r'<button type="submit" name="step" value="restart"[^>]*>Try someone else</button>', page)
    assert re.search(r'<button type="submit" name="step" value="restart"[^>]*>I’ll come back to this</button>', page)
    assert 'value="confident"' not in page


@pytest.mark.django_db
def test_too_many_doubts_say_try_someone_else_because_the_fit_is_not_right(participant):
    page = text(step(participant, "outcome", answers=answered(faith="maybe", wisdom="maybe", time="maybe")))

    assert "There’s enough here to suggest Sam may not be the right fit for this particular job." in page
    assert "isn’t really negotiable" not in page


@pytest.mark.django_db
def test_still_confident_after_a_second_thought_goes_on_without_claiming_all_six_were_yes(participant):
    """✨ The mock-up's "I'm still confident" showed the all-yes screen, saying "You've said yes to all six"."""
    page = step(participant, "confident", answers=answered(time="no")).content.decode()

    assert screen(page) == "proceed"
    assert "Sam sounds like the right person" in text(page)
    assert "You've said yes to all six" not in text(page)


@pytest.mark.django_db
def test_still_confident_cannot_get_past_a_stop(participant):
    """✨ The outcome is worked out again from the answers posted, never taken from the button pressed."""
    page = step(participant, "confident", answers=answered(faith="no")).content.decode()

    assert screen(page) == "stop"


@pytest.mark.django_db
def test_still_confident_with_a_question_unanswered_is_refused(participant):
    refused = step(participant, "confident", answers={"faith": "yes"})

    assert refused.status_code == 400
    assert screen(refused.content.decode()) == "questions"


# Starting again


@pytest.mark.django_db
def test_trying_someone_else_starts_again_with_no_name_and_no_answers(participant):
    page = step(participant, "restart", name="Sam", answers=answered(faith="no")).content.decode()

    assert screen(page) == "intro"
    assert not re.search(r'<input type="text"[^>]*name="name"[^>]*value="[^"]+"', checklist_of(page))
    assert "answer-" not in checklist_of(page)


@pytest.mark.django_db
def test_a_participant_who_leaves_partway_starts_the_questions_again(participant):
    step(participant, "outcome", answers=answered(time="maybe"))

    page = shown(participant, ONBOARDING)

    assert screen(page) == "intro"
    assert "Sam" not in checklist_of(page)


# Nothing is kept


def run_through(client, name="Sam"):
    """✨ Every screen of the checklist, to a second thought and on past it."""
    step(client, "questions", name=name)
    step(client, "intro", name=name, answers={"faith": "maybe"})
    step(client, "outcome", name=name, answers=answered(time="no"))
    step(client, "confident", name=name, answers=answered(time="no"))
    step(client, "restart", name=name, answers=answered(faith="no"))


@pytest.mark.django_db
def test_a_completed_checklist_stores_nothing_for_a_participant_who_has_saved_nothing(participant):
    run_through(participant)

    assert Response.objects.count() == 0
    assert Contact.objects.count() == 0


@pytest.mark.django_db
def test_a_completed_checklist_leaves_the_participants_answers_as_they_were(participant):
    answer(participant, "baseline-bible", "7", section=ONBOARDING)
    before = Response.objects.get()

    run_through(participant)

    after = Response.objects.get()
    assert after.answers == {"baseline-bible": 7}
    assert after.updated_at == before.updated_at
    assert after.completed_sections == before.completed_sections
    assert Contact.objects.count() == 0


@pytest.mark.django_db
def test_the_candidates_name_is_never_logged(participant, caplog):
    caplog.set_level(logging.DEBUG)

    run_through(participant, name="Zebedee")
    step(participant, "questions", name="Zebedee" * 30)  # ✨ and a refused one

    assert "Zebedee" not in caplog.text


@pytest.mark.django_db
def test_the_checklist_does_not_count_towards_progress(participant):
    """✨ It keeps no answer, so there is nothing to count: the test pathway's two, as without it."""
    assert "0 of 2 answered" in participant.get("/").content.decode()


@pytest.mark.django_db
def test_the_coach_step_can_be_skipped_and_blocks_nothing(participant):
    answer(participant, "baseline-bible", "7", section=ONBOARDING)

    assert participant.post(f"/sections/{ONBOARDING}/complete/").status_code == 303
    assert Contact.objects.count() == 0


# With and without JavaScript


@pytest.mark.django_db
def test_with_htmx_each_step_sends_back_only_the_checklist(participant):
    page = step(participant, "questions").content.decode()

    assert page.lstrip().startswith("<form id=\"block-coach\"")
    assert "<h1>" not in page


@pytest.mark.django_db
def test_the_checklist_swaps_itself_and_does_not_autosave(participant):
    """✨ Each screen replaces the last in place. Choosing an answer sends nothing: only its buttons do."""
    page = step(participant, "questions").content.decode()

    form = re.search(r'<form id="block-coach"[^>]*>', page).group(0)
    assert 'hx-post="/coach/coach/"' in form
    assert 'hx-target="this"' in form
    assert 'hx-swap="outerHTML"' in form
    assert "hx-trigger" not in form
    assert "hx-post" not in checklist_of(page).replace(form, "")


@pytest.mark.django_db
def test_without_javascript_each_step_comes_back_as_the_whole_section(participant):
    """✨ Never a redirect: the answers would have to go in the address, where they would be logged."""
    shown_again = step(participant, "outcome", answers=answered(time="no"), htmx=False)

    assert shown_again.status_code == 200
    page = shown_again.content.decode()
    assert "<h1>Before we begin</h1>" in page
    assert screen(page) == "confirm"
    assert page.index('id="block-baseline-bible"') < page.index('id="block-coach"')


@pytest.mark.django_db
def test_without_javascript_a_refusal_comes_back_as_the_whole_section(participant):
    refused = step(participant, "questions", name="", htmx=False)

    assert refused.status_code == 400
    assert "<h1>Before we begin</h1>" in refused.content.decode()
    assert "Add their first name to continue." in text(refused)


# Where the checklist is not open


@pytest.mark.django_db
def test_a_checklist_in_a_locked_section_is_refused(signed_in_client, load_pathway):  # noqa: F811
    document = with_a_coach_checklist()
    onboarding, calling = document["content"]["sections"]
    calling["blocks"].append(onboarding["blocks"].pop())
    load_pathway(document)

    assert step(signed_in_client, "questions").status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("block_id", ["nowhere", "baseline-bible"])
def test_only_a_coach_checklist_takes_its_steps(participant, block_id):
    assert step(participant, "questions", block_id=block_id).status_code == 404


@pytest.mark.django_db
def test_a_step_the_checklist_does_not_have_is_refused(participant):
    assert step(participant, "elsewhere").status_code == 400
