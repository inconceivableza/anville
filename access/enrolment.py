def is_valid_enrolment_code(submitted, *, configured):
    expected = _normalised(configured)
    return bool(expected) and _normalised(submitted) == expected


def _normalised(code):
    return code.strip().casefold()
