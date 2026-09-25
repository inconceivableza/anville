"""✨ The sort answer contract: every item placed in a bucket this pathway has, with a whole value from 0 to 100.

The widget sends the answer as JSON text. The server holds it to the contract and never trusts the widget.
"""

import json

import pytest

from engine.document import AnswerRefused, answer_from_form, answerable_block, validate
from tests.documents import complete_sort, sort_pathway


def submit(answer):
    document = sort_pathway()
    submitted = answer if isinstance(answer, str) else json.dumps(answer)
    return answer_from_form(document, answerable_block(document, "strengths-sort"), submitted)


def test_the_sort_pathway_is_a_valid_document():
    assert validate(sort_pathway()) == []


def test_a_complete_sort_is_accepted_as_sent():
    assert submit(complete_sort()) == complete_sort()


@pytest.mark.parametrize("value", [0, 100])
def test_a_value_at_either_end_of_the_slider_is_accepted(value):
    assert submit(complete_sort(a5={"bucket": "strength", "value": value}))["a5"]["value"] == value


def _without_p1():
    sort = complete_sort()
    del sort["p1"]
    return sort


@pytest.mark.parametrize(
    "answer",
    [
        pytest.param(_without_p1(), id="an item left unsorted"),
        pytest.param(complete_sort(x9={"bucket": "strength", "value": 50}), id="an item the pathway does not have"),
        pytest.param(complete_sort(a5={"bucket": "middling", "value": 50}), id="a bucket the pathway does not have"),
        pytest.param(complete_sort(a5={"bucket": "strength", "value": 101}), id="a value above 100"),
        pytest.param(complete_sort(a5={"bucket": "strength", "value": -1}), id="a value below 0"),
        pytest.param(complete_sort(a5={"bucket": "strength", "value": 5.5}), id="a fractional value"),
        pytest.param(complete_sort(a5={"bucket": "strength", "value": "50"}), id="a value sent as text"),
        pytest.param(complete_sort(a5={"bucket": "strength"}), id="an item with no value"),
        pytest.param(complete_sort(a5={"value": 50}), id="an item with no bucket"),
        pytest.param(complete_sort(a5={"bucket": "strength", "value": 50, "note": "x"}), id="an unexpected field"),
        pytest.param({}, id="an empty sort"),
        pytest.param([], id="a list rather than a sort"),
        pytest.param("not json", id="text that is not JSON"),
    ],
)
def test_a_sort_that_breaks_the_contract_is_refused(answer):
    with pytest.raises(AnswerRefused):
        submit(answer)


def test_a_whole_value_written_as_a_decimal_is_refused_rather_than_stored_as_a_float():
    """✨ JSON Schema counts 50.0 as an integer. Stored, it would turn every raw score into a float."""
    with pytest.raises(AnswerRefused):
        submit('{"a5": {"bucket": "strength", "value": 50.0}, "p1": {"bucket": "not-me", "value": 10}}')


def test_the_refusal_says_what_to_do_without_echoing_what_was_sent():
    with pytest.raises(AnswerRefused) as refused:
        submit(complete_sort(a5={"bucket": "<script>", "value": 50}))

    assert "<script>" not in str(refused.value)
    assert str(refused.value) == "Place every item in a bucket and give each one a score from 0 to 100, then submit again."
