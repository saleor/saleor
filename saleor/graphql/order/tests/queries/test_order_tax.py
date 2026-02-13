from decimal import Decimal
from functools import reduce
from operator import getitem
from unittest.mock import patch

import graphene
import pytest
from prices import TaxedMoney

from .....core.prices import quantize_price
from .....core.taxes import zero_taxed_money
from .....order import OrderStatus
from .....order.calculations import process_order_prices
from ....tests.utils import get_graphql_content


@pytest.mark.parametrize(
    ("field_on_order", "price_name"),
    [
        ("total", "total"),
        ("undiscounted_total", "undiscountedTotal"),
        ("shipping_price", "shippingPrice"),
    ],
)
def test_order_resolver_tax_recalculation(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    field_on_order,
    price_name,
    tax_configuration_flat_rates,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.total = zero_taxed_money(currency=order.currency)
    order.undiscounted_total = zero_taxed_money(currency=order.currency)
    order.shipping_price = zero_taxed_money(currency=order.currency)
    order.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    query = f"""
        query OrderPrices($id: ID!) {{
            order(id: $id) {{
                {price_name} {{ net {{ amount }} gross {{ amount }} }}
            }}
        }}
        """
    variables = {"id": order_id}

    current_tax_price = getattr(order, field_on_order)
    assert current_tax_price.net == current_tax_price.gross

    # when
    with patch(
        "saleor.graphql.order.dataloaders.process_order_prices",
        wraps=process_order_prices,
    ) as mocked_process_order_prices:
        response = staff_api_client.post_graphql(
            query,
            variables,
            permissions=[permission_manage_orders],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        data = content["data"]["order"]
        assert mocked_process_order_prices.called

    # then
    order.refresh_from_db()
    assert order.should_refresh_prices is False
    assert quantize_price(
        Decimal(data[price_name]["gross"]["amount"]), order.currency
    ) == quantize_price(getattr(order, field_on_order).gross.amount, order.currency)

    assert Decimal(data[price_name]["net"]["amount"]) == quantize_price(
        getattr(order, field_on_order).net.amount, order.currency
    )


@pytest.mark.parametrize(
    (
        "field_on_order_line",
        "price_name",
    ),
    [
        (
            "unit_price",
            "unitPrice",
        ),
        (
            "undiscounted_unit_price",
            "undiscountedUnitPrice",
        ),
        (
            "total_price",
            "totalPrice",
        ),
    ],
)
def test_order_line_resolver_tax_recalculation(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    field_on_order_line,
    price_name,
    tax_configuration_flat_rates,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save()

    order.lines.last().delete()
    assert order.lines.count() == 1

    order_line = order.lines.first()
    order_line.unit_price = zero_taxed_money(currency=order.currency)
    order_line.undiscounted_unit_price = zero_taxed_money(currency=order.currency)
    order_line.total_price = zero_taxed_money(currency=order.currency)
    order_line.save()

    taxed_price: TaxedMoney = getattr(order_line, field_on_order_line)
    assert taxed_price.net == taxed_price.gross

    order_id = graphene.Node.to_global_id("Order", order.id)

    query = f"""
        query OrderLinePrices($id: ID!) {{
            order(id: $id) {{
                lines {{
                    {price_name} {{ net {{ amount }} gross {{ amount }} }}
                }}
            }}
        }}
        """
    variables = {"id": order_id}

    # when
    with patch(
        "saleor.graphql.order.dataloaders.process_order_prices",
        wraps=process_order_prices,
    ) as mocked_process_order_prices:
        response = staff_api_client.post_graphql(
            query,
            variables,
            permissions=[permission_manage_orders],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        data = content["data"]["order"]["lines"][0]
        assert mocked_process_order_prices.called
    # then
    order.refresh_from_db()
    assert order.should_refresh_prices is False
    order_line.refresh_from_db()

    assert quantize_price(
        Decimal(data[price_name]["net"]["amount"]), order.currency
    ) == quantize_price(
        getattr(order_line, field_on_order_line).net.amount, order.currency
    )
    assert quantize_price(
        Decimal(data[price_name]["gross"]["amount"]), order.currency
    ) == quantize_price(
        getattr(order_line, field_on_order_line).gross.amount, order.currency
    )


ORDER_SHIPPING_TAX_RATE_QUERY = """
query OrderShippingTaxRate($id: ID!) {
    order(id: $id) {
        shippingTaxRate
    }
}
"""

ORDER_LINE_TAX_RATE_QUERY = """
query OrderLineTaxRate($id: ID!) {
    order(id: $id) {
        lines {
            taxRate
        }
    }
}
"""


@pytest.mark.parametrize(
    ("query", "path"),
    [
        (ORDER_SHIPPING_TAX_RATE_QUERY, ["shippingTaxRate"]),
        (ORDER_LINE_TAX_RATE_QUERY, ["lines", 0, "taxRate"]),
    ],
)
def test_order_tax_rate_resolver_tax_recalculation(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    query,
    path,
    tax_configuration_flat_rates,
):
    # given
    expected_tax_rate = Decimal("0.23")

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.shipping_tax_rate = Decimal("0.0")
    order.save()

    order.lines.last().delete()
    assert order.lines.count() == 1
    order_line = order.lines.first()
    order_line.tax_rate = Decimal("0.0")
    order_line.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {"id": order_id}

    # when
    with patch(
        "saleor.graphql.order.dataloaders.process_order_prices",
        wraps=process_order_prices,
    ) as mocked_process_order_prices:
        response = staff_api_client.post_graphql(
            query,
            variables,
            permissions=[permission_manage_orders],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        data = content["data"]["order"]
        assert mocked_process_order_prices.called
    # then
    assert str(reduce(getitem, path, data)) == str(expected_tax_rate)
