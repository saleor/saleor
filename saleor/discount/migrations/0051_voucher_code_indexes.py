from django.db import migrations
from django.contrib.postgres.operations import AddIndexConcurrently
from django.contrib.postgres.indexes import BTreeIndex


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("discount", "0050_vouchercode"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="vouchercode",
            index=BTreeIndex(fields=["voucher"], name="vouchercode_voucher_idx"),
        )
    ]
