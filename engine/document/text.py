# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import re

ROLES = ("participant", "observer", "coach")

# ✨ Whose wording a role falls back on where the document gives it none of its own: a coach reads the observer's, which
# already speaks of the participant by name, as "Definitely not {name}" and "…as they go" do (ticket 118), and then
# the participant's, as an observer does.
FALLS_BACK_ON = {"participant": (), "observer": ("participant",), "coach": ("observer", "participant")}


def text_for(text, role):
    """✨ The wording of a text field for one role.

    A text field is a single string for every role, or wording keyed by role. A blank or missing wording for a role
    means the same as the next it falls back on (`FALLS_BACK_ON`): the observer's the participant's, the coach's the
    observer's and then the participant's.
    """
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role!r}")
    if isinstance(text, str):
        return text
    for each in (role, *FALLS_BACK_ON[role]):
        wording = text.get(each, "")
        if wording.strip():
            return wording
    return text["participant"]


def worded_for(text, role):
    """✨ Whether a text field has wording for `role` other than the participant's: its own, or wording it falls back on
    before the participant's (`FALLS_BACK_ON`), as a coach falls back on an observer's, which speaks of the participant
    by name."""
    if isinstance(text, str):
        return False
    return any(text.get(each, "").strip() for each in (role, *FALLS_BACK_ON[role]) if each != "participant")


# ✨ "you" as a word the participant's name can stand in for, as someone else reads wording written to them: not the
# start of a contraction, which a name would not carry ("How Sam’re seen").
YOU = re.compile(r"\byou\b(?![’'])", re.IGNORECASE)

# ✨ "you" where a name standing in for it would not agree with what follows: a contraction ("you’re", "you’ve") or a
# verb a name takes another form of ("you are", "you have", "you were", "you do"). Such wording needs a sentence of
# its own for someone else to read (code review of 23 Nov).
YOU_A_NAME_CANNOT_TAKE = re.compile(r"\byou(?:[’']|\s+(?:are|were|have|do)\b)", re.IGNORECASE)


def speaking_of(text, name):
    """✨ `text`, written to the participant, as someone else reads it: their `name` in place of each "you" (`YOU`), so
    "How others see you" reads "How others see Sam". "your" and "yourself" are kept as written."""
    return YOU.sub(lambda _: name, text)

