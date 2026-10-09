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


def test_an_unknown_role_is_refused():
    with pytest.raises(ValueError):
        text_for("Anything", "coach")
