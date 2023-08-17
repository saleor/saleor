from typing import Union

from ...account.models import User
from ...app.models import App
from ...order.models import Order
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.utils import get_webhooks_for_event


def order_created(order: "Order", requestor: Union["User", "App"]):
    from ...plugins.webhook.tasks import trigger_webhooks_async
    from ...webhook.payloads import generate_order_payload

    event_type = WebhookEventAsyncType.ORDER_CREATED
    if webhooks := get_webhooks_for_event(event_type):
        order_data = generate_order_payload(order, requestor)
        trigger_webhooks_async(order_data, event_type, webhooks, order, requestor)
