"""✨ The coach checklist's outcome rule, and what its forms send, as the content owner's mock-up sets them out.

The questions, which of them are critical and why each matters are authored in the pathway document; turning
the answers into an outcome is the engine's (ADR 0003). Nothing here is kept: the answers are opinions about
another person, and are only ever read from a form and worked out again.
"""

from dataclasses import dataclass, field

from django.contrib.humanize.templatetags.humanize import apnumber

from engine.document.answers import AnswerRefused
from engine.document.contacts import NAME_MAX_LENGTH

# ✨ Yes, Not sure and No, as each answer is sent.
ANSWERS = ("yes", "maybe", "no")
# ✨ The most answers other than Yes, and the most Nos, that still leave room for a second thought.
MOST_DOUBTS = 2
MOST_NOS = 1


@dataclass(frozen=True)
class Outcome:
    """✨ "proceed", "confirm" (a second thought) or "stop", and the questions not answered Yes, in authored order.

    `critical_no` says whether a No to a critical question is among them, which the stop screen words apart.
    """

    verdict: str
    flagged: list
    critical_no: bool = field(default=False, compare=False)


def checklist_outcome(questions, answers):
    """✨ Any critical No, two or more Nos, or three or more answers that are not Yes stop; any other answer that
    is not Yes asks for a second thought; all Yes proceeds. A question is soft unless marked critical."""
    flagged = [question["id"] for question in questions if answers[question["id"]] != "yes"]
    nos = [question for question in questions if answers[question["id"]] == "no"]
    critical_no = any(question.get("critical", False) for question in nos)
    if critical_no or len(nos) > MOST_NOS or len(flagged) > MOST_DOUBTS:
        return Outcome("stop", flagged, critical_no)
    return Outcome("confirm" if flagged else "proceed", flagged)


def checklist_answers(questions, posted):
    """✨ Whatever answers a form holds so far, by question, leaving out anything that is not Yes, Not sure or No."""
    answers = {question["id"]: posted.get(f"answer-{question['id']}") for question in questions}
    return {question_id: value for question_id, value in answers.items() if value in ANSWERS}


def checklist_answers_from_form(questions, posted):
    """✨ Every question's answer, by question, or AnswerRefused if any is missing or not one of the three."""
    answers = checklist_answers(questions, posted)
    if len(answers) < len(questions):
        raise AnswerRefused(f"Answer all {apnumber(len(questions))} questions to continue.")
    return answers


def candidate_name_from_form(posted):
    """✨ The candidate's first name, trimmed, or AnswerRefused. Held to a contact's length, since the chosen one
    becomes the coach's contact."""
    name = (posted.get("name") or "").strip()
    if not name:
        raise AnswerRefused("Add their first name to continue.")
    if len(name) > NAME_MAX_LENGTH:
        raise AnswerRefused("That name is too long.")
    return name
