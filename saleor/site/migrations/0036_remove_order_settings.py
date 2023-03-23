from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("site", "0035_sitesettings_separate_state_remove_order_settings")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE site_sitesettings
                    DROP COLUMN
                    automatically_fulfill_non_shippable_gift_card,
                    DROP COLUMN
                    automatically_confirm_all_new_orders;
                    """,
                    reverse_sql="""
                    ALTER TABLE site_sitesettings
                    ADD COLUMN
                    automatically_fulfill_non_shippable_gift_card
                    BOOLEAN,
                    ADD COLUMN
                    automatically_confirm_all_new_orders
                    BOOLEAN;
                    """,
                )
            ]
        )
    ]
