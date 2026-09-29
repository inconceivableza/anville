"""✨ Whether a section's gate passes, and what to say to the participant when it does not.

A gate is a list of clauses drawn from the fixed set below, never an expression (ADR 0003). Every clause
must pass, and each one carries its own authored message for the case where that clause is what failed.
A new kind of clause is a code change: an entry in CLAUSES here and its authored shape in the schema.

Nothing in this module touches the database or a request. It reads a section as authored and a
response's answers as stored, so the same evaluation serves the section page, the hub and completion.
"""

from engine.document.blocks import page_count, page_of
from engine.document.text import text_for

# ✨ The answer kinds each clause can read (see blocks.py). None means any block that captures an answer.
# The linter refuses a clause naming a block whose answer it could never read.
CLAUSE_ANSWER_KINDS = {
    "has_answer": None,
    "min_text_length": ("text",),
    "entry_count": ("entries", "contacts"),
    "distinct_value_count": ("entries", "contacts"),
    "every_entry_has": ("entries", "contacts"),
}


def gate_passes(section, answers):
    """✨ Whether this section may be completed. A section with no gate always may."""
    return not unmet(section, answers)


def unmet(section, answers, role="participant", page=None):
    """✨ The authored message of every clause this response does not satisfy, in the order authored.

    Clauses that share a message say it once. An author asking for four ratings writes four clauses and one
    sentence ("Answer all four to continue"), and the participant should read that sentence, not four of it.
    With a `page`, only that page's clauses: what going on from it needs. Without, the whole gate.
    """
    return _unmet(clauses_of(section, page), answers, role)


def _unmet(clauses, answers, role):
    messages = (text_for(clause["message"], role) for clause in clauses if not _passes(clause, answers))
    return list(dict.fromkeys(messages))


def checklist(section, answers, role="participant", page=None):
    """✨ Every authored message with whether it is met, in the order authored, as (message, met) pairs.

    Shown beneath "Mark complete" in place of the unmet messages alone, so nothing comes and goes as answers
    change and the page never shortens under a participant scrolled to its foot. A message several clauses
    share is listed once, and is met only when all of them pass.

    With a `page`, that page's clauses. The last page's also says anything left unmet on an earlier one, since
    completing checks the whole gate: a rating cleared after going back would otherwise refuse without a reason.
    """
    clauses = clauses_of(section, page)
    if page is not None and page == page_count(section):
        # ✨ The whole gate's clauses on this page or left unmet on an earlier one, still in the order authored.
        clauses = [clause for clause in clauses_of(section) if clause in clauses or not _passes(clause, answers)]
    met = {}
    for clause in clauses:
        message = text_for(clause["message"], role)
        met[message] = met.get(message, True) and _passes(clause, answers)
    return list(met.items())


def _passes(clause, answers):
    return CLAUSES[clause["type"]](clause, answers.get(clause["block"]))


def clauses_of(section, page=None):
    """✨ A section's gate clauses, or one page's: those naming a block on it. A clause naming a block in another
    section belongs to the last page, where the section is completed."""
    clauses = section.get("gate", {}).get("clauses", [])
    if page is None:
        return clauses
    return [clause for clause in clauses if (page_of(section, clause["block"]) or page_count(section)) == page]


def _has_answer(clause, answer):
    return has_content(answer)


def _min_text_length(clause, answer):
    return len(str(answer or "").strip()) >= clause["min"]


def _entry_count(clause, answer):
    entries = _entries(answer)
    if clause.get("only_with_content"):
        entries = [entry for entry in entries if _entry_has_content(entry)]
    # ✨ A list the participant may leave for later: none at all, or enough, but never a start left short.
    return len(entries) >= clause["min"] or (clause.get("allow_none", False) and not entries)


def _distinct_value_count(clause, answer):
    values = [_value_of(entry, clause["field"]) for entry in _entries(answer)]
    # ✨ Values are compared as stored, because the ones an author counts are chosen by a widget, not typed.
    return len({_hashable(value) for value in values if has_content(value)}) >= clause["min"]


def _every_entry_has(clause, answer):
    # ✨ "Every" over no entries is true, so an author pairs this clause with a count of entries.
    return all(has_content(_value_of(entry, clause["field"])) for entry in _entries(answer))


CLAUSES = {
    "has_answer": _has_answer,
    "min_text_length": _min_text_length,
    "entry_count": _entry_count,
    "distinct_value_count": _distinct_value_count,
    "every_entry_has": _every_entry_has,
}


def has_content(value):
    """✨ Whether an answer, or one field of an entry, holds anything. A zero is an answer; blank space is not."""
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _entries(answer):
    return answer if isinstance(answer, list) else []


def _entry_has_content(entry):
    values = entry.values() if isinstance(entry, dict) else [entry]
    return any(has_content(value) for value in values)


def _value_of(entry, field):
    return entry.get(field) if isinstance(entry, dict) else None


def _hashable(value):
    return value if isinstance(value, (str, int, float, bool)) else repr(value)
