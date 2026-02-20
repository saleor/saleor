"""Fix GIN indexes on payment models.

Some older migrations created GIN indexes on field types that don't support
the GIN access method without an operator class:
- Payment: GIN on (order_id, is_active, charge_status) -> BTree
- Transaction: GIN on token (CharField) -> GIN with gin_trgm_ops

See: https://github.com/saleor/saleor/issues/18341
"""

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("payment", "0068_merge_20260206_1216"),
    ]

    operations = [
        # Fix payment_pay_order_i_f22aa2_gin: GIN -> BTree
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS payment_pay_order_i_f22aa2_gin;",
                (
                    "CREATE INDEX CONCURRENTLY payment_pay_order_i_f22aa2_gin "
                    "ON payment_payment "
                    "USING btree (order_id, is_active, charge_status);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS payment_pay_order_i_f22aa2_gin;",
                (
                    "CREATE INDEX CONCURRENTLY payment_pay_order_i_f22aa2_gin "
                    "ON payment_payment "
                    "USING gin (order_id, is_active, charge_status);"
                ),
            ],
        ),
        # Fix token_idx: GIN without opclass -> GIN with gin_trgm_ops
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS token_idx;",
                (
                    "CREATE INDEX CONCURRENTLY token_idx "
                    "ON payment_transaction "
                    "USING gin (token gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS token_idx;",
                (
                    "CREATE INDEX CONCURRENTLY token_idx "
                    "ON payment_transaction "
                    "USING gin (token);"
                ),
            ],
        ),
    ]
