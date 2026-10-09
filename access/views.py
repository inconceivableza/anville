# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from access.consent import current_consent, current_text_version, latest_consent, withdraw
from access.models import Consent


def password_reset_unavailable(request, *args, **kwargs):
    """✨ Every password reset page, refused until email delivery exists (ticket 28a). Without a mail server
    allauth's reset form crashes, and the spec promises no email the system cannot send."""
    raise Http404("Password reset is not available.")


@login_required
@require_http_methods(["GET", "POST"])
def consent(request):
    """✨ The participant's own decision about the consent text, separate from the enrolment code (ADR 0004).

    Agreeing records the version of the text the page showed and when, then goes on to the page that sent the
    participant here, if it named itself as `next` on this site, or else to the start. Declining records nothing.
    Withdrawing marks their consent withdrawn, and the pathway waits for consent again.
    """
    given = current_consent(request.user)
    version = current_text_version()
    decision = request.POST.get("decision")
    after = _next_on_this_site(request)
    if given is None and decision == "decline":
        return render(request, "access/consent_declined.html")
    if given is None and decision == "agree":
        # ✨ Consent is to the text that was read. If it changed while the page was open, read it again.
        if request.POST.get("version") != str(version):
            page = _page(request.user, version, given, after, text_changed=True)
            return render(request, "access/consent.html", page, status=400)
        Consent.objects.create(participant=request.user, text_version=version)
        return _see_other(after or "start")
    if given is not None and decision == "withdraw":
        withdraw(request.user)
        return _see_other("consent")
    if request.method == "POST":
        return _see_other("consent")
    return render(request, "access/consent.html", _page(request.user, version, given, after))


def _next_on_this_site(request):
    """✨ The `next` the request names, as sign-in's own is read, kept only if it is a page on this site."""
    after = request.POST.get("next") or request.GET.get("next")
    if after and url_has_allowed_host_and_scheme(after, {request.get_host()}, require_https=request.is_secure()):
        return after
    return None


def _page(participant, version, given, after, *, text_changed=False):
    """✨ The text, and where the participant stands with it: agreed, withdrawn, or agreed to an earlier version."""
    return {
        "version": version,
        "given": given,
        "previous": latest_consent(participant),
        "next": after,
        "text_changed": text_changed,
    }


def _see_other(where):
    """✨ After a POST, the browser should GET the page it lands on rather than repeat the POST."""
    response = redirect(where)
    response.status_code = 303
    return response
