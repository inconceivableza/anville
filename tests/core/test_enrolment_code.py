from access.enrolment import is_valid_enrolment_code


def test_the_configured_code_is_accepted():
    assert is_valid_enrolment_code("GRACE-2026", configured="GRACE-2026")


def test_a_different_code_is_refused():
    assert not is_valid_enrolment_code("WRONG", configured="GRACE-2026")


def test_case_and_surrounding_whitespace_are_ignored():
    assert is_valid_enrolment_code("  grace-2026 ", configured="GRACE-2026")


def test_every_code_is_refused_when_no_code_is_configured():
    assert not is_valid_enrolment_code("", configured="")
    assert not is_valid_enrolment_code("   ", configured="  ")
