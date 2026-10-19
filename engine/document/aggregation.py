# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ What others see in a participant: their observers' sorts, each scored on its own, then averaged (ADR 0005).

Only observers' sorts are passed in. The participant's own sort is never one of them, so reading the right sorts is
the caller's job. Nothing here touches the database or a request.
"""

from statistics import fmean

from engine.document.observers import minimum_observers
from engine.document.scoring import percents_by_construct, round_half_up, score, shares, unrounded_shares


def aggregate(document, answers):
    """✨ The count of observers and, from the minimum up, each construct's mean percent and every observer's percent.

    `answers` holds one sort answer per observer. Below the minimum there are no numbers at all, not even a partial
    distribution. Each answer is scored by the document's frozen method on its own, so every observer counts equally
    however high they set their sliders. The mean averages each observer's unrounded share and rounds once. Each
    observer's percent is the one their own result would show, given in ascending order and never in the order they
    answered, so no value can be paired with a person. Beside them, the mean and each observer's share unrounded and
    exact (`share`, `per_observer_shares`, ascending too), which the comparison draws and words (ADR 0018). Constructs keep the order they were declared in, so they line
    up with the participant's.
    """
    if len(answers) < minimum_observers(document):
        return {"observers": len(answers), "frameworks": None}
    scored = [score(document, answer) for answer in answers]
    percents = [percents_by_construct(each) for each in scored]
    unrounded = [shares(document, answer) for answer in answers]
    exact = [unrounded_shares(each) for each in scored]
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
                        # ✨ The same, unrounded and exact, for the comparison to draw and word (ADR 0018).
                        "share": sum(each[framework["id"]][construct["id"]] for each in exact) / len(exact),
                        "per_observer_shares": sorted(each[framework["id"]][construct["id"]] for each in exact),
                    }
                    for construct in framework["constructs"]
                ],
            }
            for framework in document["measurement"]["frameworks"]
        ],
    }
