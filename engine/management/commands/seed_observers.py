# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../../LICENSE.md

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from access.consent import current_text_version
from access.models import Consent
from engine.document.blocks import BLOCK_TYPES, blocks_of
from engine.document.scoring import score
from engine.models import ObserverResponse, Publication, Response
from engine.seeding import observer_assessment, self_assessment

SEED_PASSWORD = "information."


# ✨ Written with AI assistance.
class Command(BaseCommand):
    help = "Create a fake participant with a self-assessment and self-result, and test observers, all marked as test data."

    def add_arguments(self, parser):
        parser.add_argument("--observers", type=int, default=3, help="How many test observers to create (default 3).")
        parser.add_argument("--password", default=SEED_PASSWORD, help="The fake participant's password.")

    def handle(self, *args, observers, password, **options):
        if observers < 1:
            raise CommandError("Seed at least one observer.")
        version = Publication.current_version()
        if version is None:
            raise CommandError("No pathway is published. Load one first with load_pathway.")
        document = version.document
        block_id = next((block["id"] for block in blocks_of(document) if BLOCK_TYPES[block["type"]].scored), None)
        if block_id is None:
            raise CommandError("The published pathway has no assessment block, so there is nothing to seed.")

        email = _unused_seed_email()
        assessment = self_assessment(document)
        with transaction.atomic():
            # ✨ The reserved example.com address marks the account as fake; everything under it is marked as test data.
            participant = get_user_model().objects.create_user(username=email, email=email, password=password)
            # ✨ Consent is recorded so the account can be signed in to for a demo without a stop at the consent page.
            Consent.objects.create(participant=participant, text_version=current_text_version())
            response = Response.objects.create(participant=participant, version=version, is_test_data=True)
            response.submit_sort(block_id, assessment, score(document, assessment))
            now = timezone.now()
            ObserverResponse.objects.bulk_create(
                ObserverResponse(
                    response=response,
                    assessment=observer_assessment(document, assessment, number),
                    submitted_at=now,
                    is_test_data=True,
                )
                for number in range(1, observers + 1)
            )

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {email} (password: {password}) with {observers} test observers.")
        )


def _unused_seed_email():
    users = get_user_model().objects
    number = 1
    while users.filter(email=_seed_email(number)).exists():
        number += 1
    return _seed_email(number)


def _seed_email(number):
    return f"seed-participant-{number}@example.com"
