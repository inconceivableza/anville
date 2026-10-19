# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ What others see in a participant: their observers' sorts, each scored on its own, then averaged (ADR 0005).

Only observers' sorts are passed in. The participant's own sort is never one of them, so reading the right sorts is
the caller's job. Nothing here touches the database or a request.
"""

from engine.document.observers import minimum_observers
from engine.document.scoring import score, unrounded_shares


def aggregate(document, answers):
    """✨ The count of observers and, from the minimum up, each construct's mean share and every observer's share.

    `answers` holds one sort answer per observer. Below the minimum there are no numbers at all, not even a partial
    distribution. Each answer is scored by the document's frozen method on its own, so every observer counts equally
    however high they set their sliders. Both are unrounded and exact (ADR 0018): the mean of the observers' shares
    (`share`) and each observer's share (`per_observer_shares`), given in ascending order and never in the order they
    answered, so no value can be paired with a person. The comparison draws, words, and works its gaps and agreement
    band out from them; nothing shows a rounded value of a single observer's, so none is kept. Constructs keep the
    order they were declared in, so they line up with the participant's.
    """
    if len(answers) < minimum_observers(document):
        return {"observers": len(answers), "frameworks": None}
    exact = [unrounded_shares(score(document, answer)) for answer in answers]
    return {
        "observers": len(answers),
        "frameworks": [
            {
                "framework": framework["id"],
                "constructs": [
                    {
                        "construct": construct["id"],
                        "share": sum(each[framework["id"]][construct["id"]] for each in exact) / len(exact),
                        "per_observer_shares": sorted(each[framework["id"]][construct["id"]] for each in exact),
                    }
                    for construct in framework["constructs"]
                ],
            }
            for framework in document["measurement"]["frameworks"]
        ],
    }
