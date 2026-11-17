# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The coach sees the results and comparison (ticket 27): once the coach has accepted, and the participant has seen
their comparison, they may tick "Give my coach access to my results and this comparison", and the coach's link then shows their results
and the comparison, read-only, as the participant sees them.

The consent belongs to the coach's link, as the coach's answer does: revoking or reissuing it, or choosing another
coach, ends it. The comparison keeps its minimum for the coach too.
"""

import re

import pytest

from access.models import name_shown_for
from engine.models import Invitation, Response
from tests.documents import complete_sort, sort_pathway
from tests.journeys.test_answers import CALLING, answer, participant  # noqa: F401 (a fixture)
from tests.journeys.test_coach_checklist import choose, step, text, the_coach_checklist
from tests.journeys.test_coach_link import answer_as_coach, coach_link_action, issue_coach_link
from tests.journeys.test_comparison import THREE_OBSERVERS, with_contacts
from tests.journeys.test_consent import give_consent, withdraw_consent
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


def signed_in_over(document, client, participant, load_pathway):  # noqa: F811
    """✨ A participant of the pathway `document` who has chosen Sam as their coach and completed onboarding, so the sort
    is open."""
    load_pathway(document)
    client.force_login(participant)
    give_consent(client)
    assert choose(client).status_code == 200
    client.post("/sections/onboarding/complete/")
    return client


@pytest.fixture
def signed_in(client, participant, load_pathway):  # noqa: F811
    """✨ A participant who has chosen Sam as their coach and completed onboarding, so the sort is open."""
    return signed_in_over(with_a_sort_and_a_coach(), client, participant, load_pathway)


def with_a_result(client, participant, observers=THREE_OBSERVERS, visited=True):  # noqa: F811
    """✨ The participant's own sort (90/10) and the observers' (by default 80, 70 and 60, so means of 70 and 30), and
    unless not `visited`, their press of "Compare with how others see you →", confirmed as it asks with the minimum in
    (ticket 55). Returns their response."""
    submit_sort(client, complete_sort())
    response = Response.objects.get(participant=participant)
    for sort in observers:
        an_observer(response, sort)
    if visited:
        assert client.post(f"/results/{SORT}/comparison/visit/", {"confirmed": "yes"}).status_code == 303
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
def test_the_coach_sees_the_observers_numbers_only_once_the_participant_has_looked(
    signed_in, participant, observer  # noqa: F811
):
    """✨ Shared after a press below the minimum, which visits and freezes nothing: a third answer then brings the
    minimum in while collection is open, and the coach sees no more than the participant, nothing of the observers'
    until the participant's press freezes it (ADR 0017; sprint-3d-r1-fix-1)."""
    response = with_a_result(signed_in, participant, observers=THREE_OBSERVERS[:2])
    link = an_accepted_coach(signed_in, observer)
    assert share(signed_in).status_code == 303
    an_observer(response, THREE_OBSERVERS[2])

    before = what_the_coach_sees(observer, link)
    assert signed_in.post(f"/results/{SORT}/comparison/visit/", {"confirmed": "yes"}).status_code == 303
    after = what_the_coach_sees(observer, link)

    assert SHOWN in before  # ✨ the participant's own result
    assert "Others:" not in before
    assert "Others: Leading" in after


# ✨ What a pathway's comparison signpost may be titled: neither of the engine's own wordings, so that the test reads the
# title from the document it gave.
OWN_TITLE = "What others notice about you"


def the_headings(page):
    """✨ The words of each `<h1>` on a page, in order."""
    return [text(heading).strip() for heading in re.findall(r"<h1[^>]*>(.*?)</h1>", page.content.decode(), re.S)]


@pytest.mark.django_db
@pytest.mark.parametrize("titled", [True, False], ids=["a signpost titles it", "no signpost"])
def test_the_coach_sees_the_comparison_headed_as_the_participant_does_with_their_name_in_place_of_you(
    client, participant, observer, load_pathway, titled  # noqa: F811
):
    """✨ From the document, never from which pathway it is (sprint-3d-r1-fix-2): the signpost's title where there is
    one, as the participant's own page is headed, otherwise the engine's own."""
    document = with_a_sort_and_a_coach()
    if titled:
        document["content"]["sections"][1]["blocks"].append(
            {"id": "others", "type": "comparison_signpost", "sort": SORT, "title": OWN_TITLE}
        )
    signed_in = signed_in_over(document, client, participant, load_pathway)
    with_a_result(signed_in, participant)
    link = an_accepted_coach(signed_in, observer)
    assert share(signed_in).status_code == 303
    named = name_shown_for(participant)

    own = the_headings(signed_in.get(f"/results/{SORT}/comparison/"))[-1]
    coach_headings = the_headings(observer.get(link))

    assert (own == OWN_TITLE) is titled
    assert "you" in own
    assert coach_headings[-1] == own.replace("you", named)
    assert f"{named}'s results" in coach_headings


def worded_for_a_coach():
    """✨ The sort's test pathway with a coach, worded for the coach about the participant by name where the document
    says so, and where it does not, through the observer's wording, as an item's text is (ticket 118)."""
    document = with_a_sort_and_a_coach()
    presentation = document["presentation"]
    presentation["frameworks"][0]["heading"] = {"participant": "Your gifting", "coach": "{name}'s gifting"}
    gaps = presentation["comparison"]["gaps"]
    gaps["you_higher"]["label"] = {"participant": "You rate higher", "coach": "{name} rates higher"}
    presentation["comparison"]["prompts"] = [
        {
            "title": "The surprise",
            "text": {"participant": "Which gap surprised you most?", "coach": "Which surprised {name}?"},
        }
    ]
    document["instrument"]["items"][0]["text"] = {
        "participant": "Starting things where you are",
        "observer": "Starting things where they are",
    }
    return document


@pytest.mark.django_db
def test_the_coachs_link_speaks_of_the_participant_by_name_and_their_own_pages_still_speak_to_them(
    client, participant, observer, load_pathway  # noqa: F811
):
    """✨ The coach is not the participant, so their link names them, as an observer's pages do (ticket 118); the
    participant's own results and comparison are as they were."""
    signed_in = signed_in_over(worded_for_a_coach(), client, participant, load_pathway)
    with_a_result(signed_in, participant)
    link = an_accepted_coach(signed_in, observer)
    assert share(signed_in).status_code == 303
    named = name_shown_for(participant)

    shared = what_the_coach_sees(observer, link)
    own = text(signed_in.get(f"/results/{SORT}/")) + text(signed_in.get(f"/results/{SORT}/comparison/"))

    for theirs, yours in [
        (f"{named}'s gifting", "Your gifting"),
        (f"{named} rates higher", "You rate higher"),
        (f"Which surprised {named}?", "Which gap surprised you most?"),
        ("Starting things where they are", "Starting things where you are"),
    ]:
        assert theirs in shared and yours not in shared
        assert yours in own and theirs not in own
    assert "{name}" not in shared
    assert f"{named} is happy for you to see this: the results and comparison {named} sees." in shared


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
def test_without_javascript_a_refused_tick_comes_back_on_the_comparison_saying_why(
    signed_in, participant, observer  # noqa: F811
):
    """✨ Never the bare status line (spec, Engine; fix-2)."""
    with_a_result(signed_in, participant, visited=False)
    link = an_accepted_coach(signed_in, observer)

    refused = share(signed_in)

    page = refused.content.decode()
    assert refused.status_code == 403
    assert not Invitation.objects.filter(results_shared_at__isnull=False).exists()
    assert SHOWN not in what_the_coach_sees(observer, link)
    assert refused.templates[0].name == "engine/comparison.html"
    assert '<body class="framed">' in page
    assert "Your coach can see this only once they have accepted and you have seen your comparison." in text(refused)


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
        assert choose(signed_in, name="Alex").status_code == 200
    elif change == "coach removed":
        assert step(signed_in, "remove").status_code == 200
        assert choose(signed_in).status_code == 200
    new = an_accepted_coach(signed_in, observer)  # ✨ issuing again is the reissue

    assert observer.get(old).status_code == 404
    assert SHOWN not in what_the_coach_sees(observer, new)


# While the participant's consent is withdrawn (ticket 45)


@pytest.mark.django_db
def test_while_the_participant_has_withdrawn_the_coach_sees_nothing_of_what_was_shared(
    signed_in, participant, observer  # noqa: F811
):
    with_a_result(signed_in, participant)
    link = an_accepted_coach(signed_in, observer)
    assert share(signed_in).status_code == 303

    withdraw_consent(signed_in)

    refused = observer.get(link)
    assert refused.status_code == 404
    assert SHOWN not in refused.content.decode()
    assert "Sam" not in refused.content.decode()


@pytest.mark.django_db
def test_consenting_again_shows_the_coach_what_was_shared_before(signed_in, participant, observer):  # noqa: F811
    """✨ The participant gave the sharing separately, and can untick it: a withdrawal and a return leave it standing."""
    with_a_result(signed_in, participant)
    link = an_accepted_coach(signed_in, observer)
    assert share(signed_in).status_code == 303
    withdraw_consent(signed_in)

    give_consent(signed_in)

    assert SHOWN in what_the_coach_sees(observer, link)
