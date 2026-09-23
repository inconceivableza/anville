"""✨ What every rendered page is checked for, shared by the journey tests."""

import re


def loads_the_built_stylesheet(page):
    return re.search(r'<link\s+rel="stylesheet" href="/static/assets/main-[\w-]+\.css" />', page) is not None


def version_on(page):
    """✨ The pathway version a rendered page's forms name, which is what a browser would send back."""
    shown = re.search(r'name="version" value="(\d+)"', page)
    return shown.group(1) if shown else None
