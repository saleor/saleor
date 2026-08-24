from django.db import migrations, models


class Migration(migrations.Migration):
    """De-register the attribute presentation flags from the ORM.

    The columns stay in the database so pods still running the previous version keep
    working during a rolling deploy; they are made nullable so the new ORM, which no
    longer knows them, can insert rows.

    TODO: drop the columns in 3.25, once no process runs the version that still
    writes them.
    """

    dependencies = [
        ("attribute", "0058_alter_attribute_type"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="attribute",
            options={"ordering": ("slug",)},
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AlterField(
                    model_name="attribute",
                    name="filterable_in_storefront",
                    field=models.BooleanField(blank=True, null=True),
                ),
                migrations.AlterField(
                    model_name="attribute",
                    name="filterable_in_dashboard",
                    field=models.BooleanField(blank=True, null=True),
                ),
                migrations.AlterField(
                    model_name="attribute",
                    name="available_in_grid",
                    field=models.BooleanField(blank=True, null=True),
                ),
                migrations.AlterField(
                    model_name="attribute",
                    name="storefront_search_position",
                    field=models.IntegerField(blank=True, null=True),
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="attribute",
                    name="filterable_in_storefront",
                ),
                migrations.RemoveField(
                    model_name="attribute",
                    name="filterable_in_dashboard",
                ),
                migrations.RemoveField(
                    model_name="attribute",
                    name="available_in_grid",
                ),
                migrations.RemoveField(
                    model_name="attribute",
                    name="storefront_search_position",
                ),
            ],
        ),
    ]
