import pytest

from .....order import FulfillmentStatus, OrderEvents
from .... import PaymentError
from .. import get_fulfillment_for_order, get_payment_name, notify_dashboard


def test_notify_dashboard(order):
    # given
    message = "message"

    # when
    notify_dashboard(order, message)

    # then
    event = order.events.first()
    assert event.type == OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    assert event.parameters["message"] == message


@pytest.mark.parametrize(
    "payment_id, result",
    [
        ("123", "payment with psp reference 123"),
        (123, "payment with id 123"),
        ("", "payment"),
    ],
)
def test_get_payment_name(payment_id, result):
    # when
    payment_name = get_payment_name(payment_id)

    # then
    assert payment_name == result


def test_get_fulfillment_for_order(order):
    # given
    expected_fulfillment = order.fulfillments.create(tracking_number="123")

    # when
    fulfillment = get_fulfillment_for_order(order)

    # then
    assert expected_fulfillment == fulfillment


def test_get_fulfillment_for_order_multiple_fulfillments_one_valid(order):
    # then
    expected_fulfillment = order.fulfillments.create(tracking_number="123")
    order.fulfillments.create(tracking_number="234", status=FulfillmentStatus.REFUNDED)

    # when
    fulfillment = get_fulfillment_for_order(order)

    # then
    assert expected_fulfillment == fulfillment


def test_get_fulfillment_for_order_no_fulfillment(order):
    # then
    with pytest.raises(PaymentError, match=r".* not exist .*"):

        # when
        get_fulfillment_for_order(order)


def test_get_fulfillment_for_order_no_fulfillment_with_tracking_number(order):
    # given
    order.fulfillments.create()

    # then
    with pytest.raises(PaymentError, match=r".* not exist .*"):

        # when
        get_fulfillment_for_order(order)


def test_get_fulfillment_for_order_no_refundable_fulfillment(order):
    # given
    order.fulfillments.create(tracking_number="123", status=FulfillmentStatus.REFUNDED)

    # then
    with pytest.raises(PaymentError, match=r".* not exist .*"):

        # when
        get_fulfillment_for_order(order)


def test_get_fulfillment_for_order_multiple_fulfillments(order, fulfillment):
    # given
    order.fulfillments.create(tracking_number="123")
    order.fulfillments.create(tracking_number="234")

    # then
    with pytest.raises(PaymentError, match=r"More than one .* exist .*"):

        # when
        get_fulfillment_for_order(order)
