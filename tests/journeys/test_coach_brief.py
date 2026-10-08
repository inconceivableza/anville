"""✨ Section 1's coach brief (ticket 25a): the guide to the coach's first conversation with the participant, authored
in the pathway document with the sort whose results the coach is shown. The participant can open it beside the consent
to share those results, on their comparison, so they know what their coach has been asked to do; a coach who has
accepted sees it on their link page, before the results.

Nothing is sent: the prototype's "Sent with this" and its placeholder note are not ported (spec, Coach).
"""

import re

import pytest

from tests.journeys.test_answers import participant  # noqa: F401 (a fixture)
from tests.journeys.test_coach_checklist import QUESTION_IDS, choose, text
from tests.journeys.test_coach_link import answer_as_coach, issue_coach_link
from tests.journeys.test_coach_sees_results import (
    SHOWN,
    an_accepted_coach,
    share,
    with_a_result,
    with_a_sort_and_a_coach,
)
from tests.journeys.test_consent import give_consent
from tests.journeys.test_invitations import observer  # noqa: F401 (a fixture, used by name as the coach)
from tests.journeys.test_results import SORT

BRIEF = {
    "title": "Session 1 – Their gifts",
    "purpose": "Help them believe what the assessment is telling them.",
    "length": "45–60 minutes",
    "questions": [{"text": "Which of these results surprised you?"}, {"text": "Which felt obvious?"}],
    "watch_for": [{"text": "People dismiss their strongest gift as nothing special."}],
    "avoid": "Do not treat the assessment as a verdict.",
}

# ✨ Every passage of the brief, as a reader sees it.
PASSAGES = [
    BRIEF["title"],
    BRIEF["purpose"],
    BRIEF["length"],
    *(entry["text"] for entry in BRIEF["questions"]),
    *(entry["text"] for entry in BRIEF["watch_for"]),
    BRIEF["avoid"],
]

# ✨ What the coach's page says only straight after they accept.
THANKS = "will be told"


def with_a_brief():
    """✨ The sort's test pathway with a coach, and the brief on the sort, as Section 1's Strengths assessment holds it."""
    document = with_a_sort_and_a_coach()
    sort = next(block for section in document["content"]["sections"] for block in section["blocks"] if block["id"] == SORT)
    sort["coach_brief"] = BRIEF
    return document


@pytest.fixture
def signed_in(client, participant, load_pathway):  # noqa: F811
    """✨ A participant who has chosen Sam as their coach and completed onboarding, so the sort is open."""
    load_pathway(with_a_brief())
    client.force_login(participant)
    give_consent(client)
    assert choose(client).status_code == 200
    client.post("/sections/onboarding/complete/")
    return client


def brief_panel(page):
    """✨ The brief's panel beside the consent on the comparison, which opens and closes without JavaScript."""
    found = re.search(r"<details[^>]*\bdata-coach-brief\b.*?</details>", page, re.S)
    assert found, "no brief panel on the comparison"
    return found.group(0)


def the_comparison(client):
    page = client.get(f"/results/{SORT}/comparison/")
    assert page.status_code == 200
    return page.content.decode()


def what_the_coach_sees(coach, link):
    """✨ The words on the coach's page, which must open."""
    page = coach.get(link)
    assert page.status_code == 200
    return text(page)


@pytest.mark.django_db
def test_a_coach_who_has_accepted_sees_the_brief_with_the_results_and_only_while_they_are_shared(
    signed_in, participant, observer  # noqa: F811
):
    """✨ The brief comes with what it guides the conversation about, as the mock-up's "What happens next" promises."""
    with_a_result(signed_in, participant)
    link = an_accepted_coach(signed_in, observer)
    before = what_the_coach_sees(observer, link)

    assert share(signed_in).status_code == 303
    shared = what_the_coach_sees(observer, link)

    assert share(signed_in, happy=False).status_code == 303
    withdrawn = what_the_coach_sees(observer, link)

    for passage in PASSAGES:
        assert passage not in before
        assert passage in shared
        assert passage not in withdrawn
    assert shared.index(BRIEF["avoid"]) < shared.index(SHOWN)  # ✨ the brief comes before the results


@pytest.mark.django_db
@pytest.mark.parametrize("coach", ["waiting", "declined"])
def test_a_coach_who_has_not_accepted_sees_no_brief(signed_in, observer, coach):  # noqa: F811
    link = issue_coach_link(signed_in)
    if coach == "declined":
        assert answer_as_coach(observer, link, "decline").status_code == 303

    seen = what_the_coach_sees(observer, link)

    for passage in PASSAGES:
        assert passage not in seen


@pytest.mark.django_db
@pytest.mark.parametrize("coach", ["waiting", "accepted"])
def test_the_participant_can_open_the_brief_beside_the_consent_on_their_comparison(
    signed_in, participant, observer, coach  # noqa: F811
):
    with_a_result(signed_in, participant)
    if coach == "accepted":
        an_accepted_coach(signed_in, observer)

    panel = text(brief_panel(the_comparison(signed_in)))

    for passage in PASSAGES:
        assert passage in panel


@pytest.mark.django_db
def test_the_brief_never_says_it_is_sent(signed_in, participant, observer):  # noqa: F811
    with_a_result(signed_in, participant)
    link = an_accepted_coach(signed_in, observer)
    assert share(signed_in).status_code == 303  # ✨ so the coach's page has the brief to say it of

    for seen in (text(brief_panel(the_comparison(signed_in))), what_the_coach_sees(observer, link)):
        assert not re.search(r"\bsent\b", seen, re.I)


@pytest.mark.django_db
def test_the_coach_is_thanked_only_straight_after_accepting(signed_in, observer):  # noqa: F811
    link = issue_coach_link(signed_in)

    accepted = observer.post(f"{link}answer/", {"answer": "accept", "commitment": QUESTION_IDS}, follow=True)

    assert THANKS in text(accepted)
    assert THANKS not in what_the_coach_sees(observer, link)
