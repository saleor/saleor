import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("page", "0035_page_page_slug_btree_idx"),
        ("product", "0207_remove_producttype_is_digital_from_state"),
    ]

    # Adding a nullable column without a default is metadata-only on PostgreSQL 11+.
    # The supporting indexes are built concurrently in the next migration.
    operations = [
        migrations.AddField(
            model_name="productmedia",
            name="category",
            field=models.ForeignKey(
                blank=True,
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="media",
                to="product.category",
            ),
        ),
        migrations.AddField(
            model_name="productmedia",
            name="collection",
            field=models.ForeignKey(
                blank=True,
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="media",
                to="product.collection",
            ),
        ),
        migrations.AddField(
            model_name="productmedia",
            name="page",
            field=models.ForeignKey(
                blank=True,
                db_index=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="media",
                to="page.page",
            ),
        ),
    ]
