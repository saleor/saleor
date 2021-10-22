from contextlib import contextmanager
from typing import Union

from ....core.tracing import opentracing_trace
from ....order.events import external_notification_event
from ....order.models import Order


def notify_dashboard(order: Order, message: str):
    external_notification_event(
        order=order, user=None, app=None, message=message, parameters=None
    )


def get_payment_name(payment_id: Union[int, str]) -> str:
    if not payment_id:
        return "payment"
    if isinstance(payment_id, str):
        return f"payment with psp reference {payment_id}"
    return f"payment with id {payment_id}"


@contextmanager
def np_atobarai_opentracing_trace(span_name: str):
    with opentracing_trace(
        span_name=span_name,
        component_name="payment",
        service_name="np-atobarai",
    ):
        yield
