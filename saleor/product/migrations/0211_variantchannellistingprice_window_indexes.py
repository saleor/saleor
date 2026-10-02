import django.contrib.postgres.indexes
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("product", "0210_variantchannellistingprice_is_applied"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="variantchannellistingprice",
            index=django.contrib.postgres.indexes.BTreeIndex(
                condition=models.Q(
                    ("is_applied", False),
                    models.Q(
                        ("valid_from__isnull", False),
                        ("valid_to__isnull", False),
                        _connector="OR",
                    ),
                ),
                fields=["valid_to"],
                name="listingprice_to_apply_idx",
            ),
        ),
        AddIndexConcurrently(
            model_name="variantchannellistingprice",
            index=django.contrib.postgres.indexes.BTreeIndex(
                condition=models.Q(("is_applied", True)),
                fields=["valid_to"],
                name="listingprice_to_withdraw_idx",
            ),
        ),
    ]
