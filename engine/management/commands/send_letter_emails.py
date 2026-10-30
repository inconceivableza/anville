# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../../LICENSE.md

from django.core.management.base import BaseCommand

from engine.letters import send_ready_letters


# ✨ Written with AI assistance.
class Command(BaseCommand):
    help = (
        "Email each participant whose sealed letter has reached its date that it is ready (ticket 104). Run once a "
        "day: the chart's CronJob runs it in a deployed environment, when switched on, and locally it is run by hand."
    )

    def handle(self, *args, **options):
        sent = send_ready_letters()
        self.stdout.write(f"Sent {sent} letter email{'' if sent == 1 else 's'}.")
