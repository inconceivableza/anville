from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from access.consent import CONSENT_TEXT_VERSION, current_consent
from access.models import Consent


def password_reset_unavailable(request, *args, **kwargs):
    """✨ Every password reset page, refused until email delivery exists (ticket 28). Without a mail server
    allauth's reset form crashes, and the spec promises no email the system cannot send."""
    raise Http404("Password reset is not available.")


@login_required
@require_http_methods(["GET", "POST"])
def consent(request):
    """✨ The participant's own decision about the consent text, separate from the enrolment code (ADR 0004).

    Agreeing records the version of the text the page showed and when. Declining records nothing.
    """
    given = current_consent(request.user)
    decision = request.POST.get("decision")
    if given is None and decision == "decline":
        return render(request, "access/consent_declined.html")
    if given is None and decision == "agree":
        # ✨ Agreement is to the text that was read. If it changed while the page was open, read it again.
        if request.POST.get("version") != str(CONSENT_TEXT_VERSION):
            return render(request, "access/consent.html", _page(given, text_changed=True), status=400)
        Consent.objects.create(participant=request.user, text_version=CONSENT_TEXT_VERSION)
        return _see_other("hub")
    if request.method == "POST":
        return _see_other("consent")
    return render(request, "access/consent.html", _page(given))


def _page(given, *, text_changed=False):
    return {"version": CONSENT_TEXT_VERSION, "given": given, "text_changed": text_changed}


def _see_other(where):
    """✨ After a POST, the browser should GET the page it lands on rather than repeat the POST."""
    response = redirect(where)
    response.status_code = 303
    return response
