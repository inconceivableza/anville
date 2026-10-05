"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path, re_path
from access.views import consent, password_reset_unavailable
from engine.views import (
    answer_coaching,
    coach_checklist,
    coaching,
    comparison,
    complete_section,
    hub,
    invitations,
    issue_invitation,
    move_past_page,
    observe,
    observer,
    reopen_section,
    results,
    revoke_invitation,
    save_answer,
    section,
    send_assessment,
    share_with_coach,
    start,
    start_observing,
    visit_comparison,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # ✨ Ahead of allauth's own routes, so every password reset page is refused until email exists (ticket 28a).
    re_path(r"^accounts/password/reset/", password_reset_unavailable),
    path("accounts/", include("allauth.urls")),
    path("consent/", consent, name="consent"),
    path("start/", start, name="start"),
    path("answers/<slug:block_id>/", save_answer, name="save_answer"),
    path("coach/<slug:block_id>/", coach_checklist, name="coach_checklist"),
    path("results/<slug:block_id>/", results, name="results"),
    path("results/<slug:block_id>/comparison/", comparison, name="comparison"),
    path("results/<slug:block_id>/comparison/visit/", visit_comparison, name="visit_comparison"),
    path("results/<slug:block_id>/comparison/coach/", share_with_coach, name="share_with_coach"),
    path("invitations/", invitations, name="invitations"),
    path("invitations/<int:contact_id>/issue/", issue_invitation, name="issue_invitation"),
    path("invitations/<int:contact_id>/revoke/", revoke_invitation, name="revoke_invitation"),
    path("observe/", observer, name="observer"),
    # ✨ Ahead of the link's own route, which would otherwise take "assessment" for a token.
    path("observe/assessment/", send_assessment, name="send_assessment"),
    path("observe/<str:token>/", observe, name="observe"),
    path("observe/<str:token>/start/", start_observing, name="start_observing"),
    path("observe/<str:token>/assessment/", send_assessment, name="send_assessment_by_link"),
    # ✨ The coach's link (ticket 13c), apart from the observers', so neither kind of link works at the other's address.
    path("coaching/<str:token>/", coaching, name="coaching"),
    path("coaching/<str:token>/answer/", answer_coaching, name="answer_coaching"),
    path("sections/<slug:section_id>/", section, name="section"),
    path("sections/<slug:section_id>/pages/<int:page>/", section, name="section_page"),
    path("sections/<slug:section_id>/pages/<int:page>/continue/", move_past_page, name="move_past_page"),
    path("sections/<slug:section_id>/complete/", complete_section, name="complete_section"),
    path("sections/<slug:section_id>/reopen/", reopen_section, name="reopen_section"),
    path("", hub, name="hub"),
]
