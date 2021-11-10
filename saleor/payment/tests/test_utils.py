from itertools import chain, zip_longest
from typing import List
from unittest.mock import Mock, patch

import pytest

from ...order import FulfillmentLineData, OrderLineData
from ...order.actions import create_refund_fulfillment
from ...order.interface import OrderPaymentAction
from ...order.models import Order
from ...plugins.manager import get_plugins_manager
from ..utils import SHIPPING_PAYMENT_LINE_ID, create_refund_data


@pytest.fixture
def create_refund_fulfillment_helper(payment_dummy):
    def factory(
        order: Order,
        order_lines: List[OrderLineData] = None,
        fulfillment_lines: List[FulfillmentLineData] = None,
        include_shipping_costs: bool = False,
    ):
        with patch("saleor.order.actions.gateway.refund"):
            return create_refund_fulfillment(
                user=None,
                app=None,
                order=order,
                payments=[
                    OrderPaymentAction(
                        payment=payment_dummy, amount=order.total_gross_amount
                    )
                ],
                order_lines_to_refund=order_lines or [],
                fulfillment_lines_to_refund=fulfillment_lines or [],
                manager=get_plugins_manager(),
                include_shipping_costs=include_shipping_costs,
            )

    return factory


@pytest.mark.parametrize(
    ["include_shipping_costs", "shipping_line_quantity"], [(True, 0), (False, 1)]
)
def test_create_refund_data_order_lines(
    order_with_lines, include_shipping_costs, shipping_line_quantity
):
    # given
    order_lines = order_with_lines.lines.all()
    order_refund_lines = [
        OrderLineData(line=(line := order_lines[0]), quantity=2, variant=line.variant),
        OrderLineData(line=(line := order_lines[1]), quantity=1, variant=line.variant),
    ]
    fulfillment_refund_lines = []

    # when
    refund_data = create_refund_data(
        order_with_lines,
        order_refund_lines,
        fulfillment_refund_lines,
        include_shipping_costs,
    )

    # then
    assert refund_data == {
        **{
            line.variant_id: line.quantity - refund_line.quantity
            for line, refund_line in zip(order_lines, order_refund_lines)
        },
        SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity,
    }


@pytest.mark.parametrize(
    ["include_shipping_costs", "shipping_line_quantity"], [(True, 0), (False, 1)]
)
def test_create_refund_data_fulfillment_lines(
    fulfilled_order, include_shipping_costs, shipping_line_quantity
):
    # given
    fulfillment_lines = fulfilled_order.fulfillments.first().lines.all()
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

    # when
    refund_data = create_refund_data(
        fulfilled_order,
        order_refund_lines,
        fulfillment_refund_lines,
        include_shipping_costs,
    )

    # then
    assert refund_data == {
        **{
            line.order_line.variant_id: line.quantity - refund_line.quantity
            for line, refund_line in zip(fulfillment_lines, fulfillment_refund_lines)
        },
        SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity,
    }


@pytest.mark.parametrize(
    ["include_shipping_costs", "shipping_line_quantity"], [(True, 0), (False, 1)]
)
def test_create_refund_data_shipping_only(
    order, include_shipping_costs, shipping_line_quantity
):
    # given
    order_refund_lines = []
    fulfillment_refund_lines = []

    # when
    refund_data = create_refund_data(
        order, order_refund_lines, fulfillment_refund_lines, include_shipping_costs
    )

    # then
    assert refund_data == {SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity}


@patch("saleor.order.actions.gateway.refund")
@pytest.mark.parametrize(
    [
        "previously_included_shipping_costs",
        "currently_included_shipping_costs",
        "shipping_line_quantity",
    ],
    [
        (True, True, 0),
        (True, False, 0),
        (False, True, 0),
        (False, False, 1),
    ],
)
def test_create_refund_data_previously_refunded_order_lines(
    _mocked_refund,
    order_with_lines,
    create_refund_fulfillment_helper,
    previously_included_shipping_costs,
    currently_included_shipping_costs,
    shipping_line_quantity,
):
    # given
    order_lines = order_with_lines.lines.all()
    previous_order_refund_lines = [
        OrderLineData(line=(line := order_lines[0]), quantity=1, variant=line.variant)
    ]
    create_refund_fulfillment_helper(
        order_with_lines,
        order_lines=previous_order_refund_lines,
        include_shipping_costs=previously_included_shipping_costs,
    )
    current_order_refund_lines = [
        OrderLineData(line=(line := order_lines[0]), quantity=1, variant=line.variant),
        OrderLineData(line=(line := order_lines[1]), quantity=1, variant=line.variant),
    ]
    fulfillment_refund_lines = []

    # when
    refund_data = create_refund_data(
        order_with_lines,
        current_order_refund_lines,
        fulfillment_refund_lines,
        currently_included_shipping_costs,
    )

    # then
    order_refund_lines = [
        OrderLineData(line=cl.line, quantity=pl.quantity + cl.quantity)
        for pl, cl in zip_longest(
            previous_order_refund_lines,
            current_order_refund_lines,
            fillvalue=Mock(spec=OrderLineData, quantity=0),
        )
    ]
    assert refund_data == {
        **{
            line.variant_id: line.quantity - refund_line.quantity
            for line, refund_line in zip(order_lines, order_refund_lines)
        },
        SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity,
    }


@patch("saleor.order.actions.gateway.refund")
@pytest.mark.parametrize(
    [
        "previously_included_shipping_costs",
        "currently_included_shipping_costs",
        "shipping_line_quantity",
    ],
    [
        (True, True, 0),
        (True, False, 0),
        (False, True, 0),
        (False, False, 1),
    ],
)
def test_create_refund_data_previously_refunded_fulfillment_lines(
    _mocked_refund,
    fulfilled_order,
    create_refund_fulfillment_helper,
    previously_included_shipping_costs,
    currently_included_shipping_costs,
    shipping_line_quantity,
):
    # given
    fulfillment_lines = list(
        chain.from_iterable(f.lines.all() for f in fulfilled_order.fulfillments.all())
    )
    previous_fulfillment_refund_lines = [
        FulfillmentLineData(line=fulfillment_lines[0], quantity=1)
    ]
    create_refund_fulfillment_helper(
        fulfilled_order,
        fulfillment_lines=previous_fulfillment_refund_lines,
        include_shipping_costs=previously_included_shipping_costs,
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

    # when
    refund_data = create_refund_data(
        fulfilled_order,
        order_refund_lines,
        current_fulfillment_refund_lines,
        currently_included_shipping_costs,
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
    assert refund_data == {
        **{
            line.variant_id: line.quantity - refund_line.quantity
            for line, refund_line in zip(
                fulfilled_order.lines.all(), fulfillment_refund_lines
            )
        },
        SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity,
    }


@patch("saleor.order.actions.gateway.refund")
@pytest.mark.parametrize(
    [
        "previously_included_shipping_costs",
        "currently_included_shipping_costs",
        "shipping_line_quantity",
    ],
    [
        (True, True, 0),
        (True, False, 0),
        (False, True, 0),
        (False, False, 1),
    ],
)
def test_create_refund_data_previously_refunded_shipping_only(
    _mocked_refund,
    order,
    create_refund_fulfillment_helper,
    previously_included_shipping_costs,
    currently_included_shipping_costs,
    shipping_line_quantity,
):
    # given
    create_refund_fulfillment_helper(
        order, include_shipping_costs=previously_included_shipping_costs
    )
    order_refund_lines = []
    fulfillment_refund_lines = []

    # when
    refund_data = create_refund_data(
        order,
        order_refund_lines,
        fulfillment_refund_lines,
        currently_included_shipping_costs,
    )

    # then
    assert refund_data == {SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity}
