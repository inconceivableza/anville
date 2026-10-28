# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render, resolve_url
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_http_methods

from access.consent import (
    current_consent,
    current_text_version,
    has_passed_entry_page,
    latest_consent,
    pass_entry_page,
    text_changed,
    withdraw,
)
from access.forms import EntryPageForm
from access.models import Consent, name_shown_for
from engine.hub import entry_page_step, track_sections
from engine.models import Publication, Response


@login_required
@require_http_methods(["GET", "POST"])
def consent(request):
    """✨ The participant's own decision about the consent text, separate from the enrolment code (ADR 0004).

    Agreeing records the version of the text the page showed and when, then goes on to the page that sent the
    participant here, if it named itself as `next` on this site, or else to the start. Declining records nothing.
    Withdrawing marks their consent withdrawn, and the pathway waits for consent again.

    A participant who has not passed the entry page is sent there, whatever they pressed, with the same `next`:
    consent is first given there, beside "I am 18 or over", so agreeing here cannot step round it (ADR 0021).
    """
    after = next_on_this_site(request)
    if not has_passed_entry_page(request.user):
        entry_page = reverse("entry_page")
        return _see_other(f"{entry_page}?{urlencode({'next': after})}" if after else entry_page)
    given = current_consent(request.user)
    version = current_text_version()
    decision = request.POST.get("decision")
    if given is None and decision == "decline":
        return render(request, "access/consent_declined.html")
    if given is None and decision == "agree":
        # ✨ Consent is to the text that was read. If it changed while the page was open, read it again.
        if text_changed(request):
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


@login_required
@require_http_methods(["GET", "POST"])
def entry_page(request):
    """✨ The entry page, the engine's and authored by no pathway (ADR 0021): the first name, filled in from the
    account and changeable, "I am 18 or over", and the consent tick, with the consent text beside it. It comes before
    the track's first wizard, in its layout, as step 1 of its steps.

    Continue is refused, storing nothing, unless all three are given, the refusals shown only after the press. Passing
    it keeps the name, when 18 or over was ticked and consent to the text the page showed, then goes on as agreeing on
    the consent page does. Once passed it is never asked again: the hub leads on, and the consent page asks again after
    a withdrawal or a change to the text.

    With htmx (fix-2), a refusal sends back the form alone, to take its own place, and passing tells htmx where to go.
    """
    if has_passed_entry_page(request.user):
        return redirect("hub")
    after = next_on_this_site(request)
    form = EntryPageForm(request.POST or None, initial={"display_name": name_shown_for(request.user)})
    changed = text_changed(request)
    is_htmx = request.headers.get("HX-Request") == "true"
    if request.method == "POST" and form.is_valid() and not changed:
        pass_entry_page(request.user, form.cleaned_data["display_name"])
        if is_htmx:
            return HttpResponse(headers={"HX-Redirect": resolve_url(after or "start")})
        return _see_other(after or "start")
    step = entry_page_step(_track_of(request.user))
    shown = {
        "form": form,
        "version": current_text_version(),
        "next": after,
        "text_changed": changed,
        "step": step,
        "steps": step.numbers,
    }
    template = "access/entry_page_form.html" if is_htmx and request.method == "POST" else "access/entry_page.html"
    return render(request, template, shown, status=400 if request.method == "POST" else 200)


def _track_of(participant):
    """✨ The sections of the participant's track, in the version they answer, or before their first answer the
    published one, as the pathway's own pages read it; none while nothing is published."""
    response = Response.in_progress(participant)
    version = response.version if response is not None else Publication.current_version()
    return track_sections(version.document) if version is not None else []


def next_on_this_site(request):
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
