from functools import wraps

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from access.models import Consent

# ✨ The version of the text in templates/access/consent.html. Raise it whenever a change alters what a
# participant agrees to (not for a typo), and everyone is asked again before they continue.
CONSENT_TEXT_VERSION = 1


def current_consent(participant):
    """✨ The participant's agreement to the current text, or None if they have not given one."""
    return (
        Consent.objects.filter(participant=participant, text_version=CONSENT_TEXT_VERSION, withdrawn_at__isnull=True)
        .order_by("-given_at")
        .first()
    )


def consent_required(view):
    """✨ Nothing of the pathway is shown or stored until the participant has agreed to the current text.

    Goes beneath `login_required`, which decides who the participant is. htmx is told to go to the consent
    page rather than swap it into the middle of a section, in the way a sort is sent on to its results.
    """

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if current_consent(request.user) is not None:
            return view(request, *args, **kwargs)
        if request.headers.get("HX-Request") == "true":
            return HttpResponse(headers={"HX-Redirect": reverse("consent")})
        return redirect("consent")

    return wrapped
