from django.db import migrations, models


class Migration(migrations.Migration):
    # The unique index is built CONCURRENTLY so it does not hold an ACCESS
    # EXCLUSIVE lock on discount_voucher while it is created. CONCURRENTLY
    # cannot run inside a transaction, hence atomic = False and its own
    # migration, separate from the fast, atomic AddField in 0090.
    atomic = False

    dependencies = [
        ("discount", "0090_voucher_external_reference"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE UNIQUE INDEX CONCURRENTLY voucher_external_reference_key
                    ON discount_voucher ("external_reference");
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS voucher_external_reference_key;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE discount_voucher
                    ADD CONSTRAINT voucher_external_reference_key
                    UNIQUE USING INDEX voucher_external_reference_key;
                    """,
                    reverse_sql="""
                    ALTER TABLE discount_voucher DROP CONSTRAINT
                    IF EXISTS voucher_external_reference_key;
                    """,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="voucher",
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
