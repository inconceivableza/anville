# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../../LICENSE.md

from django.core.management.base import BaseCommand

from engine.reminders import send_due_reminders


# ✨ Written with AI assistance.
class Command(BaseCommand):
    help = (
        "Remind each observer who has not sent, once a week while their link works (ticket 43a). Run once a day: the "
        "chart's CronJob runs it in a deployed environment, and locally it is run by hand."
    )

    def handle(self, *args, **options):
        sent = send_due_reminders()
        self.stdout.write(f"Sent {sent} reminder{'' if sent == 1 else 's'}.")
