# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import pytest

from engine.document import text_for
from engine.document.text import speaking_of, worded_for


def test_a_single_string_is_the_same_for_every_role():
    assert text_for("Read these passages.", "participant") == "Read these passages."
    assert text_for("Read these passages.", "observer") == "Read these passages."


def test_each_role_sees_its_own_wording():
    text = {"participant": "Building something that will outlast you", "observer": "Building something that will outlast them"}

    assert text_for(text, "participant") == "Building something that will outlast you"
    assert text_for(text, "observer") == "Building something that will outlast them"


def test_an_observer_sees_the_participant_wording_when_theirs_is_blank():
    assert text_for({"participant": "Sensing trends", "observer": ""}, "observer") == "Sensing trends"
    assert text_for({"participant": "Sensing trends", "observer": "   "}, "observer") == "Sensing trends"
    assert text_for({"participant": "Sensing trends"}, "observer") == "Sensing trends"


def test_a_coach_sees_their_own_wording_then_the_observers_then_the_participants():
    """✨ A coach reads about the participant, as an observer does, so the observer's wording serves where the coach has
    none of their own (ticket 118)."""
    text = {"participant": "Your profile", "observer": "{name}'s profile, as you see it", "coach": "{name}'s profile"}

    assert text_for(text, "coach") == "{name}'s profile"
    assert text_for({**text, "coach": "  "}, "coach") == "{name}'s profile, as you see it"
    assert text_for({"participant": "Your profile", "observer": ""}, "coach") == "Your profile"
    assert text_for("Much the same", "coach") == "Much the same"


def test_an_observer_never_sees_the_coachs_wording():
    assert text_for({"participant": "Your profile", "coach": "{name}'s profile"}, "observer") == "Your profile"


def test_an_unknown_role_is_refused():
    with pytest.raises(ValueError):
        text_for("Anything", "mentor")


@pytest.mark.parametrize(
    "written, read",
    [
        ("How others see you", "How others see Sam"),
        ("You and your friends", "Sam and your friends"),
        ("How you’re seen", "How you’re seen"),  # ✨ never "How Sam’re seen": the linter asks for a sentence of its own
    ],
)
def test_wording_written_to_the_participant_speaks_of_them_by_name_in_place_of_you_but_not_of_a_contraction(
    written, read
):
    assert speaking_of(written, "Sam") == read


def test_a_coach_has_wording_of_their_own_only_where_a_field_gives_a_coachs_or_an_observers():
    assert not worded_for("How others see you", "coach")
    assert not worded_for({"participant": "How others see you"}, "coach")
    assert worded_for({"participant": "How you’re seen", "coach": "How {name} is seen"}, "coach")
    assert worded_for({"participant": "How you’re seen", "observer": "How {name} is seen"}, "coach")

