import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        # ruleid: add-index-concurrently
        migrations.AddIndex(
            model_name="user",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_document"],
                name="user_search_gin",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
