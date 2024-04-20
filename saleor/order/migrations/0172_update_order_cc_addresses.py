from django.db import migrations
from django.db.models import Exists, OuterRef
from django.forms.models import model_to_dict

# The batch of size 250 takes ~0.5 second and consumes ~20MB memory at peak
ADDRESS_UPDATE_BATCH_SIZE = 250


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted be pk.
    """
    start_pk = 0

    while True:
        qs = queryset.filter(pk__gt=start_pk)[:ADDRESS_UPDATE_BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))
        if not pks:
            break
        yield pks
        start_pk = pks[-1]


def update_order_addresses(apps, schema_editor):
    Order = apps.get_model("order", "Order")
    Warehouse = apps.get_model("warehouse", "Warehouse")
    Address = apps.get_model("account", "Address")
    queryset = Order.objects.filter(
        Exists(Warehouse.objects.filter(address_id=OuterRef("shipping_address_id"))),
    ).order_by("pk")

    for order_ids in queryset_in_batches(queryset):
        orders = Order.objects.filter(id__in=order_ids)
        addresses = []
        for order in orders:
            if cc_address := order.shipping_address:
                order_address = Address(**model_to_dict(cc_address, exclude=["id"]))
                order.shipping_address = order_address
                addresses.append(order_address)
        Address.objects.bulk_create(addresses, ignore_conflicts=True)
        Order.objects.bulk_update(orders, ["shipping_address"])


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0171_order_order_user_email_user_id_idx"),
    ]

    operations = [
        migrations.RunPython(update_order_addresses, migrations.RunPython.noop),
    ]
