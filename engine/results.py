"""✨ The results page and the comparison as the engine derives them: a stored result, dressed in its pathway
version's wording, and on the comparison set beside the observer average.

Nothing here touches the database or a request. The numbers come from the stored result and are never
recomputed; the words and tones come from the same pathway version the result was scored against.
"""

from engine.document.comparison import agreement, comparison_settings, largest_gaps
from engine.document.observers import minimum_observers
from engine.document.scoring import percents_by_construct
from engine.document.text import text_for

# ✨ The stylesheet defines --rank-1 to --rank-6; every rank below the sixth takes the sixth colour.
RANK_COLOURS = 6

# ✨ The stylesheet's class for each direction of a gap, so a document's key never becomes a class name.
GAP_CLASSES = {"others_higher": "gap-others-higher", "you_higher": "gap-you-higher"}


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
    construct_presentation = {entry["construct"]: entry for entry in presentation.get("constructs", [])}
    framework_presentation = {entry["framework"]: entry for entry in presentation.get("frameworks", [])}
    frameworks = {framework["id"]: framework for framework in document["measurement"]["frameworks"]}
    title = presentation.get("results_title", document["title"])
    return {
        "title": text_for(title, role).replace("{name}", name),
        "frameworks": [
            _framework(
                frameworks[scored["framework"]],
                framework_presentation.get(scored["framework"], {}),
                scored["constructs"],
                construct_presentation,
                document["instrument"]["items"],
                sort,
                role,
            )
            for scored in scores["frameworks"]
        ],
        "disclaimer": _text(presentation, "disclaimer", role),
    }


def comparison_page(document, scores, sort, observer_average):
    """✨ Everything the comparison shows: the participant's self-result beside the observer average (ADR 0005).

    The participant's bars are the results page's, in its wording and colours. Below the minimum the observer average
    holds a count and no numbers, and so does what comes out: not even the self-result's, nor any gap or band. Each
    construct's mean is read from the observer average, and its single observers' percents only for the agreement
    band, never shown. The self-result is ranked and the observer average keeps the declared order, so the two are
    paired by construct id. The largest gaps and the reflection prompts follow the bars.
    """
    shown = {"observers": observer_average["observers"], "minimum": minimum_observers(document), "frameworks": None}
    if observer_average["frameworks"] is None:
        return shown
    observed = {
        framework["framework"]: {construct["construct"]: construct for construct in framework["constructs"]}
        for framework in observer_average["frameworks"]
    }
    page = results_page(document, scores, sort, name="")
    presented = document.get("presentation", {}).get("frameworks", [])
    by_rank = {entry["framework"] for entry in presented if entry.get("bars") == "rank"}
    for framework, scored in zip(page["frameworks"], scores["frameworks"]):
        for bar, construct in zip(framework["bars"], scored["constructs"]):
            others = observed[scored["framework"]][construct["construct"]]
            bar["others"] = others["percent"]
            bar["agreement"] = text_for(agreement(document, others["per_observer"]), "participant")
            # ✨ As the prototype's comparison drew them: "You" in rank colours where the results page uses them, and
            # otherwise all in one colour, never a construct's tone, which is the distribution strip's.
            if scored["framework"] not in by_rank:
                bar["colour"] = "comparison-you"
    return {**shown, "frameworks": page["frameworks"], **_reflection(document, scores, observed)}


def _reflection(document, scores, observed):
    """✨ Below the bars: the largest gaps, worded, and the questions to reflect on, all from the document.

    Only the participant sees the comparison, so it is worded for them. A document with no gaps wording lists no gaps,
    since there would be nothing to say about them; the schema asks for all of it or none.
    """
    role = "participant"
    wording = comparison_settings(document)
    prompts = [
        {"title": text_for(prompt["title"], role), "text": text_for(prompt["text"], role)}
        for prompt in wording.get("prompts", [])
    ]
    shown = {
        "gaps": [],
        "prompts_heading": _text(wording, "prompts_heading", role),
        "prompts_intro": _text(wording, "prompts_intro", role),
        "prompts": prompts,
    }
    if "gaps" not in wording:
        return shown
    gap_wording = wording["gaps"]
    yours = percents_by_construct(scores)
    # ✨ Paired in the order the constructs were declared, so tied gaps keep it.
    pairs = [
        {"framework": framework, "construct": construct, "you": yours[framework][construct], "others": others["percent"]}
        for framework, constructs in observed.items()
        for construct, others in constructs.items()
    ]
    frameworks = {framework["id"]: framework for framework in document["measurement"]["frameworks"]}
    labels = {
        (framework["id"], construct["id"]): text_for(construct["label"], role)
        for framework in frameworks.values()
        for construct in framework["constructs"]
    }
    for gap in largest_gaps(document, pairs):
        # ✨ No gap at all has no direction, so no badge, and reads as a modest gap (the prototype said "You rate
        # higher (+0)").
        direction = gap_wording[gap["direction"]] if gap["direction"] else None
        shown["gaps"].append(
            {
                "label": labels[(gap["framework"], gap["construct"])],
                "framework": text_for(frameworks[gap["framework"]]["label"], role),
                "gap": gap["gap"],
                "badge": text_for(direction["label"], role) if direction else "",
                "badge_class": GAP_CLASSES.get(gap["direction"], ""),
                "description": text_for(
                    direction["description"] if direction and gap["significant"] else gap_wording["modest"], role
                ),
            }
        )
    return {
        **shown,
        "gaps_heading": _text(gap_wording, "heading", role),
        "gaps_intro": _text(gap_wording, "intro", role),
    }


def _framework(framework, presentation, ranked_constructs, construct_presentation, items, sort, role):
    labels = {construct["id"]: text_for(construct["label"], role) for construct in framework["constructs"]}
    by_rank = presentation.get("bars") == "rank"
    ranks = bar_ranks([construct["percent"] for construct in ranked_constructs])
    bars = []
    for construct, rank in zip(ranked_constructs, ranks):
        shown = construct_presentation.get(construct["construct"], {})
        bars.append(
            {
                "label": labels[construct["construct"]],
                "percent": construct["percent"],
                "persona": _text(shown, "persona", role),
                "description": _text(shown, "description", role),
                "colour": f"rank-{rank}" if by_rank else _tone(shown),
            }
        )
    return {
        "heading": _text(presentation, "heading", role) or text_for(framework["label"], role),
        "subtitle": _text(presentation, "subtitle", role),
        "bars": bars,
        # ✨ The item scores, grouped by construct in the order they were declared, as the prototype listed them.
        "groups": [
            {
                "label": labels[construct["id"]],
                "colour": _tone(construct_presentation.get(construct["id"], {})),
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
