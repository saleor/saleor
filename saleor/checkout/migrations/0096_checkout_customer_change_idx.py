import django.contrib.postgres.indexes
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("checkout", "0095_checkout_abandoned_notified_at"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="checkout",
            index=django.contrib.postgres.indexes.BTreeIndex(
                fields=["channel", "last_customer_change"],
                name="checkout_customer_change_idx",
            ),
        ),
    ]
