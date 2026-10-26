# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from django.conf import settings

from organisations.joining import holds_a_working_join_link


def is_valid_enrolment_code(submitted, *, configured):
    expected = _normalised(configured)
    return bool(expected) and _normalised(submitted) == expected


def asks_for_the_code(request):
    """✨ Whether sign-up asks for the enrolment code: not when turned off from the environment, or while the visitor
    holds a group's join link, which admits them in its place (organisations-and-groups spec)."""
    return settings.ANVILLE_ENROLMENT_REQUIRED and not (
        request is not None and holds_a_working_join_link(request.session)
    )


def _normalised(code):
    return code.strip().casefold()
