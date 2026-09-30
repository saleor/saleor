import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("webhook", "0015_drop_export_completed_events"),
    ]

    operations = [
        migrations.AddField(
            model_name="webhook",
            name="filterable_media_owner_types",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=32),
                blank=True,
                default=list,
                size=4,
            ),
        ),
        # Keep a DB-level default so pods still running the previous release can
        # insert webhooks without knowing about this column.
        migrations.RunSQL(
            """
            ALTER TABLE webhook_webhook
            ALTER COLUMN filterable_media_owner_types
            SET DEFAULT array[]::varchar[];
            """,
            migrations.RunSQL.noop,
        ),
    ]
