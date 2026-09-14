from django.db import migrations, models


class Migration(migrations.Migration):
    # The unique index is built CONCURRENTLY so it does not hold an ACCESS
    # EXCLUSIVE lock on product_collection while it is created. CONCURRENTLY
    # cannot run inside a transaction, hence atomic = False and its own
    # migration, separate from the fast, atomic AddField in 0208.
    atomic = False

    dependencies = [
        ("product", "0208_collection_external_reference"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE UNIQUE INDEX CONCURRENTLY collection_external_reference_key
                    ON product_collection ("external_reference");
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS collection_external_reference_key;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE product_collection
                    ADD CONSTRAINT collection_external_reference_key
                    UNIQUE USING INDEX collection_external_reference_key;
                    """,
                    reverse_sql="""
                    ALTER TABLE product_collection DROP CONSTRAINT
                    IF EXISTS collection_external_reference_key;
                    """,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="collection",
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
