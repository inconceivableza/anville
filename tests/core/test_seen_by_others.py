"""✨ Whether others see a construct higher, lower or much the same as the participant, in words, by the document's
significant gap (ticket 38).
"""

import pytest

from engine.document.comparison import seen_by_others
from tests.documents import sort_pathway


@pytest.mark.parametrize(
    "you, others, words",
    [
        (20, 25, "Seen as more"),
        (20, 24, "About the same"),
        (20, 20, "About the same"),
        (25, 21, "About the same"),
        (25, 20, "Seen as less"),
    ],
    ids=["others 5 higher", "others 4 higher", "no gap", "others 4 lower", "others 5 lower"],
)
def test_others_see_a_construct_higher_lower_or_much_the_same_from_the_significant_gap(you, others, words):
    document = sort_pathway()
    document["presentation"]["comparison"]["seen_by_others"] = {
        "others_higher": "Seen as more",
        "you_higher": "Seen as less",
        "much_the_same": "About the same",
    }

    assert seen_by_others(document, you, others) == words
