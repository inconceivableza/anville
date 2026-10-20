# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ Loading one of the tie-break's made-up scenarios (`engine/tie_break_scenarios.py`) into a participant's stored
sort, and what to show beside it: the answer to give each pair, and what the results should then show. Both
`seed_tie_break` and the demo-only choice of a demo profile (fix-21) load through here, so each loads the same sort,
worked forward and checked exactly as the other does."""

from dataclasses import dataclass

from engine.results import pair_page
from engine.tie_break_scenarios import SCENARIOS, ScenarioDoesNotHold, scenario_for, seeding


@dataclass(frozen=True)
class Offered:
    """✨ One scenario's variant that holds on a pathway: `key` names it in a form, `on` is None where it takes none."""

    key: str
    name: str
    on: str | None
    summary: str


@dataclass(frozen=True)
class Guide:
    """✨ What to show beside a loaded scenario: its summary; each pair's framework and the answer to give it, in the
    pair screen's own words; and what the results page should then show, each framework's heading, its two leaders
    with their standings and its tie-break note (None where it has none), and the generalist's box (None where it does
    not show)."""

    summary: str
    pairs: list
    results: list
    generalist: dict | None


def offered(document):
    """✨ Every scenario's variant that holds on `document`, in the order `SCENARIOS` lists them; none on a pathway the
    scenarios were not made for, such as one with no tie-break."""
    holding = []
    for name, variants in SCENARIOS.items():
        for on, scenario in variants.items():
            try:
                seeding(document, name, on)
            except ScenarioDoesNotHold:
                continue
            holding.append(Offered(f"{name}:{on}" if on else name, name, on, scenario.summary))
    return holding


def offered_by_key(document, key):
    """✨ The variant a form's `key` names, provided it holds on `document`; otherwise None."""
    return next((variant for variant in offered(document) if variant.key == key), None)


def load(response, block_id, name, on=None):
    """✨ Store the scenario `name`'s variant for `on`, worked forward on the response's pathway, as its sort for
    `block_id`, with its result, and return its Guide. NoSuchVariant or ScenarioDoesNotHold, storing nothing, where it
    has no such variant or does not hold; the response must have no sort for the block yet."""
    document = response.version.document
    seeded = seeding(document, name, on)
    response.submit_sort(block_id, seeded.sort, seeded.scores)
    return _guide(document, scenario_for(name, on).summary, seeded)


def guide(document, name, on=None):
    """✨ The Guide for the scenario `name`'s variant for `on` on `document`, storing nothing; as `load` raises."""
    return _guide(document, scenario_for(name, on).summary, seeding(document, name, on))


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
            "leaders": ", ".join(f"{bar['label']} {bar['standing']}" for bar in framework["bars"][:2]),
            "tie_break": framework["tie_break"],
        }
        for framework in seeded.shown["frameworks"]
    ]
    return Guide(summary=summary, pairs=pairs, results=results, generalist=seeded.shown["generalist"])
