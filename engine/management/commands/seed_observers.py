import hashlib

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from access.consent import current_text_version
from access.models import Consent
from engine.document.blocks import BLOCK_TYPES, blocks_of
from engine.document.scoring import score
from engine.models import ObserverResponse, Publication, Response

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

        buckets = document["instrument"]["buckets"]
        email = _unused_seed_email()
        self_assessment = _self_assessment(document["instrument"]["items"], buckets)
        with transaction.atomic():
            # ✨ The reserved example.com address marks the account as fake; everything under it is marked as test data.
            participant = get_user_model().objects.create_user(username=email, email=email, password=password)
            # ✨ Consent is recorded so the account can be signed in to for a demo without a stop at the consent page.
            Consent.objects.create(participant=participant, text_version=current_text_version())
            response = Response.objects.create(participant=participant, version=version, is_test_data=True)
            response.submit_sort(block_id, self_assessment, score(document, self_assessment))
            now = timezone.now()
            ObserverResponse.objects.bulk_create(
                ObserverResponse(
                    response=response,
                    assessment=_observer_assessment(self_assessment, buckets, number),
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


def _self_assessment(items, buckets):
    """✨ Every item placed in a bucket picked by a hash of the item, at the bucket's seed value, as if its slider were
    left untouched. The same on every run, and uneven enough that the self-result is not flat."""
    return {item["id"]: _placement(buckets, _stable_number(item["id"], "self") % len(buckets)) for item in items}


def _observer_assessment(self_assessment, buckets, number):
    """✨ The self-assessment with each item moved by at most one bucket either way, as someone who knows the
    participant well might see them: close enough to agree mostly, different enough to show gaps."""
    positions = {bucket["id"]: position for position, bucket in enumerate(buckets)}
    assessment = {}
    for item_id, placement in self_assessment.items():
        moved = positions[placement["bucket"]] + _stable_number(item_id, f"observer-{number}") % 3 - 1
        assessment[item_id] = _placement(buckets, min(max(moved, 0), len(buckets) - 1))
    return assessment


def _placement(buckets, position):
    return {"bucket": buckets[position]["id"], "value": buckets[position]["seed"]}


def _stable_number(*parts):
    # ✨ Python's hash() of a string changes between runs, so a digest keeps the seeded values the same every time.
    return int(hashlib.sha256("/".join(parts).encode()).hexdigest(), 16)
