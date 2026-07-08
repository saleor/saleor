import django.contrib.postgres.indexes
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("giftcard", "0025_giftcard_assigned_to"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="giftcard",
            index=django.contrib.postgres.indexes.BTreeIndex(
                fields=["assigned_to"], name="giftcard_assigned_to_idx"
            ),
        ),
    ]
