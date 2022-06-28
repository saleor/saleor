from typing import List

from ..celeryconf import app
from ..plugins.manager import get_plugins_manager
from .models import Order
from .utils import recalculate_order


@app.task
def recalculate_orders_task(order_ids: List[int]):
    orders = Order.objects.filter(id__in=order_ids)
    for order in orders:
        recalculate_order(order)


@app.task
def send_order_updated(order_ids):
    manager = get_plugins_manager()
    for order in Order.objects.filter(id__in=order_ids):
        manager.order_updated(order)
