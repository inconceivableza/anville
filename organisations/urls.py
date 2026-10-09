"""✨ Routes for organisations and groups: joining by link, a participant's groups, and admins' pages."""

from django.urls import path

from organisations.views import join

urlpatterns = [
    path("join/<str:token>/", join, name="join"),
]
