from django import template

from engine.views import page_url

register = template.Library()

# ✨ The views' own `page_url`, so a template links to a page exactly as a redirect does.
register.simple_tag(page_url)
