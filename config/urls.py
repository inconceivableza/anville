# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

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
from django.urls import include, path
from access.views import consent
from config.health import healthz
from engine.views import (
    another_row,
    answer_coaching,
    coach_checklist,
    coaching,
    comparison,
    complete_section,
    contact,
    contact_removal,
    contacts,
    credits_page,
    download,
    first_page,
    fresh_link,
    home,
    hub,
    invitations,
    issue_invitation,
    move_past_page,
    observe,
    observer,
    photo,
    reopen_section,
    results,
    retake,
    revoke_invitation,
    save_answer,
    section,
    send_assessment,
    share_with_coach,
    start,
    start_observing,
    stop_reminders,
    tie_break,
    visit_comparison,
    withdrawal,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz, name="healthz"),
    path("accounts/", include("allauth.urls")),
    path("consent/", consent, name="consent"),
    path("about-you/", first_page, name="first_page"),
    path("start/", start, name="start"),
    path("answers/<slug:block_id>/", save_answer, name="save_answer"),
    path("coach/<slug:block_id>/", coach_checklist, name="coach_checklist"),
    path("results/<slug:block_id>/", results, name="results"),
    path("results/<slug:block_id>/tie-break/", tie_break, name="tie_break"),
    path("results/<slug:block_id>/retake/", retake, name="retake"),  # ✨ demo only (fix-19)
    path("results/<slug:block_id>/comparison/", comparison, name="comparison"),
    path("results/<slug:block_id>/comparison/visit/", visit_comparison, name="visit_comparison"),
    path("results/<slug:block_id>/comparison/coach/", share_with_coach, name="share_with_coach"),
    path("downloads/<slug:block_id>/", download, name="download"),
    path("photos/<slug:section_id>/", photo, name="photo"),
    # ✨ A contact list's people, each added (with their link) or changed on their own (ticket 51a).
    path("contacts/<slug:block_id>/", contacts, name="contacts"),
    path("contacts/<slug:block_id>/<int:contact_id>/", contact, name="contact"),
    # ✨ Taking one person off the list, asking first while their link works (ticket 13d).
    path("contacts/<slug:block_id>/<int:contact_id>/remove/", contact_removal, name="contact_removal"),
    # ✨ One more empty row, below the rest, storing nobody (ticket 70).
    path("contacts/<slug:block_id>/rows/", another_row, name="another_row"),
    path("invitations/", invitations, name="invitations"),
    path("invitations/<int:contact_id>/issue/", issue_invitation, name="issue_invitation"),
    path("invitations/<int:contact_id>/revoke/", revoke_invitation, name="revoke_invitation"),
    path("observe/", observer, name="observer"),
    # ✨ Ahead of the link's own route, which would otherwise take "assessment" for a token.
    path("observe/assessment/", send_assessment, name="send_assessment"),
    path("observe/withdraw/", withdrawal, name="withdrawal"),
    path("observe/<str:token>/", observe, name="observe"),
    path("observe/<str:token>/start/", start_observing, name="start_observing"),
    path("observe/<str:token>/assessment/", send_assessment, name="send_assessment_by_link"),
    path("observe/<str:token>/withdraw/", withdrawal, name="withdrawal_by_link"),
    # ✨ A reminder's stop link (ticket 43a), which works whatever has happened to the observer's own link.
    path("reminders/stop/<str:signed>/", stop_reminders, name="stop_reminders"),
    # ✨ A reminder's button, which gives the observer a fresh link of their own (ticket 43b).
    path("reminders/answer/<str:signed>/", fresh_link, name="fresh_link"),
    # ✨ The coach's link (ticket 13c), apart from the observers', so neither kind of link works at the other's address.
    path("coaching/<str:token>/", coaching, name="coaching"),
    path("coaching/<str:token>/answer/", answer_coaching, name="answer_coaching"),
    path("sections/<slug:section_id>/", section, name="section"),
    path("sections/<slug:section_id>/pages/<int:page>/", section, name="section_page"),
    path("sections/<slug:section_id>/pages/<int:page>/continue/", move_past_page, name="move_past_page"),
    path("sections/<slug:section_id>/complete/", complete_section, name="complete_section"),
    path("sections/<slug:section_id>/reopen/", reopen_section, name="reopen_section"),
    path("hub/", hub, name="hub"),
    path("credits/", credits_page, name="credits"),
    # ✨ Joining by link, a participant's groups and admins' pages; each adds its routes in organisations/urls.py.
    path("", include("organisations.urls")),
    path("", home, name="home"),
]
