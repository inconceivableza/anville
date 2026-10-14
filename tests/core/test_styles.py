# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The look is themeable later only if colours live in one place: the stylesheet's :root variables."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLESHEET = ROOT / "frontend" / "src" / "styles.css"
TEMPLATES = sorted(path for app in ("access", "engine") for path in (ROOT / app / "templates").rglob("*.html"))

# Hex colours, functional colours and the named colours most likely to slip in (but not var(--white) or white-space).
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


# ✨ The final prototype's two typefaces (ticket 48). A stack may fall back to system fonts after its first family.
PROTOTYPE_FAMILIES = {"Switzer", "Newsreader", "Newsreader Variable"}


def _first_family(stack):
    return stack.split(",")[0].strip().strip("\"'")


def test_only_the_prototypes_two_typefaces_are_loaded_or_named_and_each_font_variable_is_defined_once():
    css = re.sub(r"/\*.*?\*/", "", STYLESHEET.read_text(), flags=re.S)
    imports = re.findall(r'@import\s+"([^"]+)"', css)
    variables = re.findall(r"(--font-[\w-]+)\s*:\s*([^;]+);", css)
    literal_stacks = [stack for stack in re.findall(r"font-family\s*:\s*([^;]+);", css) if "var(" not in stack]

    assert [name for name in imports if "newsreader" not in name] == []
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
    pairs = {selector: _rule_colours(css, selector) for selector in ("body", ".btn-primary", ".btn-secondary")}
    pairs["muted text on the page"] = ("--ink-muted", "--cream")
    pairs["text on the dark panels"] = ("--on-dark", "--deep")

    ratios = {name: round(_contrast(colours[text], colours[background]), 2) for name, (text, background) in pairs.items()}

    assert {name: ratio for name, ratio in ratios.items() if ratio < 4.5} == {}
