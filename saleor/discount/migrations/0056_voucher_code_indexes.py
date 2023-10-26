from django.contrib.postgres.indexes import BTreeIndex
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("discount", "0055_vouchercode"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="vouchercode",
            index=BTreeIndex(fields=["voucher"], name="vouchercode_voucher_idx"),
        )
    ]
