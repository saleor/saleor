from django.db import migrations, models


class Migration(migrations.Migration):
    # The unique index is built CONCURRENTLY so it does not hold an ACCESS
    # EXCLUSIVE lock on app_appextension while it is created. CONCURRENTLY
    # cannot run inside a transaction, hence atomic = False and its own
    # migration, separate from the fast, atomic schema changes in 0039.
    atomic = False

    dependencies = [
        ("app", "0039_appextension_identifier_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE UNIQUE INDEX CONCURRENTLY unique_app_extension_identifier
                    ON app_appextension ("app_id", "identifier");
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS unique_app_extension_identifier;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE app_appextension
                    ADD CONSTRAINT unique_app_extension_identifier
                    UNIQUE USING INDEX unique_app_extension_identifier;
                    """,
                    reverse_sql="""
                    ALTER TABLE app_appextension DROP CONSTRAINT
                    IF EXISTS unique_app_extension_identifier;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddConstraint(
                    model_name="appextension",
                    constraint=models.UniqueConstraint(
                        fields=("app", "identifier"),
                        name="unique_app_extension_identifier",
                    ),
                ),
            ],
        ),
    ]
