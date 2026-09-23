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
from access.views import password_reset_unavailable
from engine.views import complete_section, hub, reopen_section, save_answer, section

urlpatterns = [
    path("admin/", admin.site.urls),
    # ✨ Ahead of allauth's own routes, so every password reset page is refused until email exists (ticket 28).
    re_path(r"^accounts/password/reset/", password_reset_unavailable),
    path("accounts/", include("allauth.urls")),
    path("answers/<slug:block_id>/", save_answer, name="save_answer"),
    path("sections/<slug:section_id>/", section, name="section"),
    path("sections/<slug:section_id>/complete/", complete_section, name="complete_section"),
    path("sections/<slug:section_id>/reopen/", reopen_section, name="reopen_section"),
    path("", hub, name="hub"),
]
