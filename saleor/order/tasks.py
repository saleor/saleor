from typing import List

from ..celeryconf import app
from .models import Order
from .utils import recalculate_order


@app.task
def recalculate_orders_task(order_ids: List[int]):
    orders = Order.objects.filter(id__in=order_ids)
    for order in orders:
        recalculate_order(order)
