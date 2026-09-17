from django.db import migrations, models


class Migration(migrations.Migration):
    """De-register the attribute presentation flags from the ORM.

    The columns stay in the database so pods still running the previous version keep
    working during a rolling deploy. They keep their NOT NULL constraint and gain a
    `db_default`, so the new ORM, which no longer knows them, can insert rows without
    the old pods ever reading a NULL through the deprecated GraphQL fields, which are
    still non-nullable there.

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
                    field=models.BooleanField(
                        blank=True, default=False, db_default=False
                    ),
                ),
                migrations.AlterField(
                    model_name="attribute",
                    name="filterable_in_dashboard",
                    field=models.BooleanField(
                        blank=True, default=False, db_default=False
                    ),
                ),
                migrations.AlterField(
                    model_name="attribute",
                    name="available_in_grid",
                    field=models.BooleanField(
                        blank=True, default=False, db_default=False
                    ),
                ),
                migrations.AlterField(
                    model_name="attribute",
                    name="storefront_search_position",
                    field=models.IntegerField(blank=True, default=0, db_default=0),
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
