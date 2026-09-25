"""✨ The prototype and the shipped Whatever You Do document, as the tests that hold one to the other read them.

The prototype's construct codes are mapped to the new identifiers here and nowhere else. (Its inverted bucket
integers are mapped once too, in `tests/core/test_scoring.py`, beside the golden sorts that use them.)
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = (ROOT / "Prototype for reference/vibe-coded-prototype.html").read_text(encoding="utf-8")

# ✨ The prototype tags each item with one APEST(d) letter and one two-letter PEP tag.
APEST = {"A": "apostle", "P": "prophet", "E": "evangelist", "S": "shepherd", "T": "teacher", "d": "deacon"}
PEP = {"Po": "ponder", "Id": "ideate", "As": "assess", "Ra": "rally", "Fa": "facilitate", "De": "deliver"}


def whatever_you_do():
    """✨ The shipped pathway document, fresh on each call so a test may alter its copy."""
    return json.loads((ROOT / "pathways/whatever-you-do.json").read_text(encoding="utf-8"))


def js_string(escaped):
    """✨ A JavaScript string literal's contents as the text it stands for (\\u escapes decoded)."""
    return json.loads(f'"{escaped}"')
