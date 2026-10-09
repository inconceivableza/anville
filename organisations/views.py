from urllib.parse import urlencode

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from access.consent import current_consent
from organisations import joining
from organisations.models import Group, Membership


@require_http_methods(["GET", "POST"])
def join(request, token):
    """✨ A group's join link. A token no group holds, whether never issued or replaced, says only that the link no
    longer works, so it reveals nothing about any group.

    Otherwise the link is held in the session, so sign-up drops the enrolment code, and the visitor is sent to sign
    up, then to consent, each told to come back here. The page names the group and what its admins see; only "Join"
    records anything, and it leads to the hub.
    """
    group = Group.objects.filter(join_token=token).select_related("organisation").first()
    if group is None:
        return render(request, "organisations/link_no_longer_works.html", status=404)
    joining.hold(request.session, group)
    if not request.user.is_authenticated:
        return _then_back_here("account_signup", request)
    if current_consent(request.user) is None:
        return _then_back_here("consent", request)
    if request.method == "POST":
        Membership.objects.get_or_create(participant=request.user, group=group)
        joining.release(request.session)
        response = redirect("hub")
        response.status_code = 303  # ✨ the browser GETs the hub rather than repeat the POST
        return response
    return render(request, "organisations/join.html", {"group": group})


def _then_back_here(where, request):
    return redirect(f"{reverse(where)}?{urlencode({'next': request.path})}")
