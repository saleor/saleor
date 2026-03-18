from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("site", "0045_merge_20260223_0944"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AlterField(
                    model_name="sitesettings",
                    name="automatic_fulfillment_digital_products",
                    # Adds 'db_default=False' for backward-compatibility
                    field=models.BooleanField(default=False, db_default=False),
                ),
                # TODO:
                # migrations.RunPython(
                #     migrations.RunPython.noop,
                #     todo,
                # ),
            ],
            # Will be dropped from the actual DB in Saleor v3.24.0
            state_operations=[
                migrations.RemoveField(
                    model_name="sitesettings",
                    name="automatic_fulfillment_digital_products",
                ),
                migrations.RemoveField(
                    model_name="sitesettings",
                    name="default_digital_max_downloads",
                ),
                migrations.RemoveField(
                    model_name="sitesettings",
                    name="default_digital_url_valid_days",
                ),
            ],
        )
    ]
