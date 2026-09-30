from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    # CREATE INDEX CONCURRENTLY cannot run inside a transaction.
    atomic = False

    dependencies = [
        ("thumbnail", "0004_thumbnail_media_owners"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="thumbnail",
            index=models.Index(
                fields=["category_media"], name="thumbnail_categorymedia_idx"
            ),
        ),
        AddIndexConcurrently(
            model_name="thumbnail",
            index=models.Index(
                fields=["collection_media"], name="thumbnail_collectionmedia_idx"
            ),
        ),
        AddIndexConcurrently(
            model_name="thumbnail",
            index=models.Index(fields=["page_media"], name="thumbnail_pagemedia_idx"),
        ),
    ]
