# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from django.conf import settings


def demo_notice(request):
    """✨ The notice a demo deployment shows where people arrive and sign up (ticket 26), or nothing."""
    return {"demo_notice": settings.ANVILLE_DEMO_NOTICE}
