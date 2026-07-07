import django.contrib.postgres.indexes
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("account", "0101_usercustomertag_indexes"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="customertag",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["name"],
                name="customer_tag_name_gin",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
