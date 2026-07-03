from django.contrib.postgres.indexes import BTreeIndex
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations
from django.db.models import Q


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("order", "0223_add_reason_to_fulfillment_and_fulfillmentline"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="fulfillment",
            index=BTreeIndex(
                fields=["reason_reference"],
                name="fulfillment_reason_ref_idx",
                condition=Q(reason_reference__isnull=False),
            ),
        ),
    ]
