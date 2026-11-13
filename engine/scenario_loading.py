# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ Loading one of the tie-break's made-up demos (`engine/tie_break_scenarios.py`), a starting profile and a way of
answering its pairs (fix-25), into a participant's stored sort, or handing it to the sort to start from, and what to
show beside it: the answer to give each pair, and what the results should then show. `seed_tie_break` stores it
(`load`); the demo-only choice of a demo profile hands it to the sort, storing nothing until the participant sends it
themselves (`prefill`, fix-23). Both work it forward and check it exactly as the other does. An observer's sort is
handed a profile's observer version (`observer_sort`, ticket 113), which the hub's demo shortcut's made-up people send
too."""

from collections import Counter
from dataclasses import dataclass
from urllib.parse import urlencode

from engine.document.blocks import NOT_SEEN, offers_not_seen
from engine.results import pair_page
from engine.tie_break_scenarios import (
    ANSWERS,
    PROFILES,
    DoesNotFit,
    ScenarioDoesNotHold,
    fit,
    holding,
    seeding,
    sort_with_totals,
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


def observer_sort(document, profile):
    """✨ `profile`'s sort as an observer sends it, storing nothing (ticket 113): every card in the bucket the profile
    places it in, at that bucket's seed, but where the document offers observers "Haven't seen this", the cards an
    observer of a demo profile has not seen (`unseen`) placed there. None for a profile `offered` does not offer on
    `document`, as the participant's choice would not."""
    if profile not in [choice.name for choice in offered(document).profiles]:
        return None
    sort = sort_with_totals(document, PROFILES[profile].totals)
    hidden = unseen(document) if offers_not_seen(document, "observer") else set()
    return {item: dict(NOT_SEEN) if item in hidden else placement for item, placement in sort.items()}


# ✨ An observer of a demo profile has not seen one card in eight (9 of Whatever You Do's 72), and no more than two of
# any one gift's, so the profile still shows through and the observer still counts toward the minimum (ticket 113).
UNSEEN_ONE_IN = 8
UNSEEN_MOST_OF_A_GIFT = 2


def unseen(document):
    """✨ The items an observer of a demo profile has not seen, the same every time: one in eight of the instrument's,
    taken from every eighth item first, then the rest in the document's order, passing over any that would leave a gift
    (a construct an item loads) with more than two not seen."""
    items = document["instrument"]["items"]
    order = sorted(range(len(items)), key=lambda at: ((at + 1) % UNSEEN_ONE_IN != 0, at))
    chosen, per_gift = set(), Counter()
    for at in order:
        if len(chosen) == len(items) // UNSEEN_ONE_IN:
            break
        loads = items[at]["loads"]
        if all(per_gift[gift] < UNSEEN_MOST_OF_A_GIFT for gift in loads):
            chosen.add(items[at]["id"])
            per_gift.update(loads)
    return chosen


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
