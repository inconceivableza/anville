# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

from django import template

from engine import demo_shortcuts

register = template.Library()


@register.simple_tag
def made_up_address():
    """✨ Demo only (ticket 113): a made-up address to sign up with, chosen afresh on each page
    (`demo_shortcuts.example_address`), where demo tools are on; otherwise nothing."""
    return demo_shortcuts.example_address() if demo_shortcuts.tools_on() else ""
