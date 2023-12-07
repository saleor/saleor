from django.db.models import F, Func, Min, OuterRef, Subquery

from ....celeryconf import app
from ...models import Order, OrderLine

# celery task for one batch took 0.1s and 10.54MB at its peak
BATCH_SIZE = 1000


@app.task
def update_order_subtotals(batch_id=None):
    if batch_id is None:
        # Get the minimum order number from the database
        min_order_number = Order.objects.aggregate(Min("number"))["number__min"] or 0
        batch_id = min_order_number // BATCH_SIZE

    start_order_number = batch_id * BATCH_SIZE
    end_order_number = start_order_number + BATCH_SIZE

    # Get the orders for the current batch based on order numbers
    current_batch_order_numbers = Order.objects.filter(
        number__gte=start_order_number, number__lt=end_order_number
    ).values_list("number", flat=True)

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

    update_order_subtotals.delay(batch_id + 1)
