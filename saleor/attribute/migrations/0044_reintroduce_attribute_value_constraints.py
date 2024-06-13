from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("attribute", "0043_merge_20240606_1430"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
                    attribute_assignedpageat_value_id_page_id_851cd501_uniq
                    ON attribute_assignedpageattributevalue
                    ("value_id", "page_id");
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS
                    attribute_assignedpageat_value_id_page_id_851cd501_uniq;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                        DO
                        $do$
                        BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_catalog.pg_constraint
                            WHERE conname LIKE
                            'attribute_assignedpageat_value_id_page_id_851cd501_uniq'
                        ) THEN
                            ALTER TABLE attribute_assignedpageattributevalue
                            ADD CONSTRAINT
                            attribute_assignedpageat_value_id_page_id_851cd501_uniq
                            UNIQUE USING INDEX
                            attribute_assignedpageat_value_id_page_id_851cd501_uniq;
                        END IF;
                        END
                        $do$
                    """,
                    reverse_sql="""
                    ALTER TABLE attribute_assignedpageattributevalue DROP CONSTRAINT
                    IF EXISTS attribute_assignedpageat_value_id_page_id_851cd501_uniq;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
                    attribute_assignedproduc_value_id_product_id_6f6deb31_uniq
                    ON attribute_assignedproductattributevalue
                    ("value_id", "product_id");
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS
                    attribute_assignedproduc_value_id_product_id_6f6deb31_uniq;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                        DO
                        $do$
                        BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_catalog.pg_constraint
                            WHERE conname LIKE
                            'attribute_assignedproduc_value_id_product_id_6f6deb31_uniq'
                        ) THEN
                            ALTER TABLE attribute_assignedproductattributevalue
                            ADD CONSTRAINT
                            attribute_assignedproduc_value_id_product_id_6f6deb31_uniq
                            UNIQUE USING INDEX
                            attribute_assignedproduc_value_id_product_id_6f6deb31_uniq;
                        END IF;
                        END
                        $do$
                    """,
                    reverse_sql="""
                    ALTER TABLE attribute_assignedproductattributevalue DROP CONSTRAINT
                    IF EXISTS attribute_assignedproduc_value_id_product_id_6f6deb31_uniq;
                    """,
                ),
            ]
        )
    ]
