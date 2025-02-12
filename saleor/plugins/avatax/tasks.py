from celery.utils.log import get_task_logger
from django.conf import settings

from ...celeryconf import app
from ...core.db.connection import allow_writer
from ...core.taxes import TaxError
from ...core.telemetry import tracer
from ...order.events import external_notification_event
from ...order.models import Order
from . import AvataxConfiguration, api_post_request

task_logger = get_task_logger(__name__)


@app.task(
    autoretry_for=(TaxError,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 5},
)
@allow_writer()
def api_post_request_task(transaction_url, data, config, order_id):
    config = AvataxConfiguration(**config)
    order = (
        Order.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(id=order_id)
        .first()
    )
    if not order:
        task_logger.error(
            "Unable to send the order %s to Avatax. Order doesn't exist.", order_id
        )
        return
    if not data.get("createTransactionModel", {}).get("lines"):
        msg = "The order doesn't have any line which should be sent to Avatax."
        external_notification_event(
            order=order, user=None, app=None, message=msg, parameters=None
        )
        return

    with tracer.start_as_current_span("avatax.transactions.crateoradjust") as span:
        span.set_attribute("component", "tax")
        span.set_attribute("service.name", "avatax")
        response = api_post_request(transaction_url, data, config)
    msg = f"Order sent to Avatax. Order ID: {order.id}"
    if not response or "error" in response:
        avatax_msg = response.get("error", {}).get("message", "")
        msg = f"Unable to send order to Avatax. {avatax_msg}"
        task_logger.warning(
            "Unable to send order %s to Avatax. Response %s", order.id, response
        )

    external_notification_event(
        order=order, user=None, app=None, message=msg, parameters=None
    )
    if not response or "error" in response:
        raise TaxError
