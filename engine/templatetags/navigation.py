from django import template

from engine import views

register = template.Library()


@register.simple_tag(takes_context=True)
def participant_nav(context):
    """✨ The views' own `participant_nav`, worked out only where a participant page's header asks for it, so
    observers' and the coach's pages, and htmx's partial pages, never look up a participant's progress."""
    return views.participant_nav(context["request"])
