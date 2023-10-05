from django.db import migrations, connection

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


# DROP INDEX CONCURRENTLY cannot be executed from a function, so we have to generate
# multiple statements
def generate_drop_index_sql():
    GET_INDEXES_SQL = """
        select indexname
        from pg_indexes
        where tablename in (
          'discount_sale_collections',
          'discount_sale_categories',
          'discount_sale_products',
          'discount_sale_variants',
          'discount_salechannellisting',
          'discount_saletranslation',
          'discount_sale'
        )
    """

    with connection.cursor() as cursor:
        cursor.execute(GET_INDEXES_SQL)
        indexes = cursor.fetchall()
    sqls = [f'DROP INDEX CONCURRENTLY "{index[0]}"' for index in indexes]
    return ";".join(sqls)


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0051_detach_sale_from_permission"),
    ]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    DROP_CONSTRAINTS_SQL, reverse_sql=migrations.RunSQL.noop
                ),
                # migrations.RunSQL(
                #     generate_drop_index_sql(), reverse_sql=migrations.RunSQL.noop
                # ),
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
