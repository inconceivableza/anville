# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

from typing import NamedTuple


class Problem(NamedTuple):
    """✨ Something wrong with a pathway document, located by a JSON Pointer into it."""

    path: str
    message: str
