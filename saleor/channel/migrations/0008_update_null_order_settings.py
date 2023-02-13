from django.db import migrations
from django.db.models import Q

# In case of worker working on upplied 0007 migration and old code,
# could have happen to create `Channel` with null site settings.
# This migration makes sure to covers such cases.


# Small note: Filtering null values is only for performance.
# Updating all channells would have ended up with the same result.
def set_order_settings(apps, schema_editor):
    SiteSettings = apps.get_model("site", "SiteSettings")
    Channel = apps.get_model("channel", "Channel")

    site_settings = SiteSettings.objects.first()

    Channel.objects.filter(
        Q(automatically_confirm_all_new_orders__isnull=True)
        | Q(automatically_fulfill_non_shippable_gift_card__isnull=True)
    ).update(
        automatically_confirm_all_new_orders=(
            site_settings.automatically_confirm_all_new_orders
        ),
        automatically_fulfill_non_shippable_gift_card=(
            site_settings.automatically_fulfill_non_shippable_gift_card
        ),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("channel", "0007_order_settings_per_channel"),
    ]

    operations = [
        migrations.RunPython(set_order_settings, migrations.RunPython.noop),
    ]
