# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ Whether others see a construct higher, lower or much the same as the participant, in words: much the same only
when both shares have the same standing and the gap is under the document's significant gap (ticket 38, fix-11).
"""

import pytest

from engine.document.comparison import seen_by_others
from tests.documents import sort_pathway


@pytest.mark.parametrize(
    "you, others, words",
    [
        # ✨ Six constructs, so an even share is 16.67: Leading from 20.83, Strong from 17.5, Present from 14.17, Less
        # used below. All but the last two are Leading on both sides.
        (22, 27, "Seen as more"),
        (22, 26, "About the same"),
        (22, 22, "About the same"),
        (26, 22, "About the same"),
        (27, 22, "Seen as less"),
        # ✨ Facilitate as found on the comparison: Strong beside Less used, a gap of 3.6.
        (17.6, 14.0, "Seen as less"),
        (14.0, 17.6, "Seen as more"),
    ],
    ids=[
        "others 5 higher",
        "others 4 higher, same standing",
        "no gap",
        "others 4 lower, same standing",
        "others 5 lower",
        "others under 5 lower, a different standing",
        "others under 5 higher, a different standing",
    ],
)
def test_others_see_a_construct_higher_lower_or_much_the_same_from_its_standing_and_the_significant_gap(
    you, others, words
):
    document = sort_pathway()
    document["presentation"]["comparison"]["seen_by_others"] = {
        "others_higher": "Seen as more",
        "you_higher": "Seen as less",
        "much_the_same": "About the same",
    }

    assert seen_by_others(document, you, others, construct_count=6) == words
