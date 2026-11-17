# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import pytest

from engine.document import text_for


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
