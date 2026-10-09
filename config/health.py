# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


@never_cache
@require_safe
def healthz(request):
    """✨ Whether this copy of Anville can serve, and which commit it was built from.

    A deploy asks for this from outside to confirm that the commit it just rolled out is the one answering.
    It reaches the database with one trivial query, since nothing else here works without it.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse({"status": "database unavailable", "commit": settings.ANVILLE_COMMIT}, status=503)
    return JsonResponse({"status": "ok", "commit": settings.ANVILLE_COMMIT})
