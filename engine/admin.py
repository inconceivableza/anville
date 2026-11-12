# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

import csv

from django.contrib import admin
from django.http import HttpResponse

from engine.models import SignUp, SignUpChoice

# ✨ What a spreadsheet reads as the start of a formula: a cell beginning with one is run, not shown.
_FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


def _as_cell(value):
    """✨ A value as a spreadsheet shows it, never runs it: one that would start a formula is begun with "'"."""
    text = str(value)
    return f"'{text}" if text.startswith(_FORMULA_STARTS) else text


class SignUpChoiceInline(admin.TabularInline):
    """✨ What a sign-up asked for (ticket 111, ADR 0027), each with when it was ticked and the wording's version, to
    read alone: choices come only through the homepage's form."""

    model = SignUpChoice
    fields = ("choice", "chosen_at", "wording_version")
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SignUp)
class SignUpAdmin(admin.ModelAdmin):
    """✨ The "Stay in touch" list (ticket 74, ADR 0023), newest first, for the operator to export and to delete anyone
    who asks to be removed. Addresses come only through the homepage's form, which records the wording they were left
    under, so none is added or changed here. Since ticket 111 (ADR 0027) each lists what it asked for, and the list
    filters by it, so each use's list can be exported on its own; one left before there were choices lists none."""

    list_display = ("email", "signed_up_at", "wording_version", "choices_listed")
    list_filter = ("choices__choice",)
    search_fields = ("email",)
    inlines = [SignUpChoiceInline]
    actions = ["export_as_csv"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("choices")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Choices")
    def choices_listed(self, sign_up):
        made = sign_up.choices_made()
        return ", ".join(label for choice, label in SignUpChoice.Choice.choices if choice in made) or None

    @admin.action(description="Export selected sign-ups as CSV", permissions=["view"])
    def export_as_csv(self, request, queryset):
        """✨ One row per sign-up, then a column for each choice holding when it was ticked, empty if it was not."""
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="stay-in-touch.csv"'
        writer = csv.writer(response)
        writer.writerow(["Email address", "Signed up at", "Wording version", *SignUpChoice.Choice.labels])
        for sign_up in queryset.prefetch_related("choices").order_by("signed_up_at"):
            made = sign_up.choices_made()
            writer.writerow(
                [
                    _as_cell(sign_up.email),
                    sign_up.signed_up_at.isoformat(),
                    sign_up.wording_version,
                    *(made[choice].chosen_at.isoformat() if choice in made else "" for choice in SignUpChoice.Choice),
                ]
            )
        return response
