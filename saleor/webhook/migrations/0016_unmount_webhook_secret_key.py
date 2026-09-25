from django.db import migrations


class Migration(migrations.Migration):
    """Drop `Webhook.secret_key` from the model state, keeping the column.

    The field was removed from the GraphQL API in 3.24 and webhook payloads are
    signed with a verifiable JWS instead. The column is left in place so the
    release can be rolled back; it is dropped in a later migration.
    """

    dependencies = [
        ("webhook", "0015_drop_export_completed_events"),
    ]

    state_operations = [
        migrations.RemoveField(
            model_name="webhook",
            name="secret_key",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
