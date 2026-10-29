from django.db import migrations, models


class Migration(migrations.Migration):
    """Remove `ProductType.is_digital` from the Django state.

    The whole GraphQL surface of the field was removed in Saleor 3.24.0, but
    the column has to stay for one release so that pods running the previous
    version keep working during a rolling deploy.
    """

    dependencies = [("product", "0206_drop_digitalcontent_tables")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AlterField(
                    model_name="producttype",
                    name="is_digital",
                    # Adds 'db_default=False' so INSERTs that no longer include
                    # the column don't violate its NOT NULL constraint.
                    field=models.BooleanField(default=False, db_default=False),
                ),
            ],
            # Will be dropped from the actual DB in Saleor v3.25.0
            state_operations=[
                migrations.RemoveField(
                    model_name="producttype",
                    name="is_digital",
                ),
            ],
        )
    ]
