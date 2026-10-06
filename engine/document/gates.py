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
    "comparison_visited": ("sort",),
}

# ✨ A clause that reads something other than a block's answer names the block types it can read instead.
CLAUSE_BLOCK_TYPES = {
    "links_issued": ("contact_list", "coach_checklist"),
}


def comparison_visit_key(block_id):
    """✨ Where the answers the gate reads hold the participant's visit to a sort's comparison. An identifier
    cannot hold a "/", so this never meets a block's own answer."""
    return f"{block_id}/comparison"


def links_issued_key(block_id):
    """✨ Where the answers the gate reads hold how many of a block's people have a working link: a contact list's
    observers, or a coach checklist's coach. Like `comparison_visit_key`, never a block's own answer."""
    return f"{block_id}/links"


def gate_passes(section, answers):
    """✨ Whether this section may be completed. A section with no gate always may."""
    return not unmet(section, answers)


def unmet(section, answers, role="participant"):
    """✨ The authored message of every clause of the whole gate this response does not satisfy, in the order authored.

    Clauses that share a message say it once. An author asking for four ratings writes four clauses and one
    sentence ("Answer all four to continue"), and the participant should read that sentence, not four of it.
    What going on from one page needs is what that page's `checklist` marks unmet.
    """
    messages = (text_for(clause["message"], role) for clause in clauses_of(section) if not _passes(clause, answers))
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
    return CLAUSES[clause["type"]](clause, answers.get(_reads(clause)))


def _reads(clause):
    """✨ What a clause reads: the named block's answer, for `comparison_visited` the visit to its comparison, and for
    `links_issued` how many of its people have a working link."""
    if clause["type"] == "comparison_visited":
        return comparison_visit_key(clause["block"])
    if clause["type"] == "links_issued":
        return links_issued_key(clause["block"])
    return clause["block"]


def clauses_of(section, page=None):
    """✨ A section's gate clauses, or one page's: those naming a block on it. A clause naming a block in another
    section belongs to the last page, where the section is completed."""
    clauses = section.get("gate", {}).get("clauses", [])
    if page is None:
        return clauses
    last = page_count(section)
    return [clause for clause in clauses if (page_of(section, clause["block"]) or last) == page]


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


def _comparison_visited(clause, visit):
    # ✨ Visited in either state: the below-minimum explanation counts, or a participant would wait on three
    # observers before going on (spec, Observers).
    return has_content(visit)


def _links_issued(clause, issued):
    # ✨ Issued, not answered: a participant is never held back waiting on someone else (ticket 40).
    return (issued or 0) >= clause["min"]


CLAUSES = {
    "has_answer": _has_answer,
    "min_text_length": _min_text_length,
    "entry_count": _entry_count,
    "distinct_value_count": _distinct_value_count,
    "every_entry_has": _every_entry_has,
    "comparison_visited": _comparison_visited,
    "links_issued": _links_issued,
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
