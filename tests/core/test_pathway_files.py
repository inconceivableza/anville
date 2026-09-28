import json
from pathlib import Path

import pytest

from engine.document import validate

PATHWAY_FILES = sorted((Path(__file__).resolve().parents[2] / "pathways").glob("*.json"))


def test_the_repository_holds_at_least_one_pathway_document():
    assert PATHWAY_FILES


@pytest.mark.parametrize("path", PATHWAY_FILES, ids=lambda path: path.name)
def test_every_pathway_document_in_the_repository_is_valid(path):
    assert validate(json.loads(path.read_text(encoding="utf-8"))) == []


# ✨ The faithful port keeps the prototype's wording, which does not say how much is needed.
OWN_WORDING = [path for path in PATHWAY_FILES if path.name != "whatever-you-do-faithful-port.json"]


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
