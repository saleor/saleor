from django.db import migrations, models


class Migration(migrations.Migration):
    # The unique index is built CONCURRENTLY so it does not hold an ACCESS
    # EXCLUSIVE lock on webhook_webhook while it is created. CONCURRENTLY
    # cannot run inside a transaction, hence atomic = False and its own
    # migration, separate from the fast, atomic schema changes in 0013.
    atomic = False

    dependencies = [
        ("webhook", "0013_webhook_identifier_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE UNIQUE INDEX CONCURRENTLY unique_webhook_identifier
                    ON webhook_webhook ("app_id", "identifier");
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS unique_webhook_identifier;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE webhook_webhook
                    ADD CONSTRAINT unique_webhook_identifier
                    UNIQUE USING INDEX unique_webhook_identifier;
                    """,
                    reverse_sql="""
                    ALTER TABLE webhook_webhook DROP CONSTRAINT
                    IF EXISTS unique_webhook_identifier;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddConstraint(
                    model_name="webhook",
                    constraint=models.UniqueConstraint(
                        fields=("app", "identifier"),
                        name="unique_webhook_identifier",
                    ),
                ),
            ],
        ),
    ]
