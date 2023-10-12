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
    dependencies = [
        ("discount", "0051_detach_sale_from_permission"),
    ]

    operations = [
        migrations.RunSQL(DROP_CONSTRAINTS_SQL, reverse_sql=migrations.RunSQL.noop),
    ]
