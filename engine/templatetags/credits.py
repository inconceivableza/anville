# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def credit_shown(credit):
    """✨ A `Credit` as the credits page lists it (sprint-3d-r1-fix-5). With an author, from its parts, each linked where
    it gives an address: "[description], by [author] on [source], [licence]." or, with the work's own title, as a
    Creative Commons licence asks, "“[title]” by [author] on [source], [licence].", after "[description]: " where it has
    one. Without an author, its wording as written."""
    if credit.author is None:
        return credit.text
    if credit.title is None:
        what = format_html("{},", credit.description)
    elif credit.description:
        what = format_html("{}: “{}”", credit.description, _part(credit.title))
    else:
        what = format_html("“{}”", _part(credit.title))
    shown = format_html("{} by {}", what, _part(credit.author))
    if credit.source:
        shown = format_html("{} on {}", shown, _part(credit.source))
    if credit.licence:
        shown = format_html("{}, {}", shown, _part(credit.licence))
    return format_html("{}.", shown)


def _part(part):
    """✨ A part of a credit: its name, linked where it gives an address."""
    return format_html('<a href="{}">{}</a>', part.url, part.name) if part.url else part.name
