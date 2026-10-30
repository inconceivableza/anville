# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A letter's dates are whole months on from the day it is sealed, kept within the month they land in (ticket 104)."""

from datetime import date

import pytest

from engine.document.letter import months_after


@pytest.mark.parametrize(
    "day, months, expected",
    [
        (date(2030, 3, 4), 12, date(2031, 3, 4)),
        (date(2030, 11, 30), 3, date(2031, 2, 28)),
        (date(2031, 1, 31), 1, date(2031, 2, 28)),
        (date(2032, 2, 29), 12, date(2033, 2, 28)),
    ],
    ids=["same day", "into the next year", "past the end of February", "29 February"],
)
def test_months_on_keeps_the_day_or_else_ends_the_month(day, months, expected):
    assert months_after(day, months) == expected
