from django.db import migrations
from django.db.models import Exists, OuterRef
from django.forms.models import model_to_dict

from .tasks.saleor3_19 import update_order_addresses_task

# The batch of size 250 takes ~0.5 second and consumes ~20MB memory at peak
ADDRESS_UPDATE_BATCH_SIZE = 250


def update_order_addresses(apps, schema_editor):
    Order = apps.get_model("order", "Order")
    Warehouse = apps.get_model("warehouse", "Warehouse")
    Address = apps.get_model("account", "Address")
    qs = Order.objects.filter(
        Exists(Warehouse.objects.filter(address_id=OuterRef("shipping_address_id"))),
    )
    order_ids = qs.values_list("pk", flat=True)[:ADDRESS_UPDATE_BATCH_SIZE]
    addresses = []
    if order_ids:
        orders = Order.objects.filter(id__in=order_ids)
        for order in orders:
            if cc_address := order.shipping_address:
                order_address = Address(**model_to_dict(cc_address, exclude=["id"]))
                order.shipping_address = order_address
                addresses.append(order_address)
        Address.objects.bulk_create(addresses, ignore_conflicts=True)
        Order.objects.bulk_update(orders, ["shipping_address"])
        update_order_addresses_task.delay()


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0171_order_order_user_email_user_id_idx"),
    ]

    operations = [
        migrations.RunPython(update_order_addresses, migrations.RunPython.noop),
    ]
