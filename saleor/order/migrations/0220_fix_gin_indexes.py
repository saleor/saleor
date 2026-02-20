"""Fix GIN indexes on unsupported field types.

Some older migrations created GIN indexes on field types that don't have a
default operator class for the GIN access method (e.g., varchar, integer, uuid).
On newer PostgreSQL versions these migrations fail with:
    ProgrammingError: data type <type> has no default operator class for
    access method "gin"

This migration replaces those indexes for existing databases:
- order_voucher_code_idx: GIN on CharField -> GIN with gin_trgm_ops
- order_user_email_user_id_idx: GIN on (EmailField, FK) -> BTree

See: https://github.com/saleor/saleor/issues/18341
"""

from django.db import migrations


# Use raw SQL with IF EXISTS to handle both fresh and existing databases.
# Fresh databases will already have the correct index from the fixed migration
# files, so the DROP will be a no-op.

class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("order", "0219_merge_20251212_0955"),
    ]

    operations = [
        # Fix order_voucher_code_idx: GIN without opclass -> GIN with gin_trgm_ops
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS order_voucher_code_idx;",
                (
                    "CREATE INDEX CONCURRENTLY order_voucher_code_idx "
                    "ON order_order USING gin (voucher_code gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS order_voucher_code_idx;",
                (
                    "CREATE INDEX CONCURRENTLY order_voucher_code_idx "
                    "ON order_order USING gin (voucher_code);"
                ),
            ],
        ),
        # Fix order_user_email_user_id_idx: GIN -> BTree
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS order_user_email_user_id_idx;",
                (
                    "CREATE INDEX CONCURRENTLY order_user_email_user_id_idx "
                    "ON order_order USING btree (user_email, user_id);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS order_user_email_user_id_idx;",
                (
                    "CREATE INDEX CONCURRENTLY order_user_email_user_id_idx "
                    "ON order_order USING gin (user_email, user_id);"
                ),
            ],
        ),
    ]
