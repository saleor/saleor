"""Fix GIN indexes on discount models.

Several older migrations created GIN indexes on CharField fields without
specifying the gin_trgm_ops operator class. On newer PostgreSQL versions
these fail with:
    ProgrammingError: data type character varying has no default operator
    class for access method "gin"

This migration recreates those indexes with the correct operator class.

See: https://github.com/saleor/saleor/issues/18341
"""

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("discount", "0087_merge_20250630_1332"),
    ]

    operations = [
        # Fix discount_or_name_d16858_gin on OrderDiscount (name, translated_name)
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS discount_or_name_d16858_gin;",
                (
                    "CREATE INDEX CONCURRENTLY discount_or_name_d16858_gin "
                    "ON discount_orderdiscount "
                    "USING gin (name gin_trgm_ops, translated_name gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS discount_or_name_d16858_gin;",
                (
                    "CREATE INDEX CONCURRENTLY discount_or_name_d16858_gin "
                    "ON discount_orderdiscount "
                    "USING gin (name, translated_name);"
                ),
            ],
        ),
        # Fix orderdiscount_voucher_code_idx
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS orderdiscount_voucher_code_idx;",
                (
                    "CREATE INDEX CONCURRENTLY orderdiscount_voucher_code_idx "
                    "ON discount_orderdiscount "
                    "USING gin (voucher_code gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS orderdiscount_voucher_code_idx;",
                (
                    "CREATE INDEX CONCURRENTLY orderdiscount_voucher_code_idx "
                    "ON discount_orderdiscount "
                    "USING gin (voucher_code);"
                ),
            ],
        ),
        # Fix orderlinedisc_voucher_code_idx
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS orderlinedisc_voucher_code_idx;",
                (
                    "CREATE INDEX CONCURRENTLY orderlinedisc_voucher_code_idx "
                    "ON discount_orderlinediscount "
                    "USING gin (voucher_code gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS orderlinedisc_voucher_code_idx;",
                (
                    "CREATE INDEX CONCURRENTLY orderlinedisc_voucher_code_idx "
                    "ON discount_orderlinediscount "
                    "USING gin (voucher_code);"
                ),
            ],
        ),
        # Fix discount_ch_name_64e096_gin on CheckoutDiscount (name, translated_name)
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS discount_ch_name_64e096_gin;",
                (
                    "CREATE INDEX CONCURRENTLY discount_ch_name_64e096_gin "
                    "ON discount_checkoutdiscount "
                    "USING gin (name gin_trgm_ops, translated_name gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS discount_ch_name_64e096_gin;",
                (
                    "CREATE INDEX CONCURRENTLY discount_ch_name_64e096_gin "
                    "ON discount_checkoutdiscount "
                    "USING gin (name, translated_name);"
                ),
            ],
        ),
        # Fix checkoutdiscount_voucher_idx
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS checkoutdiscount_voucher_idx;",
                (
                    "CREATE INDEX CONCURRENTLY checkoutdiscount_voucher_idx "
                    "ON discount_checkoutdiscount "
                    "USING gin (voucher_code gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS checkoutdiscount_voucher_idx;",
                (
                    "CREATE INDEX CONCURRENTLY checkoutdiscount_voucher_idx "
                    "ON discount_checkoutdiscount "
                    "USING gin (voucher_code);"
                ),
            ],
        ),
        # Fix checklinedisc_voucher_code_idx
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS checklinedisc_voucher_code_idx;",
                (
                    "CREATE INDEX CONCURRENTLY checklinedisc_voucher_code_idx "
                    "ON discount_checkoutlinediscount "
                    "USING gin (voucher_code gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS checklinedisc_voucher_code_idx;",
                (
                    "CREATE INDEX CONCURRENTLY checklinedisc_voucher_code_idx "
                    "ON discount_checkoutlinediscount "
                    "USING gin (voucher_code);"
                ),
            ],
        ),
    ]
