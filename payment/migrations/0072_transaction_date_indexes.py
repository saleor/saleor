import django.contrib.postgres.indexes
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ("payment", "0071_remove_legacy_adyen_plugin_fields_from_orm"),
    ]
    operations = [
        AddIndexConcurrently(
            model_name="transactionitem",
            index=django.contrib.postgres.indexes.BTreeIndex(
                fields=["created_at"], name="transaction_created_at_idx"
            ),
        ),
        AddIndexConcurrently(
            model_name="transactionitem",
            index=django.contrib.postgres.indexes.BTreeIndex(
                fields=["modified_at"], name="transaction_modified_at_idx"
            ),
        ),
        AddIndexConcurrently(
            model_name="transactionevent",
            index=django.contrib.postgres.indexes.BTreeIndex(
                fields=["created_at"], name="transactionevent_created_at_idx"
            ),
        ),
        AddIndexConcurrently(
            model_name="transactionevent",
            index=django.contrib.postgres.indexes.BTreeIndex(
                fields=["type"], name="transactionevent_type_idx"
            ),
        ),
    ]
