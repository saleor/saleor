from itertools import chain, zip_longest
from unittest.mock import Mock, patch

import pytest

from .....order import FulfillmentLineData, FulfillmentStatus, OrderEvents
from .....order.fetch import OrderLineInfo
from .... import PaymentError
from ....interface import RefundData
from .. import get_fulfillment_for_order, get_shipping_company_code, notify_dashboard
from ..const import SHIPPING_COMPANY_CODE_METADATA_KEY, SHIPPING_COMPANY_CODES
from ..utils import create_refunded_lines


def test_notify_dashboard(order):
    # given
    message = "message"

    # when
    notify_dashboard(order, message)

    # then
    event = order.events.first()
    assert event.type == OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    assert event.parameters["message"] == message


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


def test_create_refunded_lines_order_lines(order_with_lines):
    # given
    order_lines = order_with_lines.lines.all()
    order_refund_lines = [
        OrderLineInfo(line=(line := order_lines[0]), quantity=2, variant=line.variant),
        OrderLineInfo(line=(line := order_lines[1]), quantity=1, variant=line.variant),
    ]
    fulfillment_refund_lines = []
    refund_data = RefundData(
        order_lines_to_refund=order_refund_lines,
        fulfillment_lines_to_refund=fulfillment_refund_lines,
    )

    # when
    lines = create_refunded_lines(
        order_with_lines,
        refund_data,
    )

    # then
    assert lines == {line.line.variant_id: line.quantity for line in order_refund_lines}


def test_create_refunded_lines_fulfillment_lines(fulfilled_order):
    # given
    fulfillment_lines = list(fulfilled_order.fulfillments.first().lines.all())
    order_refund_lines = []
    fulfillment_refund_lines = [
        FulfillmentLineData(
            line=fulfillment_lines[0],
            quantity=2,
        ),
        FulfillmentLineData(
            line=fulfillment_lines[1],
            quantity=1,
        ),
    ]
    refund_data = RefundData(
        order_lines_to_refund=order_refund_lines,
        fulfillment_lines_to_refund=fulfillment_refund_lines,
    )

    # when
    lines = create_refunded_lines(
        fulfilled_order,
        refund_data,
    )

    # then
    assert lines == {
        line.line.order_line.variant_id: line.quantity
        for line in fulfillment_refund_lines
    }


@patch("saleor.order.actions.gateway.refund")
@pytest.mark.parametrize("previous_refund_shipping_costs", [True, False])
def test_create_refunded_lines_previously_refunded_order_lines(
    _mocked_refund,
    order_with_lines,
    create_refund,
    previous_refund_shipping_costs,
):
    # given
    order_lines = order_with_lines.lines.all()
    previous_order_refund_lines = [
        OrderLineInfo(line=(line := order_lines[0]), quantity=1, variant=line.variant)
    ]
    create_refund(
        order_with_lines,
        order_lines=previous_order_refund_lines,
        refund_shipping_costs=previous_refund_shipping_costs,
    )
    current_order_refund_lines = [
        OrderLineInfo(line=(line := order_lines[0]), quantity=1, variant=line.variant),
        OrderLineInfo(line=(line := order_lines[1]), quantity=1, variant=line.variant),
    ]
    fulfillment_refund_lines = []
    refund_data = RefundData(
        order_lines_to_refund=current_order_refund_lines,
        fulfillment_lines_to_refund=fulfillment_refund_lines,
    )

    # when
    lines = create_refunded_lines(
        order_with_lines,
        refund_data,
    )

    # then
    order_refund_lines = [
        OrderLineInfo(line=cl.line, quantity=pl.quantity + cl.quantity)
        for pl, cl in zip_longest(
            previous_order_refund_lines,
            current_order_refund_lines,
            fillvalue=Mock(spec=OrderLineInfo, quantity=0),
        )
    ]
    assert lines == {line.line.variant_id: line.quantity for line in order_refund_lines}


@patch("saleor.order.actions.gateway.refund")
@pytest.mark.parametrize("previous_refund_shipping_costs", [True, False])
def test_create_refunded_lines_previously_refunded_fulfillment_lines(
    _mocked_refund,
    fulfilled_order,
    create_refund,
    previous_refund_shipping_costs,
):
    # given
    fulfillment_lines = list(
        chain.from_iterable(f.lines.all() for f in fulfilled_order.fulfillments.all())
    )
    previous_fulfillment_refund_lines = [
        FulfillmentLineData(line=fulfillment_lines[0], quantity=1)
    ]
    create_refund(
        fulfilled_order,
        fulfillment_lines=previous_fulfillment_refund_lines,
        refund_shipping_costs=previous_refund_shipping_costs,
    )
    order_refund_lines = []
    current_fulfillment_refund_lines = [
        FulfillmentLineData(
            line=fulfillment_lines[0],
            quantity=1,
        ),
        FulfillmentLineData(
            line=fulfillment_lines[1],
            quantity=1,
        ),
    ]
    refund_data = RefundData(
        order_lines_to_refund=order_refund_lines,
        fulfillment_lines_to_refund=current_fulfillment_refund_lines,
    )

    # when
    lines = create_refunded_lines(
        fulfilled_order,
        refund_data,
    )

    # then
    fulfillment_refund_lines = [
        FulfillmentLineData(line=cl.line, quantity=pl.quantity + cl.quantity)
        for pl, cl in zip_longest(
            previous_fulfillment_refund_lines,
            current_fulfillment_refund_lines,
            fillvalue=Mock(spec=FulfillmentLineData, quantity=0),
        )
    ]
    assert lines == {
        line.line.order_line.variant_id: line.quantity
        for line in fulfillment_refund_lines
    }
