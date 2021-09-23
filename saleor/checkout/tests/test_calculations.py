from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from saleor.checkout.calculations import (
    _apply_tax_data,
    _get_tax_data_from_plugins,
    fetch_checkout_prices_if_expired,
)
from saleor.checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from saleor.checkout.models import Checkout
from saleor.core.taxes import TaxData, TaxError, TaxLineData
from saleor.plugins.manager import get_plugins_manager


def test_apply_tax_data(checkout: Checkout):
    # given
    net = Decimal("10.00")
    gross = Decimal("12.30")
    tax_data = TaxData(
        currency=checkout.currency,
        shipping_price_net_amount=checkout.shipping_price.net.amount + net,
        shipping_price_gross_amount=checkout.shipping_price.gross.amount + gross,
        subtotal_net_amount=checkout.subtotal.net.amount + net,
        subtotal_gross_amount=checkout.subtotal.gross.amount + gross,
        total_net_amount=checkout.shipping_price.net.amount + net,
        total_gross_amount=checkout.shipping_price.gross.amount + gross,
        lines=[
            TaxLineData(
                id=i,
                currency=checkout.currency,
                unit_net_amount=line.unit_price.net.amount,
                unit_gross_amount=line.unit_price.gross.amount,
                total_net_amount=line.total_price.net.amount,
                total_gross_amount=line.total_price.gross.amount,
            )
            for i, line in enumerate(checkout.lines.all())
        ],
    )

    # when
    _apply_tax_data(checkout, tax_data)

    # then
    assert checkout.total.net.amount == tax_data.total_net_amount
    assert checkout.total.gross.amount == tax_data.total_gross_amount

    assert checkout.subtotal.net.amount == tax_data.subtotal_net_amount
    assert checkout.subtotal.gross.amount == tax_data.subtotal_gross_amount

    assert checkout.shipping_price.net.amount == tax_data.shipping_price_net_amount
    assert checkout.shipping_price.gross.amount == tax_data.shipping_price_gross_amount

    for line, tax_line in zip(checkout.lines.all(), tax_data.lines):
        assert line.unit_price.net.amout == tax_line.unit_net_amount
        assert line.unit_price.gross.amout == tax_line.unit_gross_amount

        assert line.total_price.net.amout == tax_line.total_net_amount
        assert line.total_price.gross.amout == tax_line.total_gross_amount


@pytest.fixture
def manager():
    return get_plugins_manager()


@pytest.fixture
def fetch_kwargs(checkout_with_items, manager):
    lines = fetch_checkout_lines(checkout_with_items)
    discounts = []
    return {
        "checkout_info": fetch_checkout_info(
            checkout_with_items, lines, discounts, manager
        ),
        "manager": manager,
        "lines": lines,
        "address": checkout_with_items.shipping_address
        or checkout_with_items.billing_address,
        "discounts": discounts,
    }


PLUGINS_TAX_DATA = Mock(spec=TaxData)
WEBHOOKS_TAX_DATA = Mock(spec=TaxData)


@freeze_time("2020-12-12 12:00:00")
@patch("saleor.checkout.calculations._get_tax_data_from_plugins")
@patch("saleor.checkout.calculations._apply_tax_data")
@pytest.mark.parametrize(
    ["plugins_tax_data", "webhooks_tax_data", "expected_tax_data"],
    [
        (PLUGINS_TAX_DATA, WEBHOOKS_TAX_DATA, WEBHOOKS_TAX_DATA),
        (None, WEBHOOKS_TAX_DATA, WEBHOOKS_TAX_DATA),
        (PLUGINS_TAX_DATA, None, PLUGINS_TAX_DATA),
    ],
)
def test_fetch_checkout_prices_if_expired(
    mocked_apply_tax_data,
    mocked_get_tax_data_from_plugins,
    checkout_with_items,
    plugins_tax_data,
    webhooks_tax_data,
    expected_tax_data,
    fetch_kwargs,
    manager,
):
    # given
    mocked_get_tax_data_from_plugins.return_value = plugins_tax_data
    mocked_get_taxes_for_checkout = Mock(return_value=webhooks_tax_data)
    manager.get_taxes_for_checkout = mocked_get_taxes_for_checkout

    # when
    fetch_checkout_prices_if_expired(**fetch_kwargs)

    # then
    mocked_get_tax_data_from_plugins.assert_called_once()
    mocked_get_taxes_for_checkout.assert_called_once()
    mocked_apply_tax_data.assert_called_once_with(
        checkout_with_items, expected_tax_data
    )


@freeze_time("2020-12-12 12:00:00")
@patch("saleor.checkout.calculations._get_tax_data_from_plugins")
@patch("saleor.checkout.calculations._apply_tax_data")
def test_fetch_checkout_prices_if_expired_no_response(
    mocked_apply_tax_data,
    mocked_get_tax_data_from_plugins,
    fetch_kwargs,
    manager,
):
    # given
    mocked_get_tax_data_from_plugins.return_value = None
    mocked_get_taxes_for_checkout = Mock(return_value=None)
    manager.get_taxes_for_checkout = mocked_get_taxes_for_checkout

    # when
    fetch_checkout_prices_if_expired(**fetch_kwargs)

    # then
    mocked_get_tax_data_from_plugins.assert_called_once()
    mocked_get_taxes_for_checkout.assert_called_once()
    mocked_apply_tax_data.assert_not_called()


@freeze_time(timezone.now())
@patch("saleor.checkout.calculations._get_tax_data_from_plugins")
@patch("saleor.checkout.calculations._apply_tax_data")
@pytest.mark.parametrize(["force_update", "call_count"], [(True, 1), (False, 0)])
def test_fetch_checkout_prices_if_expired_valid_prices(
    _mocked_apply_tax_data,
    mocked_get_tax_data_from_plugins,
    checkout_with_items,
    manager,
    fetch_kwargs,
    force_update,
    call_count,
):
    # given
    checkout_with_items.price_expiration -= timedelta(minutes=10)
    checkout_with_items.save(update_fields=["price_expiration"])

    mocked_get_taxes_for_checkout = Mock()
    manager.get_taxes_for_checkout = mocked_get_taxes_for_checkout

    # when
    fetch_checkout_prices_if_expired(**fetch_kwargs, force_update=force_update)

    # then
    assert mocked_get_tax_data_from_plugins.call_count == call_count
    assert mocked_get_taxes_for_checkout.call_count == call_count


@pytest.mark.parametrize(
    "calculate_name",
    [
        "calculate_checkout_line_total",
        "calculate_checkout_line_unit_price",
        "calculate_checkout_shipping",
        "calculate_checkout_subtotal",
        "calculate_checkout_total",
    ],
)
def test_get_tax_data_from_plugins(
    manager, checkout_with_items, fetch_kwargs, calculate_name
):
    # given
    def invalid_money(*_, **__):
        raise TaxError()

    setattr(manager, calculate_name, Mock(side_effect=invalid_money))

    # when
    tax_data = _get_tax_data_from_plugins(checkout_with_items, **fetch_kwargs)

    # then
    assert tax_data is None
