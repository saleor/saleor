from django.contrib.postgres.indexes import BTreeIndex
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations
from django.db.models import Q


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("order", "0225_fulfillmentline_reason_ref_idx"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="ordergrantedrefundline",
            index=BTreeIndex(
                fields=["reason_reference"],
                name="grantedrefundline_reason_ref_idx",
                condition=Q(reason_reference__isnull=False),
            ),
        ),
    ]
