from django.contrib.postgres.indexes import BTreeIndex
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("discount", "0045_promotions"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="checkoutlinediscount",
            index=BTreeIndex(
                fields=["promotion_rule"], name="checklinedisc_promotion_rule_idx"
            ),
        ),
        AddIndexConcurrently(
            model_name="orderdiscount",
            index=BTreeIndex(
                fields=["promotion_rule"], name="orderdiscount_promotion_rule_idx"
            ),
        ),
        AddIndexConcurrently(
            model_name="orderlinediscount",
            index=BTreeIndex(
                fields=["promotion_rule"], name="orderlinedisc_promotion_rule_idx"
            ),
        ),
    ]
