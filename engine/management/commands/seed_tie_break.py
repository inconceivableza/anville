# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../../LICENSE.md

from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.urls import reverse

from access.consent import current_text_version
from access.models import Account, Consent
from engine.document.blocks import BLOCK_TYPES, CHOICE, CONFIRMATION, SCALE_POINT, SCALE_POINTS, TEXT, blocks_of
from engine.hub import block_ids_fixed_on_completion, section_by_id, track_sections
from engine.models import Publication, Response
from engine.results import pair_page
from engine.tie_break_scenarios import (
    DEFAULT_ON,
    SCENARIOS,
    TAKES_ON,
    NoSuchVariant,
    ScenarioDoesNotHold,
    scenario_for,
    seeding,
)

SEED_PASSWORD = "information."
DISPLAY_NAME = "Robin"
SEEDED_TEXT = "A seeded answer, written for a demonstration."


# ✨ Written with AI assistance.
class Command(BaseCommand):
    help = (
        "Create a made-up participant on the published pathway whose stored sort puts them on one of the tie-break's "
        "ways through, ready for its pairs (or the results) on signing in, and print what to answer and what the "
        "results should then show. It writes made-up data, so it runs only with DEBUG on or ANVILLE_DEMO_NOTICE set "
        "(a demo system such as staging). It never touches an existing participant."
    )

    def add_arguments(self, parser):
        parser.add_argument("scenario", choices=list(SCENARIOS), help="Which way through the tie-break to seed.")
        parser.add_argument(
            "--on",
            help=(
                f"Only for {', '.join(TAKES_ON)}: the framework's id, apest or pep (default {DEFAULT_ON}). For "
                "separated and balanced it is the one framework tied, the other having a clear leader; for mixed it is "
                "the one that comes out Separated while the other is skipped."
            ),
        )
        parser.add_argument("--password", default=SEED_PASSWORD, help="The made-up participant's password.")

    def handle(self, *args, scenario, on, password, **options):
        try:
            summary = scenario_for(scenario, on).summary
        except NoSuchVariant as problem:
            raise CommandError(str(problem)) from problem
        if not (settings.DEBUG or settings.ANVILLE_DEMO_NOTICE):
            raise CommandError(
                "seed_tie_break makes a made-up participant, so it runs only with DEBUG on or ANVILLE_DEMO_NOTICE set."
            )
        version = Publication.current_version()
        if version is None:
            raise CommandError("No pathway is published. Load one first with load_pathway.")
        document = version.document
        block_id = next((block["id"] for block in blocks_of(document) if BLOCK_TYPES[block["type"]].scored), None)
        if block_id is None:
            raise CommandError("The published pathway has no assessment block, so there is nothing to seed.")
        try:
            seeded = seeding(document, scenario, on)
        except ScenarioDoesNotHold as problem:
            raise CommandError(f"The published pathway no longer gives this scenario: {problem}") from problem

        email = _unused_seed_email()
        with transaction.atomic():
            # ✨ The reserved example.com address marks the account as made up; its response is marked as test data.
            participant = get_user_model().objects.create_user(username=email, email=email, password=password)
            Account.objects.create(participant=participant, display_name=DISPLAY_NAME)
            Consent.objects.create(participant=participant, text_version=current_text_version())
            response = Response.objects.create(participant=participant, version=version, is_test_data=True)
            for section in _required_before(document, block_id):
                _complete(response, section)
            response.submit_sort(block_id, seeded.sort, seeded.scores)

        # ✨ Straight to the pairs once signed in; with none left, that page leads on to the results.
        next_page = urlencode({"next": reverse("tie_break", args=[block_id])}, safe="/")
        sign_in = f"{reverse('account_login')}?{next_page}"
        self.stdout.write(self.style.SUCCESS(f"Seeded {scenario}: {summary}"))
        self.stdout.write(f"Email: {email}\nPassword: {password}\nSign in at: {sign_in}\n")
        self.stdout.write("\n".join(_what_to_do(document, seeded)))


def _required_before(document, block_id):
    """✨ The sections that must be completed before the sort's section opens, those they require first."""
    section = next(section for section in track_sections(document) if block_id in _ids(section))
    ordered = []

    def add(section_id):
        required = section_by_id(document, section_id)
        for earlier in required.get("requires", []):
            add(earlier)
        if required not in ordered:
            ordered.append(required)

    for section_id in section.get("requires", []):
        add(section_id)
    return ordered


def _ids(section):
    return [block["id"] for block in section["blocks"]]


def _complete(response, section):
    """✨ Answer every block of a section that takes an answer, and complete it."""
    for number, block in enumerate(section["blocks"]):
        kind = BLOCK_TYPES[block["type"]].captures
        if kind is not None:
            response.save_answer(block["id"], _answer_of(kind, block, number))
    response.refresh_from_db()
    response.complete_section(section["id"], block_ids_fixed_on_completion(section, response.answers))


def _answer_of(kind, block, number):
    if kind is TEXT:
        return SEEDED_TEXT
    if kind is SCALE_POINT:
        return SCALE_POINTS[number % len(SCALE_POINTS)]
    if kind is CHOICE:
        return block["options"][number % len(block["options"])]["id"]
    if kind is CONFIRMATION:
        return True
    raise CommandError(f"seed_tie_break cannot answer a {kind.name} block before the sort.")


def _what_to_do(document, seeded):
    """✨ The lines saying which answer to give each pair, and what the results should then show."""
    lines = []
    if seeded.questions:
        lines.append(f"Answer the {len(seeded.questions)} pairs, in order:")
        for number, (pair, chosen) in enumerate(seeded.questions, start=1):
            # ✨ The pair screen's own words, so each line matches what the participant sees.
            shown = pair_page(document, [pair], 0)
            if chosen is None:
                answer = f"skip (“{shown['skip']}”)"
            else:
                answer = f"choose “{next(o['text'] for o in shown['options'] if o['construct'] == chosen)}”"
            lines.append(f"  {number}. {shown['framework']}: {answer}")
    else:
        lines.append("No pairs: the results show straight away.")
    lines.append("The results should then show:")
    for framework in seeded.shown["frameworks"]:
        leaders = ", ".join(f"{bar['label']} {bar['standing']}" for bar in framework["bars"][:2])
        lines.append(f"  {framework['heading']}: {leaders}")
        if framework["tie_break"]:
            lines.append(f"    {framework['tie_break']['heading']}: {framework['tie_break']['text']}")
    generalist = seeded.shown["generalist"]
    lines.append(f"  {generalist['heading']}: {generalist['text']}" if generalist else "  No generalist box.")
    return lines


def _unused_seed_email():
    users = get_user_model().objects
    number = 1
    while users.filter(email=_seed_email(number)).exists():
        number += 1
    return _seed_email(number)


def _seed_email(number):
    return f"seed-tie-break-{number}@example.com"
