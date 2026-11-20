from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("checkout", "0094_checkoutline_price_override_reason"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS
                    checkout_checkoutdelivery_external_shipping_method_id_55751488;
                    """,
                    reverse_sql=[
                        """
                        DROP INDEX CONCURRENTLY IF EXISTS
                        checkout_checkoutdelivery_external_shipping_method_id_55751488;
                        """,
                        """
                        CREATE INDEX CONCURRENTLY
                        checkout_checkoutdelivery_external_shipping_method_id_55751488
                        ON checkout_checkoutdelivery (external_shipping_method_id);
                        """,
                    ],
                ),
                migrations.RunSQL(
                    sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS
                    checkout_checkoutdeliver_external_shipping_method_55751488_like;
                    """,
                    reverse_sql=[
                        """
                        DROP INDEX CONCURRENTLY IF EXISTS
                        checkout_checkoutdeliver_external_shipping_method_55751488_like;
                        """,
                        """
                        CREATE INDEX CONCURRENTLY
                        checkout_checkoutdeliver_external_shipping_method_55751488_like
                        ON checkout_checkoutdelivery
                        (external_shipping_method_id varchar_pattern_ops);
                        """,
                    ],
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="checkoutdelivery",
                    name="external_shipping_method_id",
                    field=models.CharField(
                        blank=True, editable=False, max_length=1024, null=True
                    ),
                ),
            ],
        ),
    ]
