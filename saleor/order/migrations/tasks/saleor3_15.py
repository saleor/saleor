from django.db.models import Exists, OuterRef
from django.forms.models import model_to_dict

from ....celeryconf import app
from ....payment.models import TransactionItem
from ...models import OrderEvent, Order
from ....account.models import Address
from ....warehouse.models import Warehouse

# Batch size of size 5000 is about 5MB memory usage in task
BATCH_SIZE = 5000

# The batch of size 250 takes ~0.5 second and consumes ~20MB memory at peak
ADDRESS_UPDATE_BATCH_SIZE = 250


@app.task
def drop_status_field_from_transaction_event_task():
    orders = TransactionItem.objects.filter(order_id__isnull=False)

    qs = OrderEvent.objects.filter(
        Exists(orders.filter(order_id=OuterRef("order_id"))),
        type="transaction_event",
        parameters__has_key="status",
    )

    event_ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    if event_ids:
        events_to_update = []
        events = OrderEvent.objects.filter(id__in=event_ids)
        for event in events:
            if "status" in event.parameters:
                del event.parameters["status"]
                events_to_update.append(event)
        OrderEvent.objects.bulk_update(events_to_update, ["parameters"])
        drop_status_field_from_transaction_event_task.delay()


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
