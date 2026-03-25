"""Fix GIN index on User model.

The migration 0050 created a GIN index on (email, first_name, last_name)
CharField fields without specifying the gin_trgm_ops operator class. On newer
PostgreSQL versions this fails with:
    ProgrammingError: data type character varying has no default operator
    class for access method "gin"

This migration recreates the index with the correct operator class.

See: https://github.com/saleor/saleor/issues/18341
"""

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("account", "0098_update_user_search_vector"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS account_use_email_d707ff_gin;",
                (
                    "CREATE INDEX CONCURRENTLY account_use_email_d707ff_gin "
                    "ON account_user "
                    "USING gin (email gin_trgm_ops, first_name gin_trgm_ops, last_name gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS account_use_email_d707ff_gin;",
                (
                    "CREATE INDEX CONCURRENTLY account_use_email_d707ff_gin "
                    "ON account_user "
                    "USING gin (email, first_name, last_name);"
                ),
            ],
        ),
    ]
