from contextlib import contextmanager
from typing import Optional, Union

from django.db.models import Q

from ....core.tracing import opentracing_trace
from ....order import FulfillmentStatus
from ....order.events import external_notification_event
from ....order.models import Fulfillment, Order
from ... import PaymentError
from .api_types import ApiConfig
from .const import SHIPPING_COMPANY_CODE_METADATA_KEY, SHIPPING_COMPANY_CODES


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


STATUSES_NOT_ALLOWED_TO_REFUND = [
    FulfillmentStatus.CANCELED,
    FulfillmentStatus.REFUNDED,
    FulfillmentStatus.REPLACED,
    FulfillmentStatus.REFUNDED_AND_RETURNED,
    FulfillmentStatus.RETURNED,
]


def get_shipping_company_code(
    config: ApiConfig, fulfillment: Fulfillment
) -> Optional[str]:
    code = fulfillment.get_value_from_private_metadata(
        SHIPPING_COMPANY_CODE_METADATA_KEY, default=config.shipping_company
    )
    return None if code not in SHIPPING_COMPANY_CODES else code


def get_fulfillment_for_order(order: Order) -> Fulfillment:
    fulfillments = order.fulfillments.exclude(
        Q(tracking_number="") | Q(status__in=STATUSES_NOT_ALLOWED_TO_REFUND)
    )

    if fulfillments.count() == 0:
        raise PaymentError(
            "Fulfillment with tracking number does not exist for this order"
        )

    if fulfillments.count() > 1:
        raise PaymentError(
            "More than one fulfillment with tracking number exist for this order"
        )

    return fulfillments[0]


@contextmanager
def np_atobarai_opentracing_trace(span_name: str):
    with opentracing_trace(
        span_name=span_name,
        component_name="payment",
        service_name="np-atobarai",
    ):
        yield
