from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from access.consent import current_text_version
from access.models import Account, Consent
from engine.models import Publication
from organisations.models import Group, Membership, Organisation, Permission

ORGANISATION = "Example Church"
COHORT = "Autumn cohort"
ADMIN_EMAIL = "seed-cohort-admin@example.com"
SEED_PASSWORD = "information."
# ✨ Fictional first names, as members give them at sign-up.
MEMBERS = ["Ada", "Ben", "Cara", "Dan", "Esi", "Femi", "Grace", "Hugo", "Ines", "Jon", "Kemi", "Liam"]


# ✨ Written with AI assistance.
class Command(BaseCommand):
    help = "Create Example Church with an Autumn cohort of twelve fake members and an admin, all marked as test data."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_cohort makes fake accounts, so it runs only with DEBUG on.")
        version = Publication.current_version()
        if version is None:
            raise CommandError("No pathway is published. Load one first with load_pathway.")

        with transaction.atomic():
            church = Organisation.objects.create(name=ORGANISATION)
            cohort = Group.objects.create(organisation=church, name=COHORT, type=Group.Type.COHORT)
            admin = _account(ADMIN_EMAIL, "Admin")
            Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, organisation=church)
            for number, name in enumerate(MEMBERS, start=1):
                member = _account(f"seed-cohort-member-{number}@example.com", name)
                Membership.objects.create(participant=member, group=cohort)

        # ✨ The join route belongs to joining by link (ticket A2), so the path is written out rather than reversed.
        self.stdout.write(
            self.style.SUCCESS(f"Seeded {ORGANISATION} with an {COHORT} of {len(MEMBERS)} members.")
            + f"\nAdmin: {ADMIN_EMAIL}\nPassword: {SEED_PASSWORD}\nJoin link: /join/{cohort.join_token}/"
        )


def _account(email, display_name):
    """✨ A fake account at a reserved example.com address, with consent recorded so it can be signed in to for a demo
    without a stop at the consent page."""
    account = get_user_model().objects.create_user(username=email, email=email, password=SEED_PASSWORD)
    Account.objects.create(participant=account, display_name=display_name)
    Consent.objects.create(participant=account, text_version=current_text_version())
    return account
