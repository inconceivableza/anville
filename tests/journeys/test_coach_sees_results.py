"""✨ The coach sees the results and comparison (ticket 27): once the coach has accepted, and the participant has seen
their comparison, they may tick "Give my coach access to my results and this comparison", and the coach's link then shows their results
and the comparison, read-only, as the participant sees them.

The consent belongs to the coach's link, as the coach's answer does: revoking or reissuing it, or choosing another
coach, ends it. The comparison keeps its minimum for the coach too.
"""

import re

import pytest

from engine.models import Response
from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_answers import CALLING, answer, participant  # noqa: F401 (a fixture)
from tests.journeys.test_coach_checklist import choose, step, text, the_coach_checklist
from tests.journeys.test_coach_link import answer_as_coach, coach_link_action, issue_coach_link
from tests.journeys.test_comparison import THREE_OBSERVERS, with_contacts
from tests.journeys.test_consent import give_consent
from tests.journeys.test_invitations import observer  # noqa: F401 (a fixture, used by name as the coach)
from tests.journeys.test_observer_responses import an_observer
from tests.journeys.test_results import SORT, submit_sort

# ✨ The participant's Apostle standing, as the results and the comparison say it (ticket 38). The coach's page says it only
# when it shows those.
SHOWN = "Leading"

# ✨ A percent, which neither the results nor the comparison shows any more.
A_PERCENT = re.compile(r"\d+%")


def with_a_sort_and_a_coach():
    """✨ The sort's test pathway with Whatever You Do's coach checklist at the foot of onboarding."""
    document = sort_pathway()
    document["content"]["sections"][0]["blocks"].append(the_coach_checklist())
    return document


@pytest.fixture
def signed_in(client, participant, load_pathway):  # noqa: F811
    """✨ A participant who has chosen Sam as their coach and completed onboarding, so the sort is open."""
    load_pathway(with_a_sort_and_a_coach())
    client.force_login(participant)
    give_consent(client)
    assert choose(client).status_code == 200
    client.post("/sections/onboarding/complete/")
    return client


def with_a_result(client, participant, observers=THREE_OBSERVERS, visited=True):  # noqa: F811
    """✨ The participant's own sort (90/10) and the observers' (by default 80, 70 and 60, so means of 70 and 30), and
    unless not `visited`, their press of "Compare with how others see you →". Returns their response."""
    submit_sort(client, complete_sort())
    response = Response.objects.get(participant=participant)
    for sort in observers:
        an_observer(response, sort)
    if visited:
        assert client.post(f"/results/{SORT}/comparison/visit/").status_code == 303
    return response


def an_accepted_coach(client, coach):
    """✨ Issue the coach's link and have the coach accept; returns the link."""
    link = issue_coach_link(client)
    assert answer_as_coach(coach, link, "accept").status_code == 303
    return link


def share(client, happy=True):
    """✨ Tick (or untick) "Give my coach access to my results and this comparison" on the comparison."""
    return client.post(f"/results/{SORT}/comparison/coach/", {"share": "on"} if happy else {})


def what_the_coach_sees(coach, link):
    """✨ The words on the coach's page, which must open."""
    page = coach.get(link)
    assert page.status_code == 200
    return text(page)


# What the coach sees, and for how long


@pytest.mark.django_db
def test_with_consent_the_coachs_link_shows_the_results_and_comparison_and_withdrawing_hides_them_at_once(
    signed_in, participant, observer  # noqa: F811
):
    with_a_result(signed_in, participant)
    link = an_accepted_coach(signed_in, observer)
    assert SHOWN not in what_the_coach_sees(observer, link)

    assert share(signed_in).status_code == 303
    shared = what_the_coach_sees(observer, link)
    assert "participant: Leading" in shared  # ✨ the participant's own, named for them as "You" is for the participant
    assert "Others: Leading" in shared and "Others: Less used" in shared  # ✨ the observers' means
    assert not A_PERCENT.search(shared)

    assert share(signed_in, happy=False).status_code == 303
    assert SHOWN not in what_the_coach_sees(observer, link)


@pytest.mark.django_db
def test_below_the_minimum_the_coach_sees_how_many_have_answered_and_no_observers_numbers(
    signed_in, participant, observer  # noqa: F811
):
    """✨ Two observers, at 80 and 70, would give means of 75 and 25."""
    with_a_result(signed_in, participant, observers=THREE_OBSERVERS[:2])
    link = an_accepted_coach(signed_in, observer)
    assert share(signed_in).status_code == 303

    shared = what_the_coach_sees(observer, link)

    assert SHOWN in shared  # ✨ the participant's own result
    assert "2 of 3" in shared
    assert "Others:" not in shared
    assert not A_PERCENT.search(shared)


@pytest.mark.django_db
def test_nothing_else_of_the_participants_reaches_the_coach(signed_in, participant, observer):  # noqa: F811
    response = with_a_result(signed_in, participant)
    answer(signed_in, "statement", "A calling statement only I should read.", section=CALLING)
    with_contacts(response, "Priya Naidoo")
    link = an_accepted_coach(signed_in, observer)
    assert share(signed_in).status_code == 303

    shared = what_the_coach_sees(observer, link)

    for private in ("calling statement only I should read", "Priya", "priya@example.com"):
        assert private not in shared


# Refusals


@pytest.mark.django_db
@pytest.mark.parametrize("coach", ["no link", "waiting", "declined"])
def test_consent_is_refused_until_the_coach_has_accepted(signed_in, participant, observer, coach):  # noqa: F811
    with_a_result(signed_in, participant)
    link = None if coach == "no link" else issue_coach_link(signed_in)
    if coach == "declined":
        answer_as_coach(observer, link, "decline")

    refused = share(signed_in)

    assert refused.status_code == 403
    if coach == "waiting":
        answer_as_coach(observer, link, "accept")
    if link is not None:
        assert SHOWN not in what_the_coach_sees(observer, link)


@pytest.mark.django_db
def test_consent_is_refused_before_the_participant_has_visited_their_comparison(
    signed_in, participant, observer  # noqa: F811
):
    with_a_result(signed_in, participant, visited=False)
    link = an_accepted_coach(signed_in, observer)

    refused = share(signed_in)

    assert refused.status_code == 403
    assert SHOWN not in what_the_coach_sees(observer, link)


@pytest.mark.django_db
@pytest.mark.parametrize("change", ["revoked", "reissued", "another coach saved", "coach removed"])
def test_revoking_reissuing_or_changing_the_coach_ends_access_and_clears_the_consent(
    signed_in, participant, observer, change  # noqa: F811
):
    """✨ Whoever the coach is afterwards accepts a new link, and still sees nothing until the participant ticks again."""
    with_a_result(signed_in, participant)
    old = an_accepted_coach(signed_in, observer)
    assert share(signed_in).status_code == 303

    if change == "revoked":
        signed_in.post(coach_link_action(signed_in, "revoke"))
    elif change == "another coach saved":
        assert choose(signed_in, name="Alex", email="alex@example.com").status_code == 200
    elif change == "coach removed":
        assert step(signed_in, "remove").status_code == 200
        assert choose(signed_in).status_code == 200
    new = an_accepted_coach(signed_in, observer)  # ✨ issuing again is the reissue

    assert observer.get(old).status_code == 404
    assert SHOWN not in what_the_coach_sees(observer, new)
