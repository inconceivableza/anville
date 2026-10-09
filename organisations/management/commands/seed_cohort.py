from typing import NamedTuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.urls import reverse

from access.consent import current_text_version, withdraw
from access.models import Account, Consent
from engine.document.blocks import BLOCK_TYPES, CHOICE, CONFIRMATION, CONTACTS, SCALE_POINT, SCALE_POINTS, SORT, TEXT
from engine.document.observers import link_lifetime, minimum_observers
from engine.document.scoring import score
from engine.hub import block_ids_fixed_on_completion, track_sections
from engine.models import Contact, Invitation, ObserverResponse, Publication, Response
from engine.seeding import observer_assessment, self_assessment, stable_number
from organisations.models import Group, Membership, Organisation, Permission

ORGANISATION = "Example Church"
COHORT = "Autumn cohort"
ADMIN_EMAIL = "seed-cohort-admin@example.com"
SEED_PASSWORD = "information."


class Stage(NamedTuple):
    """✨ How far a seeded member has got through the track: `completed` of its sections (a section's parts with it),
    or every one when `finished`."""

    completed: int = 0
    finished: bool = False

    @property
    def started(self):
        """✨ A member who has not started has no response at all."""
        return self.finished or self.completed > 0

    def sections_completed(self, whole):
        """✨ The sections of `whole` this stage has completed. A part-way count is kept short of the whole track,
        however few sections it has."""
        return whole if self.finished else whole[: min(self.completed, len(whole) - 1)]


NOT_STARTED = Stage()
FINISHED = Stage(finished=True)


def part_way(completed):
    return Stage(completed=completed)


# ✨ Each member's first name, as given at sign-up, and how far they have got.
MEMBERS = [
    ("Ada", NOT_STARTED),
    ("Ben", NOT_STARTED),
    ("Cara", NOT_STARTED),
    ("Dan", part_way(1)),
    ("Esi", part_way(1)),
    ("Femi", part_way(2)),
    ("Grace", part_way(2)),
    ("Hugo", part_way(3)),
    ("Ines", FINISHED),
    ("Jon", FINISHED),
    ("Kemi", FINISHED),
    ("Liam", FINISHED),
]
# ✨ The one member who has withdrawn consent: part-way, so their progress would otherwise be worth showing.
WITHDRAWN = "Femi"
SEEDED_TEXT = "A seeded answer, written for a demonstration."


# ✨ Written with AI assistance.
class Command(BaseCommand):
    help = "Create Example Church with an Autumn cohort of twelve fake members and an admin, all marked as test data."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_cohort makes fake accounts, so it runs only with DEBUG on.")
        version = Publication.current_version()
        if version is None:
            raise CommandError("No pathway is published. Load one first with load_pathway.")
        if Organisation.objects.filter(name=ORGANISATION).exists():
            self.stdout.write(f"{ORGANISATION} already exists, so nothing was added.")
            return

        with transaction.atomic():
            church = Organisation.objects.create(name=ORGANISATION)
            cohort = Group.objects.create(organisation=church, name=COHORT, type=Group.Type.COHORT)
            admin = _account(ADMIN_EMAIL, "Admin")
            Permission.objects.create(holder=admin, capability=Permission.Capability.MANAGE, organisation=church)
            for number, (name, stage) in enumerate(MEMBERS, start=1):
                member = _account(f"seed-cohort-member-{number}@example.com", name)
                Membership.objects.create(participant=member, group=cohort)
                if stage.started:
                    _work_through(member, version, stage)
                if name == WITHDRAWN:
                    withdraw(member)

        join_link = reverse("join", args=[cohort.join_token])
        self.stdout.write(
            self.style.SUCCESS(f"Seeded {ORGANISATION} with an {COHORT} of {len(MEMBERS)} members.")
            + f"\nAdmin: {ADMIN_EMAIL}\nPassword: {SEED_PASSWORD}\nJoin link: {join_link}"
        )


def _account(email, display_name):
    """✨ A fake account at a reserved example.com address, with consent recorded so it can be signed in to for a demo
    without a stop at the consent page."""
    account = get_user_model().objects.create_user(username=email, email=email, password=SEED_PASSWORD)
    Account.objects.create(participant=account, display_name=display_name)
    Consent.objects.create(participant=account, text_version=current_text_version())
    return account


def _work_through(member, version, stage):
    """✨ A test-data response that has answered and completed the sections of the track `stage` has reached, and
    whose observers have answered through their own links, as real observers do."""
    document = version.document
    sections = track_sections(document)
    whole = [section for section in sections if "part_of" not in section]
    response = Response.objects.create(participant=member, version=version, is_test_data=True)
    tokens = []
    for section in stage.sections_completed(whole):
        for answering in [section, *(part for part in sections if part.get("part_of") == section["id"])]:
            tokens += _answer(response, document, answering, member.email)
        response.refresh_from_db()
        response.complete_section(section["id"], block_ids_fixed_on_completion(section, response.answers))
    if "instrument" in document:
        assessment = self_assessment(document, member.email)
        for number, token in enumerate(tokens, start=1):
            secret = Invitation.claim(token)
            ObserverResponse.send(
                response, secret, observer_assessment(document, assessment, number), is_test_data=True
            )


def _answer(response, document, section, seed):
    """✨ Answer every block of a section that takes an answer, and return the links issued to the people it names."""
    tokens = []
    for block in section["blocks"]:
        kind = BLOCK_TYPES[block["type"]].captures
        if kind is SORT:
            assessment = self_assessment(document, seed)
            response.submit_sort(block["id"], assessment, score(document, assessment))
            response.visit_comparison(block["id"])
        elif kind is CONTACTS:
            people = [
                {"name": f"Observer {number}", "email": f"{seed.partition('@')[0]}-observer-{number}@example.com"}
                for number in range(1, minimum_observers(document) + 1)
            ]
            for contact in response.replace_contacts(block["id"], people, Contact.Role.CONTACT):
                tokens.append(Invitation.issue(contact, link_lifetime(document)))
        elif kind is not None:
            response.save_answer(block["id"], _answer_of(kind, block, stable_number(seed, block["id"])))
    return tokens


def _answer_of(kind, block, number):
    if kind is TEXT:
        return SEEDED_TEXT
    if kind is SCALE_POINT:
        return SCALE_POINTS[number % len(SCALE_POINTS)]
    if kind is CHOICE:
        return block["options"][number % len(block["options"])]["id"]
    if kind is CONFIRMATION:
        return True
    raise CommandError(f"seed_cohort cannot answer a {kind.name} block yet.")
