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
