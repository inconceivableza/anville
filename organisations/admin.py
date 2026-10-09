from django.contrib import admin

from organisations.models import Group, Membership, Organisation, Permission


class PermissionInline(admin.TabularInline):
    """✨ On the organisation's form and the group's, so an organisation and its first admin are made in one go. The
    form it sits on supplies the scope."""

    model = Permission
    fields = ["holder", "capability"]
    autocomplete_fields = ["holder"]
    extra = 1


class MembershipInline(admin.TabularInline):
    model = Membership
    fields = ["participant", "joined_at"]
    readonly_fields = ["joined_at"]
    autocomplete_fields = ["participant"]
    extra = 0


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    inlines = [PermissionInline]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "organisation", "type"]
    list_filter = ["type"]
    search_fields = ["name", "organisation__name"]
    readonly_fields = ["join_token"]
    inlines = [PermissionInline, MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["participant", "group", "joined_at"]
    autocomplete_fields = ["participant", "group"]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["holder", "capability", "organisation", "group"]
    autocomplete_fields = ["holder", "organisation", "group"]
