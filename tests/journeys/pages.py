# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ What every rendered page is checked for, shared by the journey tests."""

import re
from html import unescape


def main_of(page):
    """✨ The page's own content, without the header and its pathway sidebar, which repeat the hub's steps."""
    return re.search(r"<main.*?</main>", page, re.S).group(0)


def text_of(page):
    """✨ The page's words as a reader sees them: no tags, entities decoded, and every run of whitespace one space,
    so a sentence the template wraps across lines, or that crosses a tag like <strong>, is still found whole.
    Tags are dropped, not spaced, so "</strong>," stays joined to its comma."""
    return " ".join(unescape(re.sub(r"<[^>]+>", "", page)).split())


def gate_checklist(page):
    """✨ The gate's checklist beneath "Mark complete", as {message: whether it is met}."""
    items = re.findall(r'<li class="gate-item( is-met)?">.*?<span class="gate-message">(.*?)</span>', page, re.S)
    return {unescape(message): bool(met) for met, message in items}


def loads_the_built_stylesheet(page):
    return re.search(r'<link\s+rel="stylesheet" href="/static/assets/main-[\w-]+\.css" />', page) is not None


def version_on(page):
    """✨ The pathway version a rendered page's forms name, which is what a browser would send back."""
    shown = re.search(r'name="version" value="(\d+)"', page)
    return shown.group(1) if shown else None
