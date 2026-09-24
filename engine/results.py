"""✨ The results page as the engine derives it: a stored result, dressed in its pathway version's wording.

Nothing here touches the database or a request. The numbers come from the stored result and are never
recomputed; the words and tones come from the same pathway version the result was scored against.
"""

from engine.document.text import text_for

# ✨ The stylesheet defines --rank-1 to --rank-6; every rank below the sixth takes the sixth colour.
RANK_COLOURS = 6


def bar_ranks(percents):
    """✨ Each score's rank among the distinct scores, strongest first, so tied scores share a colour."""
    distinct = sorted(set(percents), reverse=True)
    return [min(distinct.index(percent) + 1, RANK_COLOURS) for percent in percents]


def results_page(document, scores, sort, name, role="participant"):
    """✨ Everything the results page shows, from a stored result and the sort it was scored from.

    `{name}` in the authored title is replaced as plain text, never through `format()`, so an author's
    braces can reach nothing. The template escapes whatever comes out.
    """
    presentation = document.get("presentation", {})
    shown = {entry["construct"]: entry for entry in presentation.get("constructs", [])}
    framed = {entry["framework"]: entry for entry in presentation.get("frameworks", [])}
    frameworks = {framework["id"]: framework for framework in document["measurement"]["frameworks"]}
    title = presentation.get("results_title", document["title"])
    return {
        "title": text_for(title, role).replace("{name}", name),
        "frameworks": [
            _framework(
                frameworks[scored["framework"]],
                framed.get(scored["framework"], {}),
                scored["constructs"],
                shown,
                document["instrument"]["items"],
                sort,
                role,
            )
            for scored in scores["frameworks"]
        ],
        "disclaimer": _text(presentation, "disclaimer", role),
    }


def _framework(framework, presented, ranked, shown, items, sort, role):
    labels = {construct["id"]: text_for(construct["label"], role) for construct in framework["constructs"]}
    by_rank = presented.get("bars") == "rank"
    ranks = bar_ranks([construct["percent"] for construct in ranked])
    return {
        "heading": _text(presented, "heading", role) or text_for(framework["label"], role),
        "subtitle": _text(presented, "subtitle", role),
        "bars": [
            {
                "label": labels[construct["construct"]],
                "percent": construct["percent"],
                "persona": _text(shown.get(construct["construct"], {}), "persona", role),
                "description": _text(shown.get(construct["construct"], {}), "description", role),
                "colour": f"rank-{rank}" if by_rank else _tone(shown.get(construct["construct"], {})),
            }
            for construct, rank in zip(ranked, ranks)
        ],
        # ✨ The item scores, grouped by construct in the order they were declared, as the prototype listed them.
        "groups": [
            {
                "label": labels[construct["id"]],
                "colour": _tone(shown.get(construct["id"], {})),
                "items": [
                    {"text": text_for(item["text"], role), "value": sort[item["id"]]["value"]}
                    for item in items
                    if construct["id"] in item["loads"]
                ],
            }
            for construct in framework["constructs"]
        ],
    }


def _text(entry, field, role):
    return text_for(entry[field], role) if field in entry else ""


def _tone(entry):
    return f"tone-{entry['tone']}" if "tone" in entry else ""
