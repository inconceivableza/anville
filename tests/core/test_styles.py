# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The look is themeable later only if colours live in one place: the stylesheet's :root variables."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLESHEET = ROOT / "frontend" / "src" / "styles.css"
TEMPLATES = sorted(path for app in ("access", "engine") for path in (ROOT / app / "templates").rglob("*.html"))

# Hex colours, functional colours and the named colours most likely to slip in (but not var(--white-40) or white-space).
RAW_COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|lab|lch)\(|(?<![-\w])(?:white|black)\b(?!-)")


def _outside_root_block(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return re.sub(r":root\s*\{[^}]*\}", "", css, count=1)


def test_a_property_named_like_a_colour_is_not_taken_for_one():
    assert RAW_COLOUR.findall("white-space: nowrap;") == []
    assert RAW_COLOUR.findall("color: white;") == ["white"]


def test_the_stylesheet_uses_raw_colours_only_to_define_its_colour_variables():
    assert RAW_COLOUR.findall(_outside_root_block(STYLESHEET.read_text())) == []


def test_templates_use_no_raw_colours_and_no_inline_styles():
    for template in TEMPLATES:
        html = template.read_text()
        assert RAW_COLOUR.findall(html) == [], template.name
        assert "style=" not in html, template.name


def test_fonts_are_self_hosted_never_fetched_from_google():
    for source in [STYLESHEET, ROOT / "frontend" / "src" / "main.js", *TEMPLATES]:
        text = source.read_text()
        assert "fonts.googleapis.com" not in text, source.name
        assert "fonts.gstatic.com" not in text, source.name


# ✨ The final prototype's headings typeface and, for text, Instrument Sans in place of its Switzer, whose licence keeps
# it out of a public repository or image (ticket 48). A stack may fall back to system fonts after its first family.
PROTOTYPE_FAMILIES = {"Instrument Sans Variable", "Newsreader Variable"}
FONT_PACKAGES = ("@fontsource-variable/newsreader/", "@fontsource-variable/instrument-sans/")


def _first_family(stack):
    return stack.split(",")[0].strip().strip("\"'")


def test_only_the_prototypes_two_typefaces_are_loaded_or_named_and_each_font_variable_is_defined_once():
    css = re.sub(r"/\*.*?\*/", "", STYLESHEET.read_text(), flags=re.S)
    imports = re.findall(r'@import\s+"([^"]+)"', css)
    variables = re.findall(r"(--font-[\w-]+)\s*:\s*([^;]+);", css)
    literal_stacks = [stack for stack in re.findall(r"font-family\s*:\s*([^;]+);", css) if "var(" not in stack]

    assert [name for name in imports if not name.startswith(FONT_PACKAGES)] == []
    assert "@font-face" not in css  # ✨ every font comes from its package; none is committed
    assert [stack for _, stack in variables if _first_family(stack) not in PROTOTYPE_FAMILIES] == []
    assert [stack for stack in literal_stacks if _first_family(stack) not in PROTOTYPE_FAMILIES] == []
    names = [name for name, _ in variables]
    assert sorted({name for name in names if names.count(name) > 1}) == []


def _root_colours(css):
    root = re.search(r":root\s*\{([^}]*)\}", re.sub(r"/\*.*?\*/", "", css, flags=re.S)).group(1)
    return dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;", root))


def _rule_colours(css, selector):
    """✨ The variables a rule's own color and background name, as (text, background)."""
    body = re.search(rf"(?m)^{re.escape(selector)}\s*\{{([^}}]*)\}}", css).group(1)
    text = re.search(r"(?<![-\w])color\s*:\s*var\((--[\w-]+)\)", body).group(1)
    background = re.search(r"background(?:-color)?\s*:\s*var\((--[\w-]+)\)", body).group(1)
    return text, background


def _contrast(foreground, background):
    """✨ WCAG 2's contrast ratio between two #rrggbb colours."""

    def luminance(hex_colour):
        channels = [int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def test_body_text_and_buttons_meet_wcag_aa_contrast():
    css = STYLESHEET.read_text()
    colours = _root_colours(css)
    # ✨ a ghost pill has the text's own colours; a rating's chosen point, and those below it (fix-2)
    selectors = ("body", ".pill", ".rate-point:has(input:checked)", ".rate-point:has(~ .rate-point input:checked)")
    pairs = {selector: _rule_colours(css, selector) for selector in selectors}
    pairs["muted text on the page"] = ("--muted", "--cream")
    pairs["text on the dark panels"] = ("--on-dark", "--brown")
    # ✨ Each standing's word on the results' paper cards, in its darker text shade (fix-17).
    for standing in ("1", "2", "3", "below"):
        pairs[f"standing {standing}'s word on the results"] = (f"--standing-{standing}-text", "--paper")

    ratios = {name: round(_contrast(colours[text], colours[background]), 2) for name, (text, background) in pairs.items()}

    assert {name: ratio for name, ratio in ratios.items() if ratio < 4.5} == {}


# ✨ Colours made to be read on the dark panels, and the results' and comparison's colours, which the prototype fixes
# and ticket 48 keeps unchanged; every other text colour is read on the page's cream. ✨ Of the standings' colours, only
# the bright ones the dots and lines take are exempt: the -text shades their words take are checked (fix-17).
ON_DARK = re.compile(r"--(on-dark[\w-]*|cream[\w-]*|snow|paper|green)$")
FIXED_BY_THE_RESULTS = re.compile(r"--(tone-[\w-]+|standing-(?:\d+|below)|comparison-[\w-]+|blue-soft)$")


def test_every_text_colour_set_without_its_own_background_is_readable_on_the_page():
    css = re.sub(r"/\*.*?\*/", "", STYLESHEET.read_text(), flags=re.S)
    colours = _root_colours(css)
    rules = re.findall(r"([^{}]+)\{([^{}]*)\}", re.sub(r":root\s*\{[^}]*\}", "", css, count=1))

    unreadable = {}
    for selector, declarations in rules:
        text = re.search(r"(?<![-\w])color\s*:\s*var\((--[\w-]+)\)", declarations)
        if not text or "background" in declarations or ON_DARK.search(text.group(1)):
            continue
        if FIXED_BY_THE_RESULTS.search(text.group(1)) or text.group(1) not in colours:
            continue
        ratio = _contrast(colours[text.group(1)], colours["--cream"])
        if ratio < 4.5:
            unreadable[" ".join(selector.split())] = (text.group(1), round(ratio, 2))

    assert unreadable == {}


def test_the_comparison_shows_the_participant_in_the_original_prototypes_green():
    css = STYLESHEET.read_text()
    text = re.search(r"(?m)^\.comparison-you\s*\{\s*color\s*:\s*var\((--[\w-]+)\)", css).group(1)

    assert _root_colours(css)[text] == "#1a7a4c"
