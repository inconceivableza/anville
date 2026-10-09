from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from engine.models import Publication


# ✨ Written with AI assistance.
class Command(BaseCommand):
    help = "Create Example Church with an Autumn cohort of twelve fake members and an admin, all marked as test data."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_cohort makes fake accounts, so it runs only with DEBUG on.")
        version = Publication.current_version()
        if version is None:
            raise CommandError("No pathway is published. Load one first with load_pathway.")
