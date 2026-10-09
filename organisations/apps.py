from django.apps import AppConfig


class OrganisationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organisations'
    verbose_name = "Organisations and groups"  # ✨ apart from Django's own "Groups" in the admin
