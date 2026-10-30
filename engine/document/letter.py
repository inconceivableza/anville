# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A letter to the participant's future self, and the recap beside it (ticket 104): the dates it may be sealed until,
as its block authors them, the date a sealing press sends, and how the letter, the press and the recap are shown.
Pure: no database, no request; the view gathers what they read."""

import calendar
from datetime import date
from typing import NamedTuple

from django.utils import dateformat

from engine.document.text import text_for
from engine.document.tie_break import joined

# ✨ How a date is said to a reader, here and in a reminder's day its link stops working: "4 March 2031".
SHOWN_DATE = "j F Y"


class SealDates(NamedTuple):
    """✨ The date a sealing press offers, and the earliest and latest it accepts."""

    default: date
    earliest: date
    latest: date


def months_after(day, months):
    """✨ The same day `months` whole months on, or the last day of that month where it is shorter: 31 January and a
    month is the end of February, and 29 February and a year is 28 February."""
    month_index = day.month - 1 + months
    year, month = day.year + month_index // 12, month_index % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def seal_dates(block, today):
    """✨ The dates a letter block lets a participant seal it until, counted from `today` in its authored months."""
    months = block["months"]
    return SealDates(*(months_after(today, months[key]) for key in ("default", "earliest", "latest")))


def shown_date(day):
    return dateformat.format(day, SHOWN_DATE)


def opens_on_from_form(block, submitted, today):
    """✨ The date a sealing press chose, or None with the refusal saying the dates it may be: one missing, not a date,
    or outside the block's earliest and latest is refused alike."""
    dates = seal_dates(block, today)
    try:
        chosen = date.fromisoformat(submitted or "")
    except ValueError:
        chosen = None
    if chosen is not None and dates.earliest <= chosen <= dates.latest:
        return chosen, None
    return None, f"Choose a date from {shown_date(dates.earliest)} to {shown_date(dates.latest)}."


def sealed_sentence(block, opens_on):
    """✨ What the letter's box says in its place while it is sealed, its `{date}` the day it opens."""
    return text_for(block["sealed"], "participant").replace("{date}", shown_date(opens_on))


def unsealed_letter(section, sealed_ids):
    """✨ The section's letter while it is not sealed, which the press that finishes the section seals; None for a
    section with none, or once it is sealed. `sealed_ids` are the blocks of the participant's sealed letters."""
    letters = (block for block in section["blocks"] if block["type"] == "letter")
    return next((block for block in letters if block["id"] not in sealed_ids), None)


def seal_press(letter, today, chosen=None):
    """✨ What the press that finishes a section holding an unsealed `letter` offers: its label, the line above it, and
    the date the letter opens on as the date field takes it, `chosen` where a refused press sent one back, else the
    default, with the earliest and latest accepted."""
    dates = seal_dates(letter, today)
    return {
        "label": text_for(letter["seal_label"], "participant"),
        "note": text_for(letter["seal_note"], "participant"),
        "date_label": text_for(letter["date_label"], "participant"),
        **{field: day.isoformat() for field, day in dates._asdict().items()},
        "chosen": chosen if chosen is not None else dates.default.isoformat(),
    }


def letter_shown(block, opens_on, today):
    """✨ Where a letter stands, for its template: "writing" until it is sealed (`opens_on` None), then "sealed" with
    the sentence shown in its place, and "open" from the day it opens."""
    if opens_on is None:
        return {"state": "writing"}
    if today < opens_on:
        return {"state": "sealed", "sentence": sealed_sentence(block, opens_on)}
    return {"state": "open"}


def recap_shown(document, own_frameworks, observed_frameworks, coach_name):
    """✨ Where the participant has got to, as a `recap` block shows it beside their letter: the top construct of each
    framework in their own result, as their results page draws it (`own_frameworks`, None before there is one); the
    top of each as the people who answered see them (`observed_frameworks`, the observer average's, None below the
    minimum), constructs level at the top named together; and their coach's name, if they chose one. `empty` when
    there is none of it, for the block's own message."""
    labels = {
        construct["id"]: text_for(construct.get("text_label", construct["label"]), "participant")
        for framework in document["measurement"]["frameworks"]
        for construct in framework["constructs"]
    }
    yours = [framework["bars"][0]["text_label"] for framework in own_frameworks or () if framework["bars"]]
    others = []
    for framework in observed_frameworks or ():
        top = max(construct["share"] for construct in framework["constructs"])
        others.append(joined([labels[c["construct"]] for c in framework["constructs"] if c["share"] == top]))
    return {"yours": yours, "others": others, "coach": coach_name, "empty": not (yours or others or coach_name)}


def ready_email(block):
    """✨ The wording of the email saying the letter is ready, in the participant's words: subject, body and the
    label of its link. It never carries the letter."""
    return {field: text_for(text, "participant") for field, text in block["email"].items()}
