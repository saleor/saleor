from typing import List

from ..celeryconf import app
from .models import Order, Subscription
from .utils import recalculate_order
from . import actions


@app.task
def recalculate_orders_task(order_ids: List[int]):
    orders = Order.objects.filter(id__in=order_ids)
    for order in orders:
        recalculate_order(order)


@app.task
def subscription_renew_task(subscription_pk: int):
    subscription = Subscription.objects.get(pk=subscription_pk)
    actions.subscription_renew(subscription)


@app.task
def subscription_update_status_task(subscription_pk: int, status: str):
    subscription = Subscription.objects.get(pk=subscription_pk)
    actions.subscription_update_status(subscription, status)
