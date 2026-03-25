"""Fix GIN index on AttributeValue model.

The migration 0011 created a GIN index on (name, slug) CharField fields
without specifying the gin_trgm_ops operator class. On newer PostgreSQL
versions this fails with:
    ProgrammingError: data type character varying has no default operator
    class for access method "gin"

This migration recreates the index with the correct operator class.

See: https://github.com/saleor/saleor/issues/18341
"""

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("attribute", "0055_assignedvariantattributevalue_variant"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS attribute_a_name_9f3448_gin;",
                (
                    "CREATE INDEX CONCURRENTLY attribute_a_name_9f3448_gin "
                    "ON attribute_attributevalue "
                    "USING gin (name gin_trgm_ops, slug gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS attribute_a_name_9f3448_gin;",
                (
                    "CREATE INDEX CONCURRENTLY attribute_a_name_9f3448_gin "
                    "ON attribute_attributevalue "
                    "USING gin (name, slug);"
                ),
            ],
        ),
    ]
