from django.contrib.postgres.indexes import BTreeIndex
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("product", "0195_add_slug_to_translations"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE UNIQUE INDEX CONCURRENTLY uniq_lang_slug_categorytransl
                    ON product_categorytranslation
                    ("language_code", "slug");
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS uniq_lang_slug_categorytransl;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE product_categorytranslation
                    ADD CONSTRAINT uniq_lang_slug_categorytransl
                    UNIQUE USING INDEX uniq_lang_slug_categorytransl;
                    """,
                    reverse_sql="""
                    ALTER TABLE product_categorytranslation DROP CONSTRAINT
                    IF EXISTS uniq_lang_slug_categorytransl;
                    """,
                ),
            ],
            state_operations=[
                AddIndexConcurrently(
                    model_name="categorytranslation",
                    index=BTreeIndex(
                        fields=["language_code", "slug"],
                        name="uniq_lang_slug_categorytransl",
                    ),
                ),
                migrations.AddConstraint(
                    model_name="categorytranslation",
                    constraint=models.UniqueConstraint(
                        fields=("language_code", "slug"),
                        name="uniq_lang_slug_categorytransl",
                    ),
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE UNIQUE INDEX CONCURRENTLY uniq_lang_slug_collectiontransl
                    ON product_collectiontranslation
                    ("language_code", "slug");
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS uniq_lang_slug_collectiontransl;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE product_collectiontranslation
                    ADD CONSTRAINT uniq_lang_slug_collectiontransl
                    UNIQUE USING INDEX uniq_lang_slug_collectiontransl;
                    """,
                    reverse_sql="""
                    ALTER TABLE product_collectiontranslation DROP CONSTRAINT
                    IF EXISTS uniq_lang_slug_collectiontransl;
                    """,
                ),
            ],
            state_operations=[
                AddIndexConcurrently(
                    model_name="collectiontranslation",
                    index=BTreeIndex(
                        fields=["language_code", "slug"],
                        name="uniq_lang_slug_collectiontransl",
                    ),
                ),
                migrations.AddConstraint(
                    model_name="collectiontranslation",
                    constraint=models.UniqueConstraint(
                        fields=("language_code", "slug"),
                        name="uniq_lang_slug_collectiontransl",
                    ),
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE UNIQUE INDEX CONCURRENTLY uniq_lang_slug_producttransl
                    ON product_producttranslation
                    ("language_code", "slug");
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS uniq_lang_slug_producttransl;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE product_producttranslation
                    ADD CONSTRAINT uniq_lang_slug_producttransl
                    UNIQUE USING INDEX uniq_lang_slug_producttransl;
                    """,
                    reverse_sql="""
                    ALTER TABLE product_producttranslation DROP CONSTRAINT
                    IF EXISTS uniq_lang_slug_producttransl;
                    """,
                ),
            ],
            state_operations=[
                AddIndexConcurrently(
                    model_name="producttranslation",
                    index=BTreeIndex(
                        fields=["language_code", "slug"],
                        name="uniq_lang_slug_producttransl",
                    ),
                ),
                migrations.AddConstraint(
                    model_name="producttranslation",
                    constraint=models.UniqueConstraint(
                        fields=("language_code", "slug"),
                        name="uniq_lang_slug_producttransl",
                    ),
                ),
            ],
        ),
    ]
