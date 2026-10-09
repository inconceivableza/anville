from django.shortcuts import render

from organisations.models import Group


def join(request, token):
    """✨ A group's join link. A token no group holds, whether never issued or replaced, says only that the link no
    longer works, so it reveals nothing about any group."""
    group = Group.objects.filter(join_token=token).select_related("organisation").first()
    if group is None:
        return render(request, "organisations/link_no_longer_works.html", status=404)
    return render(request, "organisations/join.html", {"group": group})
