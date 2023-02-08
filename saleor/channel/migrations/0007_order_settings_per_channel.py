from django.db import migrations


def set_order_settings(apps, schema_editor):
    SiteSettings = apps.get_model("site", "SiteSettings")
    Channel = apps.get_model("channel", "Channel")

    site_settings = SiteSettings.objects.first()

    Channel.objects.update(
        automatically_confirm_all_new_orders=(
            site_settings.automatically_confirm_all_new_orders
        ),
        automatically_fulfill_non_shippable_gift_card=(
            site_settings.automatically_fulfill_non_shippable_gift_card
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("channel", "0006_order_settings_fields"),
        ("site", "0032_gift_card_settings"),
    ]

    operations = [
        migrations.RunPython(set_order_settings, migrations.RunPython.noop),
    ]
