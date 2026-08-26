from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    # CREATE INDEX CONCURRENTLY cannot run inside a transaction.
    atomic = False

    dependencies = [
        ("product", "0208_productmedia_owners"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="productmedia",
            index=models.Index(fields=["category"], name="productmedia_category_idx"),
        ),
        AddIndexConcurrently(
            model_name="productmedia",
            index=models.Index(
                fields=["collection"], name="productmedia_collection_idx"
            ),
        ),
        AddIndexConcurrently(
            model_name="productmedia",
            index=models.Index(fields=["page"], name="productmedia_page_idx"),
        ),
    ]
