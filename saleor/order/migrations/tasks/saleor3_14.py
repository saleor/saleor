from django.utils import timezone
from django.db.models import OuterRef, Exists
from django.forms.models import model_to_dict

from ....celeryconf import app
from ... import OrderStatus
from ...models import Order
from ....account.models import Address
from ....warehouse.models import Warehouse

# Batch size of size 5000 is about 5MB memory usage in task
PROPAGATE_EXPIRED_AT_BATCH_SIZE = 5000

# The batch of size 250 takes ~0.5 second and consumes ~20MB memory at peak
ADDRESS_UPDATE_BATCH_SIZE = 250


@app.task
def order_propagate_expired_at_task():
    qs = Order.objects.filter(status=OrderStatus.EXPIRED, expired_at__isnull=True)
    order_ids = qs.values_list("pk", flat=True)[:PROPAGATE_EXPIRED_AT_BATCH_SIZE]
    if order_ids:
        Order.objects.filter(id__in=order_ids).update(expired_at=timezone.now())
        order_propagate_expired_at_task.delay()


@app.task
def update_order_addresses_task():
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
