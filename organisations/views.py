from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from access.consent import consent_required
from organisations.models import Group


@login_required
@consent_required
def your_groups(request):
    """✨ Each group the participant is in, with its organisation and what its admins see. Admins are not named."""
    groups = (
        Group.objects.filter(memberships__participant=request.user)
        .select_related("organisation")
        .order_by("organisation__name", "name")
    )
    return render(request, "organisations/your_groups.html", {"groups": groups})


@login_required
@consent_required
def leave_group(request, group_id):
    raise Http404
