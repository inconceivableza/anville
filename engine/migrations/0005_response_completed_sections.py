# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('engine', '0004_response'),
    ]

    operations = [
        migrations.AddField(
            model_name='response',
            name='completed_sections',
            field=models.JSONField(default=dict),
        ),
    ]
