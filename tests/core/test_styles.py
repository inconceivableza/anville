"""✨ The look is themeable later only if colours live in one place: the stylesheet's :root variables."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLESHEET = ROOT / "frontend" / "src" / "styles.css"
TEMPLATES = sorted((ROOT / "engine" / "templates").rglob("*.html"))

# Hex colours, functional colours and the named colours most likely to slip in (but not var(--white)).
RAW_COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|lab|lch)\(|(?<![-\w])(?:white|black)\b")


def _outside_root_block(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return re.sub(r":root\s*\{[^}]*\}", "", css, count=1)


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
