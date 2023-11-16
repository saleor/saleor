import django.contrib.postgres.indexes
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("checkout", "0061_checkout_last_transaction_modified_at"),
    ]

    atomic = False

    operations = [
        AddIndexConcurrently(
            model_name="checkout",
            index=django.contrib.postgres.indexes.BTreeIndex(
                fields=["last_transaction_modified_at"],
                name="chckt_last_tr_modified_at_idx",
            ),
        ),
    ]
