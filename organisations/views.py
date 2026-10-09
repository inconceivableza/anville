from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from access.consent import consent_required
from organisations.models import Group, Membership


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
@require_http_methods(["GET", "POST"])
def leave_group(request, group_id):
    """✨ Asks the participant to confirm, then ends their membership of the group. Their answers are not touched.
    A group they are not in is not found."""
    membership = get_object_or_404(
        Membership.objects.select_related("group__organisation"), participant=request.user, group_id=group_id
    )
    if request.method == "POST":
        membership.delete()
        response = redirect("your_groups")
        response.status_code = 303
        return response
    return render(request, "organisations/leave_group.html", {"group": membership.group})
