from django.db import migrations, models


class Migration(migrations.Migration):
    # The unique index is built CONCURRENTLY so it does not hold an ACCESS
    # EXCLUSIVE lock on discount_promotion while it is created. CONCURRENTLY
    # cannot run inside a transaction, hence atomic = False and its own
    # migration, separate from the fast, atomic AddField in 0088.
    atomic = False

    dependencies = [
        ("discount", "0088_promotion_external_reference"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE UNIQUE INDEX CONCURRENTLY promotion_external_reference_key
                    ON discount_promotion ("external_reference");
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS promotion_external_reference_key;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE discount_promotion
                    ADD CONSTRAINT promotion_external_reference_key
                    UNIQUE USING INDEX promotion_external_reference_key;
                    """,
                    reverse_sql="""
                    ALTER TABLE discount_promotion DROP CONSTRAINT
                    IF EXISTS promotion_external_reference_key;
                    """,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="promotion",
                    name="external_reference",
                    field=models.CharField(
                        blank=True,
                        max_length=250,
                        null=True,
                        unique=True,
                        db_index=True,
                    ),
                ),
            ],
        ),
    ]
