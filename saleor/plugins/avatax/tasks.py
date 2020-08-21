from ...celeryconf import app
from ...core.taxes import TaxError
from ...order.events import external_notification_event
from ...order.models import Order
from . import AvataxConfiguration, api_post_request


@app.task(
    autoretry_for=(TaxError,), retry_backoff=60, retry_kwargs={"max_retries": 5},
)
def api_post_request_task(transaction_url, data, config, order_id):
    config = AvataxConfiguration(**config)
    response = api_post_request(transaction_url, data, config)
    order = Order.objects.get(id=order_id)
    if not order:
        return
    msg = "Order sent to Avatax."
    if not response:
        msg = "Unable to send order to Avatax."

    external_notification_event(order=order, user=None, message=msg, parameters=None)
    if not response:
        raise TaxError
