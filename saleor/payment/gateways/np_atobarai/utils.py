from collections import defaultdict
from contextlib import contextmanager
from decimal import Decimal
from itertools import chain
from typing import Dict, Optional

from django.db.models import Q, Sum

from ....core.tracing import opentracing_trace
from ....order import FulfillmentStatus
from ....order.events import external_notification_event
from ....order.models import Fulfillment, FulfillmentLine, Order
from ... import PaymentError
from ...interface import PaymentData, RefundData
from .api_types import ApiConfig
from .const import SHIPPING_COMPANY_CODE_METADATA_KEY, SHIPPING_COMPANY_CODES


def notify_dashboard(order: Order, message: str):
    external_notification_event(
        order=order, user=None, app=None, message=message, parameters=None
    )


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


def create_refunded_lines(
    order: Order,
    refund_data: RefundData,
) -> Dict[int, int]:
    """Return all refunded product variants for specified order.

    Takes into account previous refunds and current refund mutation parameters.
    :return: Dictionary of variant ids and refunded quantities.
    """
    if not refund_data.refund_amount_is_automatically_calculated:
        order_lines_to_refund = []
        fulfillment_lines_to_refund = []
    else:
        order_lines_to_refund = refund_data.order_lines_to_refund
        fulfillment_lines_to_refund = refund_data.fulfillment_lines_to_refund

    previous_fulfillment_lines = FulfillmentLine.objects.prefetch_related(
        "order_line"
    ).filter(
        fulfillment__order_id=order.pk,
        fulfillment__status__in=[
            FulfillmentStatus.REFUNDED,
            FulfillmentStatus.REFUNDED_AND_RETURNED,
        ],
        order_line__variant_id__isnull=False,
    )

    previous_refund_lines = (
        (p_variant_id, line1.quantity)
        for line1 in previous_fulfillment_lines
        if (p_variant_id := line1.order_line.variant_id)
    )
    current_order_refund_lines = (
        (variant.id, line1.quantity)
        for line1 in order_lines_to_refund
        if (variant := line1.variant)
    )
    current_fulfillment_refund_lines = (
        (f_variant_id, line1.quantity)
        for line1 in fulfillment_lines_to_refund
        if (f_variant_id := line1.line.order_line.variant_id)
    )

    refund_lines = chain(
        previous_refund_lines,
        current_order_refund_lines,
        current_fulfillment_refund_lines,
    )
    summed_refund_lines: Dict[int, int] = defaultdict(int)

    for variant_id, quantity in refund_lines:
        summed_refund_lines[variant_id] += quantity

    return dict(summed_refund_lines)


def calculate_manual_refund_amount(
    order: Order,
    payment_information: PaymentData,
    refund_data: RefundData,
) -> Decimal:
    """Return sum of all manual refunds for specified order.

    Takes into account previous refunds and current refund mutation amount.
    """
    if (
        refund_data.order_lines_to_refund or refund_data.fulfillment_lines_to_refund
    ) and refund_data.refund_amount_is_automatically_calculated:
        # automatic line refund
        manual_amount_to_refund = Decimal("0.00")
    elif (
        refund_data.refund_shipping_costs
        and refund_data.refund_amount_is_automatically_calculated
    ):
        # automatic shipping refund
        manual_amount_to_refund = payment_information.lines_data.shipping_amount
    else:
        # manual refund
        manual_amount_to_refund = payment_information.amount or Decimal("0.00")

    previous_manual_amount_to_refund = (
        order.fulfillments.filter(
            status__in=[
                FulfillmentStatus.REFUNDED,
                FulfillmentStatus.REFUNDED_AND_RETURNED,
            ],
            lines__isnull=True,
        ).aggregate(manual_amount=Sum("total_refund_amount"))["manual_amount"]
        or Decimal("0.00")
    )

    return previous_manual_amount_to_refund + manual_amount_to_refund
