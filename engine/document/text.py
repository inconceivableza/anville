# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

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
