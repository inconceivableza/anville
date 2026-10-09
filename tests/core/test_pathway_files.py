import json
import re
from pathlib import Path

import pytest

from engine.document import BLOCK_TYPES, validate

ROOT = Path(__file__).resolve().parents[2]
PATHWAY_FILES = sorted((ROOT / "pathways").glob("*.json"))


def test_the_repository_holds_at_least_one_pathway_document():
    assert PATHWAY_FILES


@pytest.mark.parametrize("path", PATHWAY_FILES, ids=lambda path: path.name)
def test_every_pathway_document_in_the_repository_is_valid(path):
    assert validate(json.loads(path.read_text(encoding="utf-8"))) == []


def test_the_repository_has_no_licence_while_its_pathways_quote_scripture_by_permission():
    """✨ The scripture is quoted by its publishers' permission, which no licence of ours can pass on, and the ESV's
    notice forbids a Creative Commons one by name (ticket 39). Adding a licence is a decision to make first, and this
    test is changed with it."""
    quoting = [path.name for path in PATHWAY_FILES if json.loads(path.read_text(encoding="utf-8")).get("translations")]
    licences = [path.name for path in ROOT.iterdir() if re.match(r"(LICEN[CS]E|COPYING)", path.name, re.IGNORECASE)]
    licences_not_excluding = [license_file for license_file in licences if "Scripture" not in open(license_file, 'r').read()]

    assert not (quoting and licences_not_excluding), (
        f"{licences} would license the scripture quoted in {quoting}. Decide the licence first: see the spec, "
        "Legalities are parked, not forgotten."
    )


# ✨ The faithful port keeps the prototype's wording, which does not say how much is needed.
OWN_WORDING = [path for path in PATHWAY_FILES if path.name != "whatever-you-do-faithful-port.json"]


WITH_AN_INSTRUMENT = [path for path in PATHWAY_FILES if "instrument" in json.loads(path.read_text(encoding="utf-8"))]


@pytest.mark.parametrize("path", WITH_AN_INSTRUMENT, ids=lambda path: path.name)
def test_an_observer_sorts_the_participants_items_about_them_with_four_in_wording_of_their_own(path):
    """✨ Thirty-two items are shared verbatim; the four that say "you" or "yours" get observer wording, and no item or
    bucket an observer sorts with speaks as the participant or to them (spec, Observers)."""
    document = json.loads(path.read_text(encoding="utf-8"))
    sort_widget = BLOCK_TYPES["sort_assessment"].widget
    participants, observers = sort_widget(document, "participant", "Sam"), sort_widget(document, "observer", "Sam")

    reworded = [mine["id"] for mine, theirs in zip(participants["items"], observers["items"]) if mine != theirs]
    assert reworded == ["a5", "e1", "e3", "t1"]
    shown = [item["text"] for item in observers["items"]] + [bucket["label"] for bucket in observers["buckets"]]
    assert [text for text in shown if re.search(r"\b(you|your|yours|me|my)\b", text, re.IGNORECASE)] == []


@pytest.mark.parametrize("path", OWN_WORDING, ids=lambda path: path.name)
def test_every_minimum_length_message_says_how_much_is_needed(path):
    """✨ A participant told only to write something cannot tell why three words were not enough."""
    document = json.loads(path.read_text(encoding="utf-8"))
    clauses = [
        clause
        for section in document["content"]["sections"]
        for clause in section.get("gate", {}).get("clauses", [])
        if clause["type"] == "min_text_length"
    ]

    silent = [clause["message"] for clause in clauses if f"{clause['min']} characters" not in clause["message"]]
    assert silent == []
