from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0049_auto_20230322_0634"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE payment_transactionevent
                    DROP COLUMN name,
                    DROP COLUMN reference;
                    """,
                    reverse_sql="""
                    ALTER TABLE payment_transactionevent
                    ADD COLUMN name VARCHAR(512),
                    ADD COLUMN reference VARCHAR(512);
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE payment_transactionitem
                    DROP COLUMN reference,
                    DROP COLUMN type,
                    DROP COLUMN voided_value;
                    """,
                    reverse_sql="""
                    ALTER TABLE payment_transactionitem
                    ADD COLUMN reference VARCHAR(512),
                    ADD COLUMN type VARCHAR(512),
                    ADD COLUMN voided_value NUMERIC(12, 3);
                    """,
                ),
            ]
        )
    ]
