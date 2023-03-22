from django.contrib.postgres.functions import RandomUUID
from django.db import migrations


# This data migration is handled in the 0043 with celery tasks.
# 0043 is due to zero-downtime policy, this migration is to ensure
# that we can change token to non-nullable.
def populate_transaction_item_token(apps, schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")

    transactions = TransactionItem.objects.filter(token__isnull=True)
    for transaction in transactions:
        transaction.token = RandomUUID()

    transactions.bulk_update(transactions, ["token"])


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0047_merge_20230321_1456"),
    ]

    operations = [
        migrations.RunPython(
            populate_transaction_item_token, migrations.RunPython.noop
        ),
    ]
