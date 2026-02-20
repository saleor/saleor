"""Fix GIN index on PageType model.

The migration 0023 created a GIN index on (name, slug) CharField fields
without specifying the gin_trgm_ops operator class.

This migration recreates the index with the correct operator class.

See: https://github.com/saleor/saleor/issues/18341
"""

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("page", "0035_page_page_slug_btree_idx"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS page_pagety_name_7c1cb8_gin;",
                (
                    "CREATE INDEX CONCURRENTLY page_pagety_name_7c1cb8_gin "
                    "ON page_pagetype "
                    "USING gin (name gin_trgm_ops, slug gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS page_pagety_name_7c1cb8_gin;",
                (
                    "CREATE INDEX CONCURRENTLY page_pagety_name_7c1cb8_gin "
                    "ON page_pagetype "
                    "USING gin (name, slug);"
                ),
            ],
        ),
    ]
