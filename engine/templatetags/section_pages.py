from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def page_url(section_id, page=1):
    """✨ The address of one page of a section. The first is the section's own address, as before it had pages."""
    if page == 1:
        return reverse("section", args=[section_id])
    return reverse("section_page", args=[section_id, page])
