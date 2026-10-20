# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ Loading one of the tie-break's made-up demos (`engine/tie_break_scenarios.py`), a starting profile and a way of
answering its pairs (fix-25), into a participant's stored sort, or handing it to the sort to start from, and what to
show beside it: the answer to give each pair, and what the results should then show. `seed_tie_break` stores it
(`load`); the demo-only choice of a demo profile hands it to the sort, storing nothing until the participant sends it
themselves (`prefill`, fix-23). Both work it forward and check it exactly as the other does."""

from dataclasses import dataclass
from urllib.parse import urlencode

from engine.results import pair_page
from engine.tie_break_scenarios import (
    ANSWERS,
    PROFILES,
    DoesNotFit,
    ScenarioDoesNotHold,
    fit,
    holding,
    seeding,
    summary,
)


@dataclass(frozen=True)
class Choice:
    """✨ One option of the demo-profile choice: its `name`, its summary, and for a way of answering the profiles it
    holds with."""

    name: str
    summary: str
    fits: tuple = ()


@dataclass(frozen=True)
class Offered:
    """✨ What the demo-profile choice offers on a pathway: each starting profile with a combination that holds, each way
    of answering that holds with at least one, the profiles that take no answers, and every combination that holds as
    `(profile, answers)`."""

    profiles: list
    answers: list
    no_pairs: tuple
    combinations: list


@dataclass(frozen=True)
class Guide:
    """✨ What to show beside a loaded demo: its summary; each pair's framework and the answer to give it, in the pair
    screen's own words; and what the results page should then show, each framework's heading, its two leaders with
    their standings and its tie-break note (None where it has none), and the generalist's box (None where it does not
    show)."""

    summary: str
    pairs: list
    results: list
    generalist: dict | None


def offered(document):
    """✨ Every combination that holds on `document`, as the demo-profile choice offers it, in the order PROFILES and
    ANSWERS list them; nothing on a pathway the profiles were not made for, such as one with no tie-break."""
    combinations = holding(document)
    profiles = [
        Choice(name, PROFILES[name].summary) for name in PROFILES if any(profile == name for profile, _ in combinations)
    ]
    answers = [
        Choice(name, ANSWERS[name].summary, tuple(profile for profile, answers in combinations if answers == name))
        for name in ANSWERS
        if any(answers == name for _, answers in combinations)
    ]
    no_pairs = tuple(profile for profile, answers in combinations if answers is None)
    return Offered(profiles=profiles, answers=answers, no_pairs=no_pairs, combinations=combinations)


def refusal(offer, profile, answers):
    """✨ Why the choice of `profile` answered as `answers` (None for none) is not offered, in a short sentence, or None
    where it is."""
    if (profile, answers) in offer.combinations:
        return None
    if profile not in [choice.name for choice in offer.profiles]:
        return "That demo profile is not offered on this pathway."
    try:
        fit(profile, answers)
    except DoesNotFit as problem:
        return str(problem)
    return "That way of answering the pairs is not offered with this profile on this pathway."


def load(response, block_id, profile, answers=None):
    """✨ Store `profile` answered as `answers`, worked forward on the response's pathway, as its sort for `block_id`,
    with its result, and return its Guide. DoesNotFit or ScenarioDoesNotHold, storing nothing, where the two do not
    suit each other or do not hold; the response must have no sort for the block yet."""
    document = response.version.document
    seeded = seeding(document, profile, answers)
    response.submit_sort(block_id, seeded.sort, seeded.scores)
    return _guide(document, summary(profile, answers), seeded)


@dataclass(frozen=True)
class Prefill:
    """✨ A demo as the sort starts from it: its profile and answers (None for none), the address's query naming them,
    the sort it would send untouched (each item's bucket and value), and its Guide."""

    profile: str
    answers: str | None
    query: str
    sort: dict
    guide: Guide


def prefill(document, profile, answers=None):
    """✨ `profile` answered as `answers` as the sort should start from it, storing nothing, provided the two fit and
    hold on `document`, as `offered` would offer them; otherwise None."""
    try:
        seeded = seeding(document, profile, answers)
    except (DoesNotFit, ScenarioDoesNotHold):
        return None
    return Prefill(
        profile=profile,
        answers=answers,
        query=demo_query(profile, answers),
        sort=seeded.sort,
        guide=_guide(document, summary(profile, answers), seeded),
    )


# ✨ The address's fields naming the demo profile the sort starts from and the answers the pairs are guided by (fix-23,
# fix-25), as in `?profile=tied-both&answers=skip`.
PROFILE_FIELD = "profile"
ANSWERS_FIELD = "answers"


def demo_query(profile, answers=None):
    """✨ The address's query naming `profile` and, where given, `answers`."""
    return urlencode({PROFILE_FIELD: profile, **({ANSWERS_FIELD: answers} if answers else {})})


def _guide(document, summary, seeded):
    pairs = []
    for pair, chosen in seeded.questions:
        # ✨ The pair screen's own words, so each answer matches what the participant sees.
        shown = pair_page(document, [pair], 0)
        if chosen is None:
            answer = f"skip (“{shown['skip']}”)"
        else:
            answer = f"choose “{next(o['text'] for o in shown['options'] if o['construct'] == chosen)}”"
        pairs.append((shown["framework"], answer))
    results = [
        {
            "heading": framework["heading"],
            "leaders": ", ".join(f"{bar['text_label']} {bar['standing']}" for bar in framework["bars"][:2]),
            "tie_break": framework["tie_break"],
        }
        for framework in seeded.shown["frameworks"]
    ]
    return Guide(summary=summary, pairs=pairs, results=results, generalist=seeded.shown["generalist"])
