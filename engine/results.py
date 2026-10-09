# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ The results page and the comparison as the engine derives them: a stored result, dressed in its pathway
version's wording, and on the comparison set beside the observer average.

Nothing here touches the database or a request. The numbers come from the stored result and are never
recomputed, and are shown only as words and places on an axis (ticket 38); the words, standings and tones come from
the same pathway version the result was scored against.
"""

from engine.document.comparison import agreement, comparison_settings, largest_gaps, seen_by_others
from engine.document.observers import minimum_observers
from engine.document.scoring import percents_by_construct
from engine.document.standing import standing
from engine.document.text import text_for

# ✨ The stylesheet defines --rank-1 to --rank-6; every rank below the sixth takes the sixth colour.
RANK_COLOURS = 6

# ✨ How the comparison draws a construct, in its axis's view box's units, where the line runs along y = 3: a dot of
# DOT_RADIUS at each of the participant's and the observers' places, as variant F drew them, with the person icon,
# MARK_SIZE across, just above the participant's dot and the group icon just below the observers'. Stacked so, the two
# icons never cover each other, and each stays over its own value.
DOT_RADIUS = 1.8
MARK_SIZE = 3.5
MARK_CLEARANCE = 0.4

# ✨ Each observer's own dot, shown while the spread is ticked: smaller than the participant's, and where it would
# cover another it drops into a lane of its own below the line, LANE apart, or closer where more lanes are needed
# than fit above the drawing's foot, so every person still shows. The group icon below the line is hidden meanwhile,
# so the lanes have room. The line runs along LINE_Y, and the comparison's drawing ends at DRAWING_FOOT.
OBSERVER_RADIUS = 1.1
LANE = 2.6
LINE_Y = 3
DRAWING_FOOT = 9

# ✨ The drawing's view box runs a little past the axis's 0 to 100 at each end, so a mark at either end is whole.
AXIS_START, AXIS_END = -3, 103

# ✨ How near either side of the drawing, in percents of its width, a centred line of text under it is set against
# that side instead, so it is never cut off.
LABEL_EDGE = 20

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
                document,
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

    Each construct is drawn as variant F drew it (ticket 38): the participant's dot and the observers' on one axis,
    the gap between them shaded, a person icon above the one and a group icon below the other, each with its standing
    in words and whether others see it higher, lower or much the same, in two colours only. Each observer's own dot is
    on the same axis, for the page to reveal on request. The axis is the results page's, its even share in the middle.
    Below the minimum the observer average holds a count and no numbers, and so does what comes out:
    not even the self-result's, nor any gap, standing or strip. Each construct's mean is read from the observer
    average, and its single observers' percents only for the agreement band and the distribution strip, in ascending
    order. The self-result is ranked and the observer average keeps the declared order, so the two are paired by
    construct id. The largest gaps and the reflection prompts follow the drawings.
    """
    shown = {"observers": observer_average["observers"], "minimum": minimum_observers(document), "frameworks": None}
    if observer_average["frameworks"] is None:
        return shown
    observed = {
        framework["framework"]: {construct["construct"]: construct for construct in framework["constructs"]}
        for framework in observer_average["frameworks"]
    }
    page = results_page(document, scores, sort, name="")
    declared = {framework["id"]: framework for framework in document["measurement"]["frameworks"]}
    for framework, scored in zip(page["frameworks"], scores["frameworks"]):
        constructs = len(declared[scored["framework"]]["constructs"])

        def worded(percent):
            return text_for(standing(document, percent, constructs), "participant")

        pairs = [
            (bar, observed[scored["framework"]][construct["construct"]])
            for bar, construct in zip(framework["bars"], scored["constructs"])
        ]
        # ✨ The results page's axis, so each mark of the participant's sits where it does there.
        top = _axis_top(constructs)
        for bar, others in pairs:
            # ✨ The participant's dot is where the results page puts it, in the comparison's own colour, not theirs.
            del bar["colour"]
            you_at, others_at = bar.pop("at"), _at(others["percent"], top)
            bar["you_at"], bar["others_at"] = you_at, others_at
            bar["others_past_end"] = others["percent"] > top
            bar["you_x"], bar["others_x"] = _mark(you_at), _mark(others_at)
            bar["gap_from"], bar["gap_width"] = min(you_at, others_at), round(abs(you_at - others_at), 2)
            bar["others_standing"] = worded(others["percent"])
            bar["seen_by_others"] = text_for(seen_by_others(document, bar["percent"], others["percent"]), "participant")
            bar["agreement"] = text_for(agreement(document, others["per_observer"]), "participant")
            bar["agreement_at"] = _label_at(others_at)
            bar["strip"] = {
                "dots": [
                    {**dot, "past_end": percent > top}
                    for dot, percent in zip(
                        _stacked([_at(percent, top) for percent in others["per_observer"]], you_at),
                        others["per_observer"],
                    )
                ],
                # ✨ `per_observer` is already in ascending order, never the order observers answered (ADR 0005).
                "standings": [worded(percent) for percent in others["per_observer"]],
            }
    return {
        **shown,
        "frameworks": page["frameworks"],
        "marks": {
            "dot_radius": DOT_RADIUS,
            "observer_radius": OBSERVER_RADIUS,
            "size": MARK_SIZE,
            "you_y": round(LINE_Y - DOT_RADIUS - MARK_CLEARANCE - MARK_SIZE, 2),
            "others_y": round(LINE_Y + DOT_RADIUS + MARK_CLEARANCE, 2),
        },
        **_reflection(document, scores, observed),
    }


def _stacked(dots, you_at):
    """✨ Where each observer's dot is drawn: on the line at its place, unless it would cover the participant's dot or
    an observer's already there, and then in the first lane below the line where it covers none. Kept in the order
    given, ascending (ADR 0005), so the lanes say nothing about who answered when."""
    placed = []
    for x in dots:
        lane = 0
        while (lane == 0 and abs(x - you_at) < DOT_RADIUS + OBSERVER_RADIUS) or any(
            other_lane == lane and abs(x - other_x) < 2 * OBSERVER_RADIUS for other_x, other_lane in placed
        ):
            lane += 1
        placed.append((x, lane))
    # ✨ However many lanes there are, they fit between the line and the drawing's foot: more lanes than fit at LANE
    # apart are drawn closer together, so the dots overlap a little but never leave the drawing.
    lanes = max(lane for _, lane in placed) if placed else 0
    spacing = min(LANE, (DRAWING_FOOT - OBSERVER_RADIUS - LINE_Y) / lanes) if lanes else LANE
    return [{"x": x, "y": round(LINE_Y + lane * spacing, 2)} for x, lane in placed]


def _label_at(at):
    """✨ Where a line of text under a drawing is centred so it sits under `at` on the axis: as a percent of the
    drawing's whole width, which runs from AXIS_START to AXIS_END around the axis. Near either end it is set against
    that end instead, so it is never cut off or runs into the columns beside it."""
    across = round((at - AXIS_START) / (AXIS_END - AXIS_START) * 100, 2)
    if across < LABEL_EDGE:
        return {"x": 0, "anchor": "start"}
    if across > 100 - LABEL_EDGE:
        return {"x": 100, "anchor": "end"}
    return {"x": across, "anchor": "middle"}


def _mark(centre):
    """✨ Where a person or group icon starts so that it is centred on `centre`."""
    return round(centre - MARK_SIZE / 2, 2)


def _reflection(document, scores, observed):
    """✨ Below the drawings: the largest gaps, worded, and the questions to reflect on, all from the document.

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


def _axis_top(constructs):
    """✨ Where a framework's axis ends: twice an even share of it, so the even share's tick is always in the middle
    and the axis is the same for every participant, on the results page and the comparison alike (ticket 38,
    developer's call, in place of variant F's next ten up from the largest share)."""
    return 2 * 100 / constructs


def _at(percent, top):
    """✨ Where a percent sits on an axis ending at `top`, as a percent of the axis's width, for the SVG to draw. A
    share past the end, more than twice an even share, sits at the end, where the templates add an arrow past it."""
    return round(min(percent / top, 1) * 100, 2)


def _framework(document, framework, presentation, ranked_constructs, construct_presentation, items, sort, role):
    labels = {construct["id"]: text_for(construct["label"], role) for construct in framework["constructs"]}
    by_rank = presentation.get("bars") == "rank"
    ranks = bar_ranks([construct["percent"] for construct in ranked_constructs])
    constructs = len(framework["constructs"])
    top = _axis_top(constructs)
    bars = []
    for construct, rank in zip(ranked_constructs, ranks):
        shown = construct_presentation.get(construct["construct"], {})
        bars.append(
            {
                "label": labels[construct["construct"]],
                "percent": construct["percent"],
                "standing": text_for(standing(document, construct["percent"], constructs), role),
                "at": _at(construct["percent"], top),
                "past_end": construct["percent"] > top,
                "persona": _text(shown, "persona", role),
                "description": _text(shown, "description", role),
                "colour": f"rank-{rank}" if by_rank else _tone(shown),
            }
        )
    return {
        "heading": _text(presentation, "heading", role) or text_for(framework["label"], role),
        "subtitle": _text(presentation, "subtitle", role),
        # ✨ The dashed tick: an even share of the framework, 100 divided among its constructs.
        "even_at": _at(100 / constructs, top),
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
