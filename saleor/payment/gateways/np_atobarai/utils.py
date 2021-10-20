from contextlib import contextmanager

from ....core.tracing import opentracing_trace
from ....order.events import external_notification_event
from ....order.models import Order


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
