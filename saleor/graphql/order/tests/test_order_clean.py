from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError

from ....order import FulfillmentStatus, OrderStatus
from ....order.error_codes import OrderErrorCode
from ....payment.models import Payment
from ..mutations.order_cancel import clean_order_cancel
from ..mutations.order_capture import clean_order_capture
from ..mutations.order_refund import clean_refund_payment


def test_clean_order_refund_payment():
    payment = MagicMock(spec=Payment)
    payment.can_refund.return_value = False
    with pytest.raises(ValidationError) as e:
        clean_refund_payment(payment)
    assert e.value.error_dict["payment"][0].code == OrderErrorCode.CANNOT_REFUND.value


def test_clean_order_capture():
    with pytest.raises(ValidationError) as e:
        clean_order_capture(None)
    msg = "There's no payment associated with the order."
    assert e.value.error_dict["payment"][0].message == msg


@pytest.mark.parametrize(
    "status",
    [
        FulfillmentStatus.RETURNED,
        FulfillmentStatus.REFUNDED_AND_RETURNED,
        FulfillmentStatus.REFUNDED,
        FulfillmentStatus.CANCELED,
        FulfillmentStatus.REPLACED,
    ],
)
def test_clean_order_cancel(status, fulfillment):
    order = fulfillment.order
    fulfillment.status = status
    fulfillment.save()
    # Shouldn't raise any errors
    assert clean_order_cancel(order) is order


def test_clean_order_cancel_draft_order(
    fulfilled_order_with_all_cancelled_fulfillments,
):
    order = fulfilled_order_with_all_cancelled_fulfillments

    order.status = OrderStatus.DRAFT
    order.save()

    with pytest.raises(ValidationError) as e:
        clean_order_cancel(order)
    assert (
        e.value.error_dict["order"][0].code == OrderErrorCode.CANNOT_CANCEL_ORDER.value
    )


def test_clean_order_cancel_canceled_order(
    fulfilled_order_with_all_cancelled_fulfillments,
):
    order = fulfilled_order_with_all_cancelled_fulfillments

    order.status = OrderStatus.CANCELED
    order.save()

    with pytest.raises(ValidationError) as e:
        clean_order_cancel(order)
    assert (
        e.value.error_dict["order"][0].code == OrderErrorCode.CANNOT_CANCEL_ORDER.value
    )


def test_clean_order_cancel_order_with_fulfillment(
    fulfilled_order_with_cancelled_fulfillment,
):
    order = fulfilled_order_with_cancelled_fulfillment

    order.status = OrderStatus.CANCELED
    order.save()

    with pytest.raises(ValidationError) as e:
        clean_order_cancel(order)
    assert (
        e.value.error_dict["order"][0].code == OrderErrorCode.CANNOT_CANCEL_ORDER.value
    )
