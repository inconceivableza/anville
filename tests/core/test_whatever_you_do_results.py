# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The Whatever You Do results wording and colours, held to the prototype's buildResults().

Wording is read out of the prototype file, so a word mistyped in the migration fails here. Colours are
checked through the stylesheet: the document names a tone, and the stylesheet's :root gives it the
prototype's hex.
"""

import re

from tests.prototype import APEST, PEP, PROTOTYPE, ROOT, js_string, whatever_you_do

STYLESHEET = (ROOT / "frontend/src/styles.css").read_text(encoding="utf-8")


def presentation_of(construct):
    return next(entry for entry in whatever_you_do()["presentation"]["constructs"] if entry["construct"] == construct)


def framework_presentation(framework):
    frameworks = whatever_you_do()["presentation"]["frameworks"]
    return next(entry for entry in frameworks if entry["framework"] == framework)


def prototype_object(name):
    """✨ One of buildResults()'s object literals, such as aD or pepP, as a dict of decoded strings."""
    body = re.search(rf"\b{name}=\{{(.*?)\}}", PROTOTYPE).group(1)
    return {key: js_string(value) for key, value in re.findall(r"(\w+):'((?:[^'\\]|\\.)*)'", body)}


def stylesheet_colour(variable):
    return re.search(rf"--{variable}:\s*(#[0-9a-fA-F]{{6}})\s*;", STYLESHEET).group(1).lower()


def test_the_apest_descriptions_are_the_prototypes_word_for_word():
    descriptions = prototype_object("aD")

    assert {APEST[key]: text for key, text in descriptions.items()} == {
        construct: presentation_of(construct)["description"] for construct in APEST.values()
    }


def test_the_pep_personas_and_descriptions_are_the_prototypes_word_for_word():
    personas, descriptions = prototype_object("pepP"), prototype_object("pepD")

    assert {key: (personas[key], descriptions[key]) for key in PEP.values()} == {
        construct: (presentation_of(construct)["persona"], presentation_of(construct)["description"])
        for construct in PEP.values()
    }


def test_the_headings_and_subtitles_are_the_prototypes_word_for_word():
    shown = re.findall(r'<h3>(.*?)</h3><div class="results-desc">(.*?)</div>', PROTOTYPE)
    (apest_heading, apest_subtitle), (pep_heading, pep_subtitle) = [
        (js_string(heading), js_string(subtitle)) for heading, subtitle in shown[:2]
    ]

    assert (framework_presentation("apest")["heading"], framework_presentation("apest")["subtitle"]) == (
        apest_heading,
        apest_subtitle,
    )
    assert (framework_presentation("pep")["heading"], framework_presentation("pep")["subtitle"]) == (
        pep_heading,
        pep_subtitle,
    )


def test_the_validity_disclaimer_is_the_prototypes_word_for_word():
    disclaimer = re.search(r"<strong>Important:</strong> (.*?)</div>", PROTOTYPE).group(1)

    assert whatever_you_do()["presentation"]["disclaimer"] == f"Important: {js_string(disclaimer)}"


def test_the_results_title_greets_the_participant_as_the_prototype_did():
    assert "<h2>'+saState.name+', here\\u2019s your profile</h2>" in PROTOTYPE
    assert whatever_you_do()["presentation"]["results_title"] == "{name}, here’s your profile"


def test_each_construct_has_the_prototypes_colour_through_its_tone():
    """✨ Each construct's item group takes its tone: APEST(d)'s the prototype's aC, PEP's its pepC. The bars take their
    standing's colour instead (developer's call, 20 Oct)."""
    apest_colours = {APEST[key]: colour.lower() for key, colour in prototype_object("aC").items()}
    pep_colours = {PEP[key]: colour.lower() for key, colour in prototype_object("pepC").items()}

    assert {
        construct: stylesheet_colour(f"tone-{presentation_of(construct)['tone']}")
        for construct in [*APEST.values(), *PEP.values()]
    } == {**apest_colours, **pep_colours}


def test_the_standing_colours_are_the_prototypes_pep_rank_colours_from_the_highest_band_to_less_used():
    """✨ Leading, Strong and Present take the prototype's first three PEP rank colours, darkest green first, and Less
    used its orange, the fourth (developer's call, 20 Oct)."""
    rag = re.findall(r"'(#[0-9A-Fa-f]{6})'", re.search(r"var ragColors=\[(.*?)\]", PROTOTYPE).group(1))

    assert [stylesheet_colour(name) for name in ("standing-1", "standing-2", "standing-3", "standing-below")] == [
        colour.lower() for colour in rag[:4]
    ]
