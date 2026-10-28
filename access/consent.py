# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

from functools import wraps

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from access.models import Account, Consent

# ✨ The version of the text in templates/access/consent_text.html. Raise it whenever a change alters what a
# participant agrees to (not for a typo), and everyone is asked again before they continue. Version 3 leaves out
# group admins while no organisation is set up (ADR 0021).
CONSENT_TEXT_VERSION = 3


def current_text_version():
    """✨ Read when asked rather than imported, so a raised version reaches every caller at once."""
    return CONSENT_TEXT_VERSION


def current_consents():
    """✨ Every consent to the current text that has not been withdrawn, whoever gave it."""
    return Consent.objects.filter(text_version=current_text_version(), withdrawn_at__isnull=True)


def current_consent(participant):
    """✨ The participant's consent to the current text, or None if they have not given it."""
    return current_consents().filter(participant=participant).order_by("-given_at").first()


def latest_consent(participant):
    """✨ The participant's most recent consent, whatever has happened to it since, or None if they never gave one."""
    return Consent.objects.filter(participant=participant).order_by("-given_at").first()


def withdrawn_participants():
    """✨ The participants whose consent is withdrawn: they withdrew and have not agreed since, as ids to filter by. A
    consent merely out of date, to a text that has since changed, is not withdrawn (ticket 45)."""
    standing = Consent.objects.filter(withdrawn_at__isnull=True).values("participant")
    return Consent.objects.filter(withdrawn_at__isnull=False).exclude(participant__in=standing).values("participant")


def text_changed(request):
    """✨ Whether a press agreed to a version of the text other than the current one, as when it changed while the page
    was open: consent is to the text that was read, so it is read again."""
    return request.method == "POST" and request.POST.get("version") != str(current_text_version())


@transaction.atomic
def pass_entry_page(participant, display_name):
    """✨ What passing the entry page keeps (ADR 0021), all at once: the first name given there, when "I am 18 or over"
    was ticked, and consent to the current text, as the consent page records it."""
    now = timezone.now()
    Account.objects.update_or_create(
        participant=participant, defaults={"display_name": display_name, "adult_confirmed_at": now}
    )
    Consent.objects.create(participant=participant, text_version=current_text_version(), given_at=now)


def withdraw(participant):
    """✨ Withdraw every consent still standing. The rows stay, as the record of what was consented to and when.

    Stored answers are kept for now: what withdrawal does to them is open (spec, "Legalities are parked").
    """
    Consent.objects.filter(participant=participant, withdrawn_at__isnull=True).update(withdrawn_at=timezone.now())


def has_passed_entry_page(participant):
    """✨ Whether the participant has passed the entry page, saying they are 18 or over and consenting (ADR 0021). An
    account made before it ticked 18 or over at sign-up, where the time was not kept, and then consented on the
    consent page, so any consent on record, even one withdrawn or out of date, counts as having passed it."""
    account = getattr(participant, "account", None)
    if account is not None and account.adult_confirmed_at is not None:
        return True
    return Consent.objects.filter(participant=participant).exists()


def where_consent_is_asked(participant):
    """✨ The name of the page that asks for the participant's consent: the entry page until they have passed it, and
    after that the consent page, which asks again after a withdrawal or a change to the text."""
    return "consent" if has_passed_entry_page(participant) else "entry_page"


def consent_required(view):
    """✨ Nothing of the pathway is shown or stored until the participant has consented to the current text.

    Goes beneath `login_required`, which decides who the participant is. htmx is told to go to the page that asks
    rather than swap it into the middle of a section, in the way a sort is sent on to its results.
    """

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if current_consent(request.user) is not None:
            return view(request, *args, **kwargs)
        asked = where_consent_is_asked(request.user)
        if request.headers.get("HX-Request") == "true":
            return HttpResponse(headers={"HX-Redirect": reverse(asked)})
        return redirect(asked)

    return wrapped
