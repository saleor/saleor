from django.db import migrations
from django.conf import settings


def create_default_warehouse(apps, schema_editor):
    if settings.POPULATE_DEFAULTS:
        address = apps.get_model("account", "Address").objects.create(country="US")
        Channel = apps.get_model("channel", "Channel")
        Warehouse = apps.get_model("warehouse", "Warehouse")
        if not Warehouse.objects.all().exists():
            warehouse = Warehouse.objects.create(
                address=address,
                name="Default Warehouse",
                slug="default-warehouse",
            )

            channel = Channel.objects.filter(slug="default-channel").first()
            if channel:
                warehouse.channels.add(channel)


class Migration(migrations.Migration):
    dependencies = [
        ("channel", "0004_create_default_channel"),
        ("warehouse", "0030_add_channels_to_warehouses"),
    ]

    operations = [
        migrations.RunPython(create_default_warehouse, migrations.RunPython.noop),
    ]
