"""✨ What others see in a participant: their observers' sorts, each scored on its own, then averaged (ADR 0005).

Only observers' sorts are passed in. The participant's own sort is never one of them, so reading the right sorts is
the caller's job. Nothing here touches the database or a request.
"""

from statistics import fmean

from engine.document.observers import minimum_observers
from engine.document.scoring import round_half_up, score, shares


def aggregate(document, answers):
    """✨ The count of observers and, from the minimum up, each construct's mean percent and every observer's percent.

    `answers` holds one sort answer per observer. Below the minimum there are no numbers at all, not even a partial
    distribution. Each answer is scored by the document's frozen method on its own, so every observer counts equally
    however high they set their sliders. The mean averages each observer's unrounded share and rounds once. Each
    observer's percent is the one their own result would show, given in ascending order and never in the order they
    answered, so no value can be paired with a person. Constructs keep the order they were declared in, so they line
    up with the participant's.
    """
    if len(answers) < minimum_observers(document):
        return {"observers": len(answers), "frameworks": None}
    percents = [_percents(score(document, answer)) for answer in answers]
    unrounded = [shares(document, answer) for answer in answers]
    return {
        "observers": len(answers),
        "frameworks": [
            {
                "framework": framework["id"],
                "constructs": [
                    {
                        "construct": construct["id"],
                        "percent": round_half_up(fmean(each[framework["id"]][construct["id"]] for each in unrounded)),
                        "per_observer": sorted(each[framework["id"]][construct["id"]] for each in percents),
                    }
                    for construct in framework["constructs"]
                ],
            }
            for framework in document["measurement"]["frameworks"]
        ],
    }


def _percents(result):
    """✨ A result's rounded percents as `{framework: {construct: percent}}`, so they are found by id, not position."""
    return {
        framework["framework"]: {construct["construct"]: construct["percent"] for construct in framework["constructs"]}
        for framework in result["frameworks"]
    }
