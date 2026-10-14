# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0002_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="reason",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="account",
            name="path",
            field=models.CharField(
                blank=True,
                choices=[("online", "Guided online"), ("paper", "Paper workbook")],
                default="",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="account",
            name="remind",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="account",
            name="onboarding_completed",
            field=models.BooleanField(default=True),
        ),
    ]
