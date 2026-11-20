from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("checkout", "0095_drop_checkoutdelivery_external_shipping_method_id_indexes"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS
                    checkout_checkoutdelivery_built_in_shipping_method_id_5d9ed35a;
                    """,
                    reverse_sql=[
                        """
                        DROP INDEX CONCURRENTLY IF EXISTS
                        checkout_checkoutdelivery_built_in_shipping_method_id_5d9ed35a;
                        """,
                        """
                        CREATE INDEX CONCURRENTLY
                        checkout_checkoutdelivery_built_in_shipping_method_id_5d9ed35a
                        ON checkout_checkoutdelivery (built_in_shipping_method_id);
                        """,
                    ],
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="checkoutdelivery",
                    name="built_in_shipping_method_id",
                    field=models.IntegerField(blank=True, editable=False, null=True),
                ),
            ],
        ),
    ]
