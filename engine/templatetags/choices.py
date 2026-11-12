# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

from django import template

from engine.document.blocks import choices_of

register = template.Library()

# ✨ The block type's own reading of a choice of many (`choices_of`), so its template ticks what the answer holds.
register.filter("choices_of", choices_of)
