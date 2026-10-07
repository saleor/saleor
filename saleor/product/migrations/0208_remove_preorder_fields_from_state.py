from django.db import migrations, models


class Migration(migrations.Migration):
    """Remove the preorder fields from the Django state.

    The whole GraphQL surface of the preorder feature was removed in Saleor
    3.24.0, but the columns have to stay for one release so that pods running
    the previous version keep working during a rolling deploy.
    """

    dependencies = [("product", "0207_remove_producttype_is_digital_from_state")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AlterField(
                    model_name="productvariant",
                    name="is_preorder",
                    # Adds 'db_default=False' so INSERTs that no longer include
                    # the column don't violate its NOT NULL constraint.
                    field=models.BooleanField(default=False, db_default=False),
                ),
            ],
            # Will be dropped from the actual DB in Saleor v3.25.0
            state_operations=[
                migrations.RemoveField(
                    model_name="productvariant",
                    name="is_preorder",
                ),
                migrations.RemoveField(
                    model_name="productvariant",
                    name="preorder_end_date",
                ),
                migrations.RemoveField(
                    model_name="productvariant",
                    name="preorder_global_threshold",
                ),
                migrations.RemoveField(
                    model_name="productvariantchannellisting",
                    name="preorder_quantity_threshold",
                ),
            ],
        )
    ]
