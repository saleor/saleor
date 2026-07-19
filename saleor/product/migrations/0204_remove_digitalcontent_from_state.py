from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0203_mark_products_search_index_as_dirty"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AlterField(
                    model_name="digitalcontent",
                    name="product_variant",
                    field=models.OneToOneField(
                        "product.ProductVariant",
                        related_name="digital_content",
                        on_delete=models.CASCADE,
                        # Added 'db_constraint=False' - drops the FK
                        # from the DB which prevents errors when deleting in cascade
                        # due to Django no longer knowing about the existence of the
                        # DigitalContent table
                        db_constraint=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="digitalcontenturl",
                    name="line",
                    field=models.OneToOneField(
                        "order.OrderLine",
                        related_name="digital_content_url",
                        blank=True,
                        null=True,
                        on_delete=models.CASCADE,
                        # Added 'db_constraint=False' - drops the FK
                        # from the DB which prevents errors when deleting in cascade
                        # due to Django no longer knowing about the existence of the
                        # DigitalContentUrl table
                        db_constraint=False,
                    ),
                ),
            ],
            # Will be dropped from the actual DB in Saleor v3.24.0
            state_operations=[
                migrations.RemoveField(
                    model_name="digitalcontenturl",
                    name="content",
                ),
                migrations.RemoveField(
                    model_name="digitalcontenturl",
                    name="line",
                ),
                migrations.DeleteModel(
                    name="DigitalContent",
                ),
                migrations.DeleteModel(
                    name="DigitalContentUrl",
                ),
            ],
        )
    ]
