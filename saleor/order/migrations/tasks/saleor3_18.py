from django.db.models import Sum

from ....celeryconf import app
from ...models import Order

# time it !
BATCH_SIZE = 5


@app.task
def update_order_subtotals(batch_id=None, batch_size=BATCH_SIZE):
    # Determine the starting and ending order numbers for the current batch
    if batch_id is None:
        batch_id = 0
    start_order_number = batch_id * batch_size
    end_order_number = start_order_number + batch_size

    # Get the orders for the current batch based on order numbers
    current_batch_order_numbers = Order.objects.filter(
        number__gte=start_order_number, number__lt=end_order_number
    ).values_list("number", flat=True)

    # If there are no orders in the range, exit the task
    if not current_batch_order_numbers:
        return

    orders_with_totals = Order.objects.filter(
        number__in=current_batch_order_numbers
    ).annotate(
        subtotal_net_sum=Sum("lines__total_price_net_amount"),
        subtotal_gross_sum=Sum("lines__total_price_gross_amount"),
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

    update_order_subtotals.delay(batch_id + 1, batch_size)
