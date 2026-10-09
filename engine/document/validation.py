# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from engine.document.lint import lint
from engine.document.problem import Problem

SCHEMA = json.loads((Path(__file__).parent / "pathway.schema.json").read_text())

_validator = Draft202012Validator(SCHEMA)


def validate(document):
    return _schema_problems(document) or sorted(lint(document))


def _schema_problems(document):
    problems = [
        Problem(_pointer(error.absolute_path), error.message)
        for error in _validator.iter_errors(document)
    ]
    return sorted(problems)


def _pointer(parts):
    return "".join(f"/{part}" for part in parts)
