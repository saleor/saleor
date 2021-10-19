from contextlib import contextmanager
from typing import Optional

from ....core.tracing import opentracing_trace
from ....order.events import external_notification_event
from ....order.models import Fulfillment, Order

CAPTURED_METADATA_KEY = "np_atobarai.fulfillment_is_captured"


def mark_fulfillment_as_captured(fulfillment: Fulfillment) -> None:
    fulfillment.store_value_in_private_metadata({CAPTURED_METADATA_KEY: "true"})
    fulfillment.save(update_fields=["metadata"])


def fulfillment_is_captured(fulfillment: Optional[Fulfillment]) -> bool:
    return bool(
        fulfillment and fulfillment.get_value_from_metadata(CAPTURED_METADATA_KEY)
    )


def notify_dashboard(order: Order, message: str):
    external_notification_event(
        order=order, user=None, app=None, message=message, parameters=None
    )


@contextmanager
def np_atobarai_opentracing_trace(span_name: str):
    with opentracing_trace(
        span_name=span_name,
        component_name="payment",
        service_name="np-atobarai",
    ):
        yield
