from decimal import Decimal
from typing import Literal, Union
from unittest.mock import Mock, patch, sentinel

import pytest
from prices import Money, TaxedMoney

from ...core.prices import quantize_price
from ...core.taxes import TaxData, TaxError, TaxLineData, zero_taxed_money
from .. import OrderStatus, calculations
from ..interface import OrderTaxedPricesData


@pytest.fixture
def order_with_lines(order_with_lines):
    order_with_lines.status = OrderStatus.UNCONFIRMED
    return order_with_lines


@pytest.fixture
def order_lines(order_with_lines):
    return order_with_lines.lines.all()


@pytest.fixture
def tax_data(order_with_lines, order_lines):
    order = order_with_lines
    tax_rate = Decimal("1.23")
    shipping_tax_rate = Decimal("1.17")
    lines = []
    for i, line in enumerate(order_lines, start=1):
        line_tax_rate = tax_rate + Decimal(f"{i}") / 100
        lines.append(
            TaxLineData(
                total_net_amount=line.total_price.net.amount,
                total_gross_amount=line.total_price.net.amount * line_tax_rate,
                tax_rate=line_tax_rate,
            )
        )

    shipping_net = order.shipping_price.net.amount
    shipping_gross = order.shipping_price.net.amount * shipping_tax_rate
    return TaxData(
        shipping_price_net_amount=shipping_net,
        shipping_price_gross_amount=shipping_gross,
        shipping_tax_rate=shipping_tax_rate,
        lines=lines,
    )


def create_taxed_money(net: Decimal, gross: Decimal, currency: str) -> TaxedMoney:
    return TaxedMoney(net=Money(net, currency), gross=Money(gross, currency))


def create_order_taxed_prices_data(
    net: Decimal, gross: Decimal, currency: str
) -> OrderTaxedPricesData:
    return OrderTaxedPricesData(
        undiscounted_price=create_taxed_money(net, gross, currency),
        price_with_discounts=create_taxed_money(net, gross, currency),
    )


def test_recalculate_order_prices(order_with_lines, order_lines, tax_data):
    # given
    order = order_with_lines
    currency = order.currency
    lines = list(order_lines)
    lines.append(
        Mock(
            variant=None,
            total_price=create_taxed_money(
                net=Decimal("33.33"),
                gross=Decimal("44.44"),
                currency=order.currency,
            ),
        )
    )

    total_prices = [
        get_order_priced_taxes_data(line, "total", currency) for line in tax_data.lines
    ]
    unit_prices = []
    for line, total_price in zip(lines, total_prices):
        unit_prices.append(
            OrderTaxedPricesData(
                undiscounted_price=total_price.undiscounted_price / line.quantity,
                price_with_discounts=total_price.price_with_discounts / line.quantity,
            )
        )
    tax_rates = [line.tax_rate for line in tax_data.lines]
    shipping_tax_rate = tax_data.shipping_tax_rate
    shipping = get_taxed_money(tax_data, "shipping_price", currency)
    subtotal = sum(
        (get_taxed_money(line, "total", currency) for line in tax_data.lines),
        zero_taxed_money(order.currency),
    ) + create_taxed_money(Decimal("33.33"), Decimal("44.44"), order.currency)
    total = shipping + subtotal

    manager = Mock(
        calculate_order_line_unit=Mock(side_effect=unit_prices),
        calculate_order_line_total=Mock(side_effect=total_prices),
        get_order_shipping_tax_rate=Mock(return_value=shipping_tax_rate),
        get_order_line_tax_rate=Mock(side_effect=tax_rates),
        calculate_order_shipping=Mock(return_value=shipping),
    )

    # when
    calculations._recalculate_order_prices(manager, order, lines)

    # then
    assert order.total == total
    assert order.shipping_price == shipping
    assert order.shipping_tax_rate == shipping_tax_rate

    for line_unit, line_total, tax_rate, line in zip(
        unit_prices, total_prices, tax_rates, lines
    ):
        assert line.unit_price == line_unit.price_with_discounts
        assert line.undiscounted_unit_price == line_unit.undiscounted_price
        assert line.total_price == line_total.price_with_discounts
        assert line.undiscounted_total_price == line_total.undiscounted_price
        assert tax_rate == line.tax_rate


@pytest.mark.parametrize(
    "mocked_method_name",
    [
        "calculate_order_line_unit",
        "calculate_order_line_total",
        "get_order_line_tax_rate",
        "calculate_order_shipping",
        "get_order_shipping_tax_rate",
    ],
)
def test_recalculate_order_prices_tax_error(
    order_with_lines, order_lines, mocked_method_name
):
    # given
    order = order_with_lines
    lines = order_lines
    zero_money = zero_taxed_money(order.currency)
    zero_prices = OrderTaxedPricesData(
        undiscounted_price=zero_money,
        price_with_discounts=zero_money,
    )
    manager_methods = {
        "calculate_order_line_unit": Mock(return_value=zero_prices),
        "calculate_order_line_total": Mock(return_value=zero_prices),
        "get_order_shipping_tax_rate": Mock(return_value=Decimal("0.00")),
        "get_order_line_tax_rate": Mock(return_value=Decimal("0.00")),
        "calculate_order_shipping": Mock(return_value=zero_money),
        mocked_method_name: Mock(side_effect=TaxError()),
    }
    manager = Mock(**manager_methods)

    # when
    calculations._recalculate_order_prices(manager, order, lines)

    # then
    # no exception is raised


def test_recalculate_order_prices_tax_error_line_prices(
    order_with_lines, order_lines, tax_data
):
    # given
    order = order_with_lines
    currency = order.currency
    lines = list(order_lines)
    lines.append(
        Mock(
            variant=None,
            total_price=create_taxed_money(
                net=Decimal("33.33"),
                gross=Decimal("44.44"),
                currency=currency,
            ),
        )
    )
    error_line = order_lines[0]
    old_line_unit_price = error_line.unit_price
    old_line_undiscounted_unit_price = error_line.undiscounted_unit_price
    old_line_total_price = error_line.total_price
    old_line_undiscounted_total_price = error_line.undiscounted_total_price
    old_line_tax_rate = error_line.tax_rate

    total_prices = [
        get_order_priced_taxes_data(line, "total", currency) for line in tax_data.lines
    ]
    unit_prices = []
    for line, total_price in zip(lines, total_prices):
        unit_prices.append(
            OrderTaxedPricesData(
                undiscounted_price=total_price.undiscounted_price / line.quantity,
                price_with_discounts=total_price.price_with_discounts / line.quantity,
            )
        )
    tax_rates = [line.tax_rate for line in tax_data.lines]
    shipping_tax_rate = tax_data.shipping_tax_rate
    shipping = get_taxed_money(tax_data, "shipping_price", currency)

    subtotal = (
        error_line.total_price
        + sum(
            [get_taxed_money(line, "total", currency) for line in tax_data.lines[1:]],
            zero_taxed_money(currency),
        )
        + create_taxed_money(Decimal("33.33"), Decimal("44.44"), currency)
    )
    total = shipping + subtotal

    manager = Mock(
        calculate_order_line_unit=Mock(side_effect=[TaxError] + unit_prices[1:]),
        calculate_order_line_total=Mock(side_effect=total_prices[1:]),
        get_order_shipping_tax_rate=Mock(return_value=shipping_tax_rate),
        get_order_line_tax_rate=Mock(side_effect=tax_rates[1:]),
        calculate_order_shipping=Mock(return_value=shipping),
    )

    # when
    calculations._recalculate_order_prices(manager, order, lines)

    # then
    assert order.total == total
    assert order.shipping_price == shipping
    assert order.shipping_tax_rate == shipping_tax_rate

    assert old_line_unit_price == error_line.unit_price
    assert old_line_undiscounted_unit_price == error_line.undiscounted_unit_price
    assert old_line_total_price == error_line.total_price
    assert old_line_undiscounted_total_price == error_line.undiscounted_total_price
    assert old_line_tax_rate == error_line.tax_rate

    for line_unit, line_total, tax_rate, line in list(
        zip(unit_prices, total_prices, tax_rates, lines)
    )[1:]:
        assert line.unit_price == line_unit.price_with_discounts
        assert line.undiscounted_unit_price == line_unit.undiscounted_price
        assert line.total_price == line_total.price_with_discounts
        assert line.undiscounted_total_price == line_total.undiscounted_price
        assert tax_rate == line.tax_rate


def test_recalculate_order_prices_tax_error_shipping_price(
    order_with_lines, order_lines, tax_data
):
    # given
    order = order_with_lines
    currency = order.currency
    lines = list(order_lines)
    lines.append(
        Mock(
            variant=None,
            total_price=create_taxed_money(
                net=Decimal("33.33"),
                gross=Decimal("44.44"),
                currency=currency,
            ),
        )
    )
    old_shipping_price = order.shipping_price
    old_shipping_tax_rate = order.shipping_tax_rate

    total_prices = [
        get_order_priced_taxes_data(line, "total", currency) for line in tax_data.lines
    ]
    unit_prices = []
    for line, total_price in zip(lines, total_prices):
        unit_prices.append(
            OrderTaxedPricesData(
                undiscounted_price=total_price.undiscounted_price / line.quantity,
                price_with_discounts=total_price.price_with_discounts / line.quantity,
            )
        )
    tax_rates = [line.tax_rate for line in tax_data.lines]
    shipping_tax_rate = tax_data.shipping_tax_rate

    subtotal = sum(
        [get_taxed_money(line, "total", currency) for line in tax_data.lines],
        zero_taxed_money(currency),
    ) + create_taxed_money(Decimal("33.33"), Decimal("44.44"), currency)

    manager = Mock(
        calculate_order_line_unit=Mock(side_effect=unit_prices),
        calculate_order_line_total=Mock(side_effect=total_prices),
        get_order_shipping_tax_rate=Mock(return_value=shipping_tax_rate),
        get_order_line_tax_rate=Mock(side_effect=tax_rates),
        calculate_order_shipping=Mock(side_effect=TaxError),
    )

    # when
    calculations._recalculate_order_prices(manager, order, lines)

    # then
    assert order.total == subtotal + old_shipping_price
    assert order.shipping_price == old_shipping_price
    assert order.shipping_tax_rate == old_shipping_tax_rate

    for line_unit, line_total, tax_rate, line in zip(
        unit_prices, total_prices, tax_rates, lines
    ):
        assert line.unit_price == line_unit.price_with_discounts
        assert line.undiscounted_unit_price == line_unit.undiscounted_price
        assert line.total_price == line_total.price_with_discounts
        assert line.undiscounted_total_price == line_total.undiscounted_price
        assert tax_rate == line.tax_rate


def test_apply_tax_data(order_with_lines, order_lines, tax_data):
    # given
    order = order_with_lines
    lines = order_lines

    # when
    calculations._apply_tax_data(order, [line for line in lines], tax_data)

    # then
    assert str(order.shipping_price.net.amount) == str(
        tax_data.shipping_price_net_amount
    )
    assert str(order.shipping_price.gross.amount) == str(
        tax_data.shipping_price_gross_amount
    )

    for line, tax_line in zip(lines, tax_data.lines):
        assert str(line.total_price.net.amount) == str(tax_line.total_net_amount)
        assert str(line.total_price.gross.amount) == str(tax_line.total_gross_amount)


@pytest.fixture
def manager_with_mocked_plugins_calculations(
    plugins_manager, tax_data, order_with_lines
):
    currency = order_with_lines.currency
    plugins_manager.get_order_shipping_tax_rate = Mock(
        return_value=tax_data.shipping_tax_rate
    )
    plugins_manager.calculate_order_shipping = Mock(
        return_value=get_taxed_money(tax_data, "shipping_price", currency)
    )

    total_prices = [
        get_order_priced_taxes_data(line, "total", currency) for line in tax_data.lines
    ]
    plugins_manager.calculate_order_line_total = Mock(side_effect=total_prices)

    unit_prices = []
    for line, total_price in zip(order_with_lines.lines.all(), total_prices):
        unit_price = quantize_price(
            total_price.price_with_discounts / line.quantity, currency
        )
        unit_prices.append(
            OrderTaxedPricesData(
                undiscounted_price=unit_price,
                price_with_discounts=unit_price,
            )
        )

    plugins_manager.calculate_order_line_unit = Mock(side_effect=unit_prices)
    plugins_manager.get_order_line_tax_rate = Mock(
        side_effect=[line.tax_rate for line in tax_data.lines]
    )
    return plugins_manager


@pytest.fixture
def fetch_kwargs(order_with_lines, plugins_manager):
    return {
        "order": order_with_lines,
        "manager": plugins_manager,
        "force_update": True,
    }


@pytest.fixture
def fetch_kwargs_with_lines(order_with_lines, order_lines, plugins_manager):
    return {
        "order": order_with_lines,
        "lines": order_lines,
        "manager": plugins_manager,
    }


def get_taxed_money(
    obj: Union[TaxData, TaxLineData],
    attr: Literal["unit", "total", "subtotal", "shipping_price"],
    currency: str,
) -> TaxedMoney:
    return TaxedMoney(
        Money(getattr(obj, f"{attr}_net_amount"), currency),
        Money(getattr(obj, f"{attr}_gross_amount"), currency),
    )


def get_order_priced_taxes_data(
    obj: Union[TaxData, TaxLineData],
    attr: Literal["unit", "total", "subtotal", "shipping_price"],
    currency: str,
) -> OrderTaxedPricesData:
    return OrderTaxedPricesData(
        undiscounted_price=get_taxed_money(obj, attr, currency),
        price_with_discounts=get_taxed_money(obj, attr, currency),
    )


def test_fetch_order_prices_if_expired_plugins(
    plugins_manager,
    fetch_kwargs,
    order_with_lines,
    tax_data,
):
    # given
    currency = order_with_lines.currency
    total_prices = [
        get_order_priced_taxes_data(line, "total", currency) for line in tax_data.lines
    ]
    subtotal = zero_taxed_money(currency)
    unit_prices = []
    for line, total_price in zip(order_with_lines.lines.all(), total_prices):
        subtotal += total_price.price_with_discounts
        unit_prices.append(
            OrderTaxedPricesData(
                undiscounted_price=total_price.undiscounted_price / line.quantity,
                price_with_discounts=total_price.price_with_discounts / line.quantity,
            )
        )
    tax_rates = [line.tax_rate for line in tax_data.lines]
    shipping_tax_rate = tax_data.shipping_tax_rate
    shipping = get_taxed_money(tax_data, "shipping_price", currency)

    total = subtotal + shipping

    plugins_manager.calculate_order_line_unit = Mock(side_effect=unit_prices)
    plugins_manager.calculate_order_line_total = Mock(side_effect=total_prices)
    plugins_manager.get_order_line_tax_rate = Mock(side_effect=tax_rates)
    plugins_manager.calculate_order_shipping = Mock(return_value=shipping)
    plugins_manager.get_order_shipping_tax_rate = Mock(return_value=shipping_tax_rate)
    plugins_manager.get_taxes_for_order = Mock(return_value=None)

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.shipping_price == get_taxed_money(
        tax_data, "shipping_price", currency
    )
    assert order_with_lines.shipping_tax_rate == tax_data.shipping_tax_rate
    assert order_with_lines.total == total
    for order_line, tax_line, unit_price in zip(
        order_with_lines.lines.all(), tax_data.lines, unit_prices
    ):
        assert order_line.unit_price == unit_price.price_with_discounts
        assert order_line.total_price == get_taxed_money(tax_line, "total", currency)
        assert order_line.tax_rate == tax_line.tax_rate


def test_fetch_order_prices_if_expired_webhooks_success(
    plugins_manager,
    fetch_kwargs,
    order_with_lines,
    tax_data,
):
    # given
    currency = order_with_lines.currency
    plugins_manager.get_taxes_for_order = Mock(return_value=tax_data)

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    shipping_price = get_taxed_money(tax_data, "shipping_price", currency)
    assert order_with_lines.shipping_price == shipping_price
    assert order_with_lines.shipping_tax_rate == tax_data.shipping_tax_rate / 100
    subtotal = zero_taxed_money(currency)
    for order_line, tax_line in zip(order_with_lines.lines.all(), tax_data.lines):
        line_total = get_taxed_money(tax_line, "total", currency)
        subtotal += line_total
        assert order_line.total_price == line_total
        assert order_line.unit_price == line_total / order_line.quantity
        assert order_line.tax_rate == tax_line.tax_rate / 100
    assert order_with_lines.total == subtotal + shipping_price


def test_fetch_order_prices_if_expired_recalculate_all_prices(
    plugins_manager,
    fetch_kwargs,
    order_with_lines,
    tax_data,
):
    # given
    currency = order_with_lines.currency
    discount_amount = Decimal("3.00")
    order_with_lines.discounts.create(
        value=discount_amount,
        amount_value=discount_amount,
        currency=order_with_lines.currency,
    )
    order_with_lines.total_net_amount = Decimal("0.00")
    order_with_lines.total_gross_amount = Decimal("0.00")
    order_with_lines.undiscounted_total_net_amount = Decimal("0.00")
    order_with_lines.undiscounted_total_gross_amount = Decimal("0.00")
    order_with_lines.save()
    plugins_manager.get_taxes_for_order = Mock(return_value=tax_data)

    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    order_with_lines.refresh_from_db()
    shipping_price = get_taxed_money(tax_data, "shipping_price", currency)
    assert order_with_lines.shipping_price == shipping_price
    assert order_with_lines.shipping_tax_rate == tax_data.shipping_tax_rate / 100
    subtotal = zero_taxed_money(currency)
    for order_line, tax_line in zip(order_with_lines.lines.all(), tax_data.lines):
        line_total = get_taxed_money(tax_line, "total", currency)
        subtotal += line_total
        assert order_line.total_price == line_total
        assert order_line.unit_price == line_total / order_line.quantity
        assert order_line.tax_rate == tax_line.tax_rate / 100

    assert order_with_lines.undiscounted_total == subtotal + shipping_price
    assert order_with_lines.total == subtotal + shipping_price - create_taxed_money(
        discount_amount, discount_amount, order_with_lines.currency
    )


def test_fetch_order_prices_if_expired_prefetch(fetch_kwargs, order_lines):
    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs)

    # then
    assert all(line._state.fields_cache for line in order_lines)


def test_fetch_order_prices_if_expired_prefetch_with_lines(
    fetch_kwargs_with_lines, order_lines
):
    # when
    calculations.fetch_order_prices_if_expired(**fetch_kwargs_with_lines)

    # then
    assert all(line._state.fields_cache for line in order_lines)


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_line_unit(mocked_fetch_order_prices_if_expired):
    # given
    expected_line_unit_price = create_taxed_money(
        Decimal("1234.0000"), Decimal("1234.0000"), "USD"
    )
    expected_line_undiscounted_unit_price = create_taxed_money(
        Decimal("5678.0000"), Decimal("5678.0000"), "USD"
    )

    order = Mock(currency="USD")
    order_line = Mock(
        pk=1,
        unit_price=expected_line_unit_price,
        undiscounted_unit_price=expected_line_undiscounted_unit_price,
    )
    mocked_fetch_order_prices_if_expired.return_value = (Mock(), [order_line])

    # when
    line_unit_price = calculations.order_line_unit(order, order_line, Mock())

    # then
    assert line_unit_price == OrderTaxedPricesData(
        undiscounted_price=expected_line_undiscounted_unit_price,
        price_with_discounts=expected_line_unit_price,
    )


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_line_total(mocked_fetch_order_prices_if_expired):
    # given
    expected_line_total_price = create_taxed_money(
        Decimal("1234.0000"), Decimal("1234.0000"), "USD"
    )
    expected_line_undiscounted_total_price = create_taxed_money(
        Decimal("5678.0000"), Decimal("5678.0000"), "USD"
    )

    order = Mock(currency="USD")
    order_line = Mock(
        pk=1,
        total_price=expected_line_total_price,
        undiscounted_total_price=expected_line_undiscounted_total_price,
    )
    mocked_fetch_order_prices_if_expired.return_value = (Mock(), [order_line])

    # when
    line_total_price = calculations.order_line_total(order, order_line, Mock())

    # then
    assert line_total_price == OrderTaxedPricesData(
        undiscounted_price=expected_line_undiscounted_total_price,
        price_with_discounts=expected_line_total_price,
    )


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_line_tax_rate(mocked_fetch_order_prices_if_expired):
    # given
    expected_line_tax_rate = sentinel.TAX_RATE

    order_line = Mock(pk=1, tax_rate=expected_line_tax_rate)
    mocked_fetch_order_prices_if_expired.return_value = (Mock(), [order_line])

    # when
    line_tax_rate = calculations.order_line_tax_rate(Mock(), order_line, Mock())

    # then
    assert line_tax_rate == expected_line_tax_rate


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_shipping(mocked_fetch_order_prices_if_expired):
    # given
    expected_shipping_price = Decimal("1234.0000")

    order = Mock(shipping_price=expected_shipping_price, currency="USD")
    mocked_fetch_order_prices_if_expired.return_value = (order, Mock())

    # when
    shipping_price = calculations.order_shipping(order, Mock())

    # then
    assert shipping_price == quantize_price(expected_shipping_price, order.currency)


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_shipping_tax_rate(mocked_fetch_order_prices_if_expired):
    # given
    expected_shipping_tax_rate = sentinel.SHIPPING_TAX_RATE

    order = Mock(shipping_tax_rate=expected_shipping_tax_rate)
    mocked_fetch_order_prices_if_expired.return_value = (order, Mock())

    # when
    shipping_tax_rate = calculations.order_shipping_tax_rate(order, Mock())

    # then
    assert shipping_tax_rate == expected_shipping_tax_rate


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_total(mocked_fetch_order_prices_if_expired):
    # given
    expected_total = Decimal("1234.0000")

    order = Mock(total=expected_total, currency="USD")
    mocked_fetch_order_prices_if_expired.return_value = (order, Mock())

    # when
    total = calculations.order_total(order, Mock())

    # then
    assert total == quantize_price(expected_total, order.currency)


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_order_undiscounted_total(mocked_fetch_order_prices_if_expired):
    # given
    expected_undiscounted_total = Decimal("1234.0000")

    order = Mock(undiscounted_total=expected_undiscounted_total, currency="USD")
    mocked_fetch_order_prices_if_expired.return_value = (order, Mock())

    # when
    undiscounted_total = calculations.order_undiscounted_total(order, Mock())

    # then
    assert undiscounted_total == quantize_price(
        expected_undiscounted_total, order.currency
    )
