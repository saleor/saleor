from django.db import migrations
from django.db.models import F


def set_order_line_base_prices(apps, schema_editor):
    SiteSettings = apps.get_model("site", "SiteSettings")
    OrderLine = apps.get_model("order", "OrderLine")
    site_settings = SiteSettings.objects.first()
    included_taxes = site_settings.include_taxes_in_prices if site_settings else None
    if not included_taxes:
        OrderLine.objects.all().update(
            undiscounted_base_unit_price_amount=F("undiscounted_unit_price_net_amount"),
            base_unit_price_amount=F("unit_price_net_amount"),
        )
    else:
        OrderLine.objects.all().update(
            undiscounted_base_unit_price_amount=F(
                "undiscounted_unit_price_gross_amount"
            ),
            base_unit_price_amount=F("unit_price_gross_amount"),
        )


class Migration(migrations.Migration):
    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("site", "0034_sitesettings_limit_quantity_per_checkout"),
        ("order", "0137_auto_20220427_0822"),
    ]

    operations = [
        migrations.RunPython(
            set_order_line_base_prices, reverse_code=migrations.RunPython.noop
        ),
    ]
