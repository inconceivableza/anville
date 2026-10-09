# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../../LICENSE.md

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from engine.document import content_hash, validate
from engine.models import PathwayVersion, Publication


# ✨ Written with AI assistance.
class Command(BaseCommand):
    help = "Validate a pathway document file, load it as an immutable pathway version and publish it."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the pathway document (JSON).")

    def handle(self, *args, path, **options):
        try:
            document = json.loads(Path(path).read_text(encoding="utf-8"))
        except OSError as error:
            raise CommandError(f"Cannot read {path}: {error.strerror}.")
        except json.JSONDecodeError as error:
            raise CommandError(f"{path} is not valid JSON (line {error.lineno}, column {error.colno}: {error.msg}).")

        problems = validate(document)
        if problems:
            listed = "\n".join(f"  {problem.path or '/'}: {problem.message}" for problem in problems)
            raise CommandError(f"{path} was not loaded. Fix these problems first:\n{listed}")

        with transaction.atomic():
            version, created = PathwayVersion.objects.get_or_create(
                content_hash=content_hash(document), defaults={"document": document}
            )
            if Publication.current_version() == version:
                self.stdout.write(f"No change: this content is already pathway version {version.pk}, and it is published.")
                return
            Publication.objects.create(version=version)

        verb = "Loaded" if created else "Republished"
        self.stdout.write(self.style.SUCCESS(f"{verb} pathway version {version.pk} ({version.content_hash[:12]})."))
