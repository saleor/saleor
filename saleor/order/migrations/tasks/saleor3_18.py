from django.db.models import Exists, F, Func, OuterRef, Subquery
from django.forms.models import model_to_dict

from ....account.models import Address
from ....celeryconf import app
from ....warehouse.models import Warehouse
from ...models import Order, OrderLine

# celery task for one batch took 0.1s and 10.54MB at its peak
BATCH_SIZE = 1000

# The batch of size 250 takes ~0.5 second and consumes ~20MB memory at peak
ADDRESS_UPDATE_BATCH_SIZE = 250


@app.task
def update_order_subtotals(start_number=None):
    if start_number is None:
        first_order = Order.objects.last()
        if first_order is None:
            return  # Exit if there are no orders
        start_number = first_order.number

    # Get the orders for the current batch based on order numbers
    lines = OrderLine.objects.all()
    queryset = Order.objects.order_by("number").filter(
        Exists(lines.filter(order_id=OuterRef("id"))), number__gte=start_number
    )[:BATCH_SIZE]
    current_batch_order_numbers = list(queryset.values_list("number", flat=True))

    # If there are no orders in the range, exit the task
    if not current_batch_order_numbers:
        return

    order_line = OrderLine.objects.filter(order=OuterRef("pk"))
    subtotal_net_sum = order_line.annotate(
        net_sum=Func(F("total_price_net_amount"), function="Sum")
    ).values("net_sum")

    subtotal_gross_sum = order_line.annotate(
        gross_sum=Func(F("total_price_gross_amount"), function="Sum")
    ).values("gross_sum")

    orders_with_totals = Order.objects.filter(
        number__in=current_batch_order_numbers
    ).annotate(
        subtotal_net_sum=Subquery(subtotal_net_sum),
        subtotal_gross_sum=Subquery(subtotal_gross_sum),
    )

    # Iterate over annotated orders and update them in batches
    orders_to_update = []
    for order in orders_with_totals:
        order.subtotal_net_amount = order.subtotal_net_sum
        order.subtotal_gross_amount = order.subtotal_gross_sum
        orders_to_update.append(order)

    Order.objects.bulk_update(
        orders_to_update, ["subtotal_net_amount", "subtotal_gross_amount"]
    )

    last_number = current_batch_order_numbers[-1]
    update_order_subtotals.delay(last_number + 1)


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
