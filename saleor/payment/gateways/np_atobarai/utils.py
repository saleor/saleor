from contextlib import contextmanager

from ....core.tracing import opentracing_trace
from ....order.models import Fulfillment
from ... import ChargeStatus


@contextmanager
def np_atobarai_opentracing_trace(span_name: str):
    with opentracing_trace(
        span_name=span_name,
        component_name="payment",
        service_name="np-atobarai",
    ):
        yield


def mark_payment_as_fully_charged(fulfillment: Fulfillment) -> None:
    order = fulfillment.order
    payment = order.get_last_payment()
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = order.total.gross.amount
    payment.save(update_fields=["captured_amount", "charge_status", "modified"])
