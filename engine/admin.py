# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

import csv

from django.contrib import admin
from django.http import HttpResponse

from engine.models import SignUp

# ✨ What a spreadsheet reads as the start of a formula: a cell beginning with one is run, not shown.
_FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


def _as_cell(value):
    """✨ A value as a spreadsheet shows it, never runs it: one that would start a formula is begun with "'"."""
    text = str(value)
    return f"'{text}" if text.startswith(_FORMULA_STARTS) else text


@admin.register(SignUp)
class SignUpAdmin(admin.ModelAdmin):
    """✨ The "Stay in touch" list (ticket 74, ADR 0023), newest first, for the operator to export and to delete anyone
    who asks to be removed. Addresses come only through the homepage's form, which records the sentence they were left
    under, so none is added or changed here."""

    list_display = ("email", "signed_up_at", "wording_version")
    search_fields = ("email",)
    actions = ["export_as_csv"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.action(description="Export selected sign-ups as CSV", permissions=["view"])
    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="stay-in-touch.csv"'
        writer = csv.writer(response)
        writer.writerow(["Email address", "Signed up at", "Wording version"])
        for sign_up in queryset.order_by("signed_up_at"):
            writer.writerow([_as_cell(sign_up.email), sign_up.signed_up_at.isoformat(), sign_up.wording_version])
        return response
