from django.db import migrations


class Migration(migrations.Migration):
    """Drop the legacy digital content shop settings columns.

    The fields were removed from the Django state in
    `0046_remove_digital_content_settings_from_state` (Saleor 3.23), so no
    running pod reads or writes these columns anymore.
    """

    dependencies = [("site", "0051_merge_20260717_1400")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # A single ALTER TABLE: dropping a column is a metadata-only
                # operation, so one statement means one short lock instead of
                # three.
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE site_sitesettings
                    DROP COLUMN automatic_fulfillment_digital_products,
                    DROP COLUMN default_digital_max_downloads,
                    DROP COLUMN default_digital_url_valid_days;
                    """,
                    reverse_sql="""
                    ALTER TABLE site_sitesettings
                    ADD COLUMN automatic_fulfillment_digital_products
                    BOOLEAN NOT NULL DEFAULT false,
                    ADD COLUMN default_digital_max_downloads INTEGER,
                    ADD COLUMN default_digital_url_valid_days INTEGER;
                    """,
                )
            ]
        )
    ]
