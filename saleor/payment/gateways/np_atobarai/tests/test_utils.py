import pytest

from .....order import FulfillmentStatus, OrderEvents
from .... import PaymentError
from .. import (
    get_fulfillment_for_order,
    get_payment_name,
    get_shipping_company_code,
    notify_dashboard,
)
from ..const import SHIPPING_COMPANY_CODE_METADATA_KEY, SHIPPING_COMPANY_CODES


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


@pytest.mark.parametrize(
    "config_shipping_company_code",
    SHIPPING_COMPANY_CODES,
)
def test_get_shipping_company_code_no_metadata(
    config, fulfillment, config_shipping_company_code
):
    # given
    config.shipping_company = config_shipping_company_code

    # when
    shipping_company_code = get_shipping_company_code(config, fulfillment)

    # then
    assert shipping_company_code == config_shipping_company_code


@pytest.mark.parametrize(
    ["config_shipping_company_code", "result_shipping_company_code"],
    zip(SHIPPING_COMPANY_CODES + ["invalid_code"], SHIPPING_COMPANY_CODES + [None]),
)
def test_get_shipping_company_code_valid_metadata(
    config, fulfillment, config_shipping_company_code, result_shipping_company_code
):
    # given
    fulfillment.store_value_in_private_metadata(
        {SHIPPING_COMPANY_CODE_METADATA_KEY: config_shipping_company_code}
    )
    fulfillment.save(update_fields=["private_metadata"])

    # when
    shipping_company_code = get_shipping_company_code(config, fulfillment)

    # then
    assert shipping_company_code == result_shipping_company_code


@pytest.mark.parametrize(
    "config_shipping_company_code",
    SHIPPING_COMPANY_CODES,
)
def test_get_shipping_company_code_invalid_metadata(
    config, fulfillment, config_shipping_company_code
):
    # given
    config.shipping_company = config_shipping_company_code
    fulfillment.store_value_in_private_metadata({"invalid_metadata_key": "50000"})
    fulfillment.save(update_fields=["private_metadata"])

    # when
    shipping_company_code = get_shipping_company_code(config, fulfillment)

    # then
    assert shipping_company_code == config_shipping_company_code
