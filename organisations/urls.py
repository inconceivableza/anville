"""✨ Routes for organisations and groups: joining by link, a participant's groups, and admins' pages."""

from django.urls import path

from organisations.views import join, leave_group, new_group, your_groups, your_organisations

urlpatterns = [
    path("organisations/", your_organisations, name="your_organisations"),
    path("organisations/<int:organisation_id>/groups/new/", new_group, name="new_group"),
    path("join/<str:token>/", join, name="join"),
    path("groups/", your_groups, name="your_groups"),
    path("groups/<int:group_id>/leave/", leave_group, name="leave_group"),
]
