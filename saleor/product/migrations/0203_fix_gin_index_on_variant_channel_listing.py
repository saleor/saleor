"""Fix GIN index on ProductVariantChannelListing.

The migration 0187 created a GIN index on (price_amount, channel_id) which
are DecimalField and IntegerField respectively. These field types don't have
a default operator class for the GIN access method.

This migration replaces the GIN index with a BTree index for existing databases.

See: https://github.com/saleor/saleor/issues/18341
"""

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("product", "0202_category_product_category_tree_id_lf1e1"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS product_pro_price_a_fb6bd3_gin;",
                (
                    "CREATE INDEX CONCURRENTLY product_pro_price_a_fb6bd3_gin "
                    "ON product_productvariantchannellisting "
                    "USING btree (price_amount, channel_id);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS product_pro_price_a_fb6bd3_gin;",
                (
                    "CREATE INDEX CONCURRENTLY product_pro_price_a_fb6bd3_gin "
                    "ON product_productvariantchannellisting "
                    "USING gin (price_amount, channel_id);"
                ),
            ],
        ),
    ]
