from django.db import migrations


class Migration(migrations.Migration):
    """Drop the legacy digital content tables.

    Both models were removed from the Django state in
    `0204_remove_digitalcontent_from_state` (Saleor 3.23), so no running pod
    reads or writes these tables anymore.
    """

    dependencies = [("product", "0205_merge_20260615_1308")]

    operations = [
        migrations.RunSQL(
            # Drop the child table first, it holds a FK to product_digitalcontent.
            sql="DROP TABLE IF EXISTS product_digitalcontenturl;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS product_digitalcontent;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
