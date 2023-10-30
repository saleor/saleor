from django.db import migrations


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ("discount", "0052_drop_sales_constraints"),
    ]

    operations = [
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY "discount_sale_collections_sale_id_a912da4a";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX CONCURRENTLY "
            '"discount_sale_collections_collection_id_f66df9d7";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY "discount_saletranslation_sale_id_36a69b0a";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY "discount_sale_categories_sale_id_2aeee4a7";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX CONCURRENTLY "
            '"discount_sale_categories_category_id_64e132af";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY "discount_sale_products_sale_id_10e3a20f";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY "discount_sale_products_product_id_d42c9636";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY "discount_sale_created_c17254d6";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY "discount_sale_updated_at_1fb1171b";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX CONCURRENTLY "
            '"discount_salechannellisting_channel_id_3319ed70";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY "discount_salechannellisting_sale_id_13a35e18";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY "discount_sale_variants_sale_id_50fc4c3a";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX CONCURRENTLY "
            '"discount_sale_variants_productvariant_id_91fa5f1b";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX CONCURRENTLY "
            '"discount_checkoutlinediscount_sale_id_b0964e58";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY "discount_orderlinediscount_sale_id_d95994f8";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY "discount_orderdiscount_sale_id_849ebbef";',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
