from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("page", "0029_add_page_translation_slug"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE UNIQUE INDEX CONCURRENTLY uniq_lang_slug_pagetransl
                    ON page_pagetranslation
                    ("language_code", "slug");
                    """,
                    reverse_sql="""
                    DROP INDEX CONCURRENTLY IF EXISTS uniq_lang_slug_pagetransl;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE page_pagetranslation
                    ADD CONSTRAINT uniq_lang_slug_pagetransl
                    UNIQUE USING INDEX uniq_lang_slug_pagetransl;
                    """,
                    reverse_sql="""
                    ALTER TABLE page_pagetranslation DROP CONSTRAINT
                    IF EXISTS uniq_lang_slug_pagetransl;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddConstraint(
                    model_name="pagetranslation",
                    constraint=models.UniqueConstraint(
                        fields=("language_code", "slug"),
                        name="uniq_lang_slug_pagetransl",
                    ),
                ),
            ],
        )
    ]
