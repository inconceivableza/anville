"""✨ What every rendered page is checked for, shared by the journey tests."""

import re


def loads_the_built_stylesheet(page):
    return re.search(r'<link\s+rel="stylesheet" href="/static/assets/main-[\w-]+\.css" />', page) is not None
