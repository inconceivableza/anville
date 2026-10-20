# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A participant flat on both frameworks is told on their results that they are a generalist (ticket 30a, ADR 0018).
The tie detection runs on the participant's own sort alone, never an observer's."""

import pytest

from tests.documents import complete_sort, sort_pathway, with_a_tie_break
from engine.models import Response, Result
from tests.journeys.pages import text_of
from tests.journeys.test_answers import participant  # noqa: F401 (a fixture)
from tests.journeys.test_comparison import comparison, observer_sort, with_observers
from tests.journeys.test_consent import give_consent
from tests.journeys.test_contact_list import JO, PRIYA, save_contacts
from tests.journeys.test_hub import signed_in_client  # noqa: F401 (a fixture)
from tests.journeys.test_invitations import issue_link, observer  # noqa: F401 (observer is a fixture)
from tests.journeys.test_observer_assessment import observed_pathway, send
from tests.journeys.test_observer_landing import claim
from tests.journeys.test_observer_responses import an_observer
from tests.journeys.test_results import in_order, results, submit_sort

GENERALIST = "Two flat profiles"

# ✨ The test pathway's two items each load onto one construct of each framework, so a sort splitting them evenly is
# flat on both, every construct at an even share ("Present"), and one leaning on either is tied on neither.
EVEN = complete_sort(a5={"bucket": "strength", "value": 50}, p1={"bucket": "strength", "value": 50})


@pytest.fixture
def signed_in(client, participant, load_pathway):
    """✨ A participant with onboarding complete, on a pathway with a tie-break and the generalist's wording."""
    load_pathway(with_a_tie_break(sort_pathway(), percent=5, cluster=4))
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    return client


@pytest.mark.django_db
def test_a_participant_flat_on_both_frameworks_is_told_on_their_results_they_are_a_generalist(signed_in):
    submit_sort(signed_in, EVEN)

    assert GENERALIST in results(signed_in).content.decode()


@pytest.mark.django_db
def test_a_participant_with_a_clear_leader_is_not_told_they_are_a_generalist(signed_in):
    submit_sort(signed_in, complete_sort())

    assert GENERALIST not in results(signed_in).content.decode()


@pytest.mark.django_db
def test_observers_sorts_tied_on_both_frameworks_never_make_the_participant_a_generalist(signed_in, participant):
    with_observers(signed_in, participant, [observer_sort(50)] * 3)

    assert GENERALIST not in results(signed_in).content.decode()
    assert GENERALIST not in comparison(signed_in).content.decode()


# ✨ The tie-break's pairs (ticket 30b). The test pathway's two items load the same way on both frameworks, so a third,
# loading onto Prophet and Deliver, lets a sort tie one framework alone: Apostle 50 and Prophet 10 + 40 on APEST(d),
# Ponder 10 and Deliver 50 + 40 on PEP. Tied on Apostle and Prophet, two pairs follow, one each round.
TIE_BREAK = "/results/strengths-sort/tie-break/"
TIED_ON_ONE = complete_sort(
    a5={"bucket": "strength", "value": 50},
    p1={"bucket": "not-me", "value": 10},
    x1={"bucket": "strength", "value": 40},
)
CLEAR = complete_sort(x1={"bucket": "not-me", "value": 10})


def tie_breaking_pathway(document=None):
    document = document or sort_pathway()
    document["instrument"]["items"].append({"id": "x1", "text": "Seeing it through", "loads": ["prophet", "deliver"]})
    return with_a_tie_break(document)


@pytest.fixture
def marked(client, participant, load_pathway):
    """✨ A participant with onboarding complete, on a pathway whose sort can tie one framework alone."""
    load_pathway(tie_breaking_pathway())
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    return client


def choose(client, pair, chosen):
    """✨ Answer one pair as its form does: by its place in the plan and the construct chosen, or "" to skip."""
    return client.post(TIE_BREAK, {"pair": pair, "chosen": chosen})


def stored():
    result = Result.objects.get()
    return result.scores, result.tie_break_answers


@pytest.mark.django_db
def test_sending_a_sort_tied_on_one_framework_leads_to_its_pairs(marked):
    sent = submit_sort(marked, TIED_ON_ONE)

    assert sent["HX-Redirect"] == TIE_BREAK
    page = marked.get(TIE_BREAK).content.decode()
    assert "I am apostle, first" in page and "I am prophet, second" in page


@pytest.mark.django_db
def test_sending_a_sort_with_nothing_to_break_leads_to_the_results(marked):
    sent = submit_sort(marked, CLEAR)

    assert sent["HX-Redirect"] == "/results/strengths-sort/"
    assert marked.get(TIE_BREAK)["Location"] == "/results/strengths-sort/"


@pytest.mark.django_db
def test_answers_and_skips_are_stored_beside_the_sorts_result_which_is_unchanged(marked):
    submit_sort(marked, TIED_ON_ONE)
    scores_before, _ = stored()

    choose(marked, 0, "prophet")
    choose(marked, 1, "")

    scores, answers = stored()
    assert scores == scores_before
    assert [answer["chosen"] for answer in answers] == ["prophet", None]
    assert [answer["constructs"] for answer in answers] == [["apostle", "prophet"]] * 2


@pytest.mark.django_db
def test_a_choice_outside_the_pair_is_refused_and_nothing_is_stored(marked):
    submit_sort(marked, TIED_ON_ONE)

    refused = choose(marked, 0, "deliver")

    assert refused.status_code == 400
    assert stored()[1] == []


@pytest.mark.django_db
def test_leaving_part_way_comes_back_to_the_next_pair_and_the_last_leads_to_the_results(marked):
    submit_sort(marked, TIED_ON_ONE)
    choose(marked, 0, "apostle")

    assert results(marked)["Location"] == TIE_BREAK
    page = marked.get(TIE_BREAK).content.decode()
    assert "I am apostle, second" in page and "I am prophet, third" in page

    assert choose(marked, 1, "prophet")["Location"] == TIE_BREAK
    assert marked.get(TIE_BREAK)["Location"] == "/results/strengths-sort/"
    assert results(marked).status_code == 200


def tied_on_both_pathway():
    """✨ The test pathway with a third construct on each framework and an item loading onto both, Teacher and Assess."""
    document = sort_pathway()
    apest, pep = document["measurement"]["frameworks"]
    apest["constructs"].append({"id": "teacher", "label": "Teacher"})
    pep["constructs"].append({"id": "assess", "label": "Assess"})
    document["instrument"]["items"].append({"id": "t1", "text": "Explaining it clearly", "loads": ["teacher", "assess"]})
    return with_a_tie_break(document)


# ✨ Apostle and Prophet 45 each, Teacher 10; Ponder and Deliver 45 each, Assess 10. Tied at the top of both, and far
# from flat, as Teacher and Assess read "Less used".
TIED_ON_BOTH = complete_sort(
    a5={"bucket": "strength", "value": 45},
    p1={"bucket": "strength", "value": 45},
    t1={"bucket": "not-me", "value": 10},
)


@pytest.mark.django_db
def test_a_sort_tied_on_both_frameworks_but_not_flat_asks_pairs_on_each_in_turn_and_never_says_generalist(
    client, participant, load_pathway
):
    load_pathway(tied_on_both_pathway())
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")

    assert submit_sort(client, TIED_ON_BOTH)["HX-Redirect"] == TIE_BREAK
    asked = []
    for place in range(4):
        page = text_of(client.get(TIE_BREAK).content.decode())
        if "Your role among people" in page and "I am apostle" in page and "I am prophet" in page:
            asked.append("apest")
        elif "How you work" in page and "I am ponder" in page and "I am deliver" in page:
            asked.append("pep")
        choose(client, place, "")

    assert asked == ["apest", "pep", "apest", "pep"]
    assert client.get(TIE_BREAK)["Location"] == "/results/strengths-sort/"
    page = text_of(results(client).content.decode())
    assert GENERALIST not in page
    assert in_order(page, "Your gifting", "Every pair skipped", "Your energy", "Every pair skipped")


@pytest.fixture
def observed(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(tie_breaking_pathway(observed_pathway()))
    save_contacts(signed_in_client, JO, PRIYA)
    return signed_in_client


@pytest.mark.django_db
def test_an_observer_sending_a_tied_sort_is_never_offered_the_tie_break(observed, observer):  # noqa: F811
    claim(observer, issue_link(observed, "Jo"))

    sent = send(observer, TIED_ON_ONE)

    assert sent["Location"] == "/observe/"


# ✨ The re-weighted result (ticket 30c). TIED_ON_ONE gives Apostle and Prophet 50 each, so both stand at an even share
# ("Present") and Apostle leads by declaration order. Choosing Prophet in both rounds weighs Prophet 2 to Apostle's 1,
# so Prophet leads by just over 5% (fix-22): 51.22 to 48.78, both still "Present".
CHOSE_PROPHET = ["prophet", "prophet"]
# ✨ What 30c stored for those answers, sharing the 100 out by weight: whole numbers only, well above and well below an
# even share of 50.
AS_30C_STORED = {"prophet": 67, "apostle": 33}


def as_30c_stored(reweighted):
    """✨ A re-weighted result's frameworks as 30c stored them: AS_30C_STORED's whole numbers, no unrounded shares."""
    return [
        {
            "framework": framework["framework"],
            "constructs": [
                {
                    **{k: v for k, v in c.items() if k != "share"},
                    "percent": AS_30C_STORED.get(c["construct"], c["percent"]),
                }
                for c in framework["constructs"]
            ],
        }
        for framework in reweighted["frameworks"]
    ]


def answer_every_pair(client, choices):
    submit_sort(client, TIED_ON_ONE)
    for place, chosen in enumerate(choices):
        choose(client, place, chosen)


@pytest.mark.django_db
def test_the_re_weighted_result_is_stored_beside_the_sorts_once_every_pair_is_answered(marked):
    submit_sort(marked, TIED_ON_ONE)
    sent, _ = stored()
    choose(marked, 0, "prophet")
    assert Result.objects.get().reweighted is None

    choose(marked, 1, "prophet")

    result = Result.objects.get()
    assert result.scores == sent
    assert [construct["construct"] for construct in result.reweighted["frameworks"][0]["constructs"]] == [
        "prophet",
        "apostle",
    ]


@pytest.mark.django_db
def test_the_results_page_shows_the_re_weighted_result_and_how_the_tie_break_changed_it(marked):
    answer_every_pair(marked, CHOSE_PROPHET)

    page = text_of(results(marked).content.decode())

    assert in_order(page, "Your gifting", "The top changed", "Prophet", "Present", "Apostle", "Present", "Your energy")


@pytest.mark.django_db
def test_the_results_page_says_a_framework_is_balanced_when_the_choices_name_no_winner(marked):
    answer_every_pair(marked, ["apostle", "prophet"])

    page = text_of(results(marked).content.decode())

    assert in_order(page, "Your gifting", "Genuinely balanced", "Apostle", "Present", "Prophet", "Present")
    assert "The top changed" not in page


@pytest.mark.django_db
def test_the_results_page_says_every_pair_was_skipped_in_words_of_its_own(marked):
    answer_every_pair(marked, ["", ""])

    page = text_of(results(marked).content.decode())

    assert in_order(page, "Your gifting", "Every pair skipped", "As your sort left them.", "Apostle", "Prophet")
    assert "Genuinely balanced" not in page and GENERALIST not in page


@pytest.mark.django_db
def test_a_construct_named_in_the_tie_break_sentence_is_escaped(client, participant, load_pathway):
    """✨ fix-26: the sentence names the constructs by their labels, escaped as every label is."""
    document = tie_breaking_pathway()
    [prophet] = [c for c in document["measurement"]["frameworks"][0]["constructs"] if c["id"] == "prophet"]
    prophet["label"] = "<b>Prophet</b>"
    document["presentation"]["tie_break"]["separated"]["changed"] = "{top} now sits on top, in place of {previous}."
    load_pathway(document)
    client.force_login(participant)
    give_consent(client)
    client.post("/sections/onboarding/complete/")
    answer_every_pair(client, CHOSE_PROPHET)

    page = results(client).content.decode()

    assert "&lt;b&gt;Prophet&lt;/b&gt; now sits on top, in place of Apostle." in page
    assert "<b>Prophet</b>" not in page


@pytest.mark.django_db
def test_the_re_weighted_result_keeps_each_unrounded_share_beside_its_whole_number(marked):
    """✨ Prophet weighs 2 to Apostle's 1, so leads by 5.01% of their 100: 1050100/20501, stored as 51."""
    answer_every_pair(marked, CHOSE_PROPHET)

    apest = Result.objects.get().reweighted["frameworks"][0]["constructs"]

    assert [(c["construct"], c["percent"], c["share"]) for c in apest] == [
        ("prophet", 51, "1050100/20501"),
        ("apostle", 49, "1000000/20501"),
    ]


@pytest.mark.django_db
def test_a_result_re_weighted_before_its_shares_were_kept_still_renders_with_its_outcome(marked):
    """✨ As 30c stored it: one framework named on its own, whole numbers only."""
    answer_every_pair(marked, CHOSE_PROPHET)
    result = Result.objects.get()
    result.reweighted = {
        "method": "pairwise_reweighting",
        "frameworks": as_30c_stored(result.reweighted),
        "tie_break": {"framework": "apest", "outcome": "top_changed"},
    }
    result.save()

    page = text_of(results(marked).content.decode())

    assert in_order(page, "Your gifting", "The top changed", "Prophet", "Leading", "Apostle", "Less used", "Your energy")


@pytest.mark.django_db
def test_a_result_re_weighted_before_its_shares_were_kept_still_shows_its_gaps_on_the_comparison(marked, participant):
    """✨ Kept as whole numbers only, Prophet's 67 and Apostle's 33 are read as its shares: 17 from the observers' 50
    each."""
    answer_every_pair(marked, CHOSE_PROPHET)
    result = Result.objects.get()
    result.reweighted = {**result.reweighted, "frameworks": as_30c_stored(result.reweighted)}
    result.save()
    response = Response.objects.get(participant=participant)
    for _ in range(3):
        an_observer(response, TIED_ON_ONE)

    page = text_of(comparison(marked).content.decode())

    assert in_order(page, "Prophet (APEST(d))", "You rate higher (+17)")
    assert in_order(page, "Apostle (APEST(d))", "Others rate higher (+17)")


@pytest.mark.django_db
def test_the_comparison_sets_the_re_weighted_result_beside_the_observers_sorts_as_sent(marked, participant):
    """✨ The observers sent TIED_ON_ONE too, so their mean is 50 each, never re-weighted: the participant's 51.22 and
    48.78 are a point either side of it."""
    answer_every_pair(marked, CHOSE_PROPHET)
    response = Response.objects.get(participant=participant)
    for _ in range(3):
        an_observer(response, TIED_ON_ONE)

    page = text_of(comparison(marked).content.decode())

    assert in_order(page, "Prophet", "You: Present", "Others: Present", "Apostle", "You: Present", "Others: Present")
    assert in_order(page, "Prophet (APEST(d))", "You rate higher (+1)")
    assert in_order(page, "Apostle (APEST(d))", "Others rate higher (+1)")
