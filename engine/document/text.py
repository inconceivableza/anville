ROLES = ("participant", "observer")


def text_for(text, role):
    """✨ The wording of a text field for one role.

    A text field is a single string for every role, or wording keyed by role. A blank or missing
    observer wording means the same as the participant's.
    """
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role!r}")
    if isinstance(text, str):
        return text
    wording = text.get(role, "")
    return wording if wording.strip() else text["participant"]
