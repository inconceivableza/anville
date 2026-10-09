from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from access.consent import consent_required


@login_required
@consent_required
def your_groups(request):
    """✨ Each group the participant is in, with its organisation and what its admins see."""
    return render(request, "organisations/your_groups.html")


@login_required
@consent_required
def leave_group(request, group_id):
    raise Http404
