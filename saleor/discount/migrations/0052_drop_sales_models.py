from django.db import migrations

DROP_CONSTRAINTS_SQL = """
do $$
declare
   r record;
   tab text;
   tabs text[] := array[
      'discount_sale_collections',
      'discount_sale_categories',
      'discount_sale_products',
      'discount_sale_variants',
      'discount_salechannellisting',
      'discount_saletranslation',
      'discount_sale'
   ];
begin
   ALTER TABLE discount_orderdiscount DROP CONSTRAINT IF EXISTS
      "discount_orderdiscount_sale_id_849ebbef_fk_discount_sale_id";
   ALTER TABLE discount_checkoutlinediscount DROP CONSTRAINT IF EXISTS
      "discount_checkoutlin_sale_id_b0964e58_fk_discount_";
   ALTER TABLE discount_orderlinediscount DROP CONSTRAINT IF EXISTS
      "discount_orderlinediscount_sale_id_d95994f8_fk_discount_sale_id";
   foreach tab in array tabs loop
      for r in (
         select constraint_name
         from information_schema.table_constraints
         where table_name=tab
      ) loop
         execute concat(
            'ALTER TABLE '||tab||' DROP CONSTRAINT IF EXISTS "'||r.constraint_name||'"'
         );
      end loop;
   end loop;
end;
$$
"""


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ("discount", "0051_detach_sale_from_permission"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    DROP_CONSTRAINTS_SQL, reverse_sql=migrations.RunSQL.noop
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY "
                    '"discount_sale_collections_sale_id_a912da4a";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY "
                    '"discount_sale_collections_collection_id_f66df9d7";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY "
                    '"discount_saletranslation_sale_id_36a69b0a";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY "
                    '"discount_sale_categories_sale_id_2aeee4a7";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY "
                    '"discount_sale_categories_category_id_64e132af";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY "
                    '"discount_sale_products_sale_id_10e3a20f";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY "
                    '"discount_sale_products_product_id_d42c9636";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY " '"discount_sale_created_c17254d6";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY " '"discount_sale_updated_at_1fb1171b";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY "
                    '"discount_salechannellisting_channel_id_3319ed70";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY "
                    '"discount_salechannellisting_sale_id_13a35e18";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY "
                    '"discount_sale_variants_sale_id_50fc4c3a";',
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
                    "DROP INDEX CONCURRENTLY "
                    '"discount_orderlinediscount_sale_id_d95994f8";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "DROP INDEX CONCURRENTLY "
                    '"discount_orderdiscount_sale_id_849ebbef";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="sale",
                    name="categories",
                ),
                migrations.RemoveField(
                    model_name="sale",
                    name="collections",
                ),
                migrations.RemoveField(
                    model_name="sale",
                    name="products",
                ),
                migrations.RemoveField(
                    model_name="sale",
                    name="variants",
                ),
                migrations.AlterUniqueTogether(
                    name="salechannellisting",
                    unique_together=None,
                ),
                migrations.RemoveField(
                    model_name="salechannellisting",
                    name="channel",
                ),
                migrations.RemoveField(
                    model_name="salechannellisting",
                    name="sale",
                ),
                migrations.AlterUniqueTogether(
                    name="saletranslation",
                    unique_together=None,
                ),
                migrations.RemoveField(
                    model_name="saletranslation",
                    name="sale",
                ),
                migrations.RemoveField(
                    model_name="checkoutlinediscount",
                    name="sale",
                ),
                migrations.RemoveField(
                    model_name="orderdiscount",
                    name="sale",
                ),
                migrations.RemoveField(
                    model_name="orderlinediscount",
                    name="sale",
                ),
                migrations.DeleteModel(
                    name="Sale",
                ),
                migrations.DeleteModel(
                    name="SaleChannelListing",
                ),
                migrations.DeleteModel(
                    name="SaleTranslation",
                ),
            ],
        ),
    ]
