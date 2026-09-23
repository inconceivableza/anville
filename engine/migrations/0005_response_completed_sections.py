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
