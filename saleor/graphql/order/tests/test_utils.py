import pytest

from ....account.models import Address
from ....order import OrderStatus
from ....order.utils import invalidate_order_prices
from ..mutations.utils import save_addresses


@pytest.mark.parametrize(
    ("status", "invalid_prices"),
    [
        (OrderStatus.DRAFT, True),
        (OrderStatus.UNCONFIRMED, True),
        (OrderStatus.UNFULFILLED, False),
    ],
)
def test_invalidate_order_prices_status(order, status, invalid_prices):
    # given
    order.should_refresh_prices = False
    order.status = status

    # when
    invalidate_order_prices(order, save=False)

    # then
    assert order.should_refresh_prices is invalid_prices


@pytest.mark.parametrize(
    ("save", "invalid_prices"),
    [
        (True, True),
        (False, False),
    ],
)
def test_invalidate_order_prices_save(order, save, invalid_prices):
    # given
    order.should_refresh_prices = False
    order.save(update_fields=["should_refresh_prices"])
    order.status = OrderStatus.DRAFT

    # when
    invalidate_order_prices(order, save=save)

    # then
    assert order.should_refresh_prices
    order.refresh_from_db()
    assert order.should_refresh_prices is invalid_prices


def test_save_addresses_both_addresses(order):
    # given
    address_count = Address.objects.count()
    cleaned_input = {
        "billing_address": Address(first_name="Billing", last_name="Test"),
        "shipping_address": Address(first_name="Shipping", last_name="Test"),
    }

    # when
    update_fields = save_addresses(order, cleaned_input)

    # then
    assert set(update_fields) == {"billing_address", "shipping_address"}
    assert Address.objects.count() == address_count + 2


def test_save_addresses_only_billing_address(order):
    # given
    address_count = Address.objects.count()
    cleaned_input = {
        "billing_address": Address(first_name="Billing", last_name="Test"),
    }

    # when
    update_fields = save_addresses(order, cleaned_input)

    # then
    assert set(update_fields) == {"billing_address"}
    assert Address.objects.count() == address_count + 1


def test_save_addresses_only_shipping_address(order):
    # given
    address_count = Address.objects.count()
    cleaned_input = {
        "shipping_address": Address(first_name="Shipping", last_name="Test"),
    }

    # when
    update_fields = save_addresses(order, cleaned_input)

    # then
    assert set(update_fields) == {"shipping_address"}
    assert Address.objects.count() == address_count + 1


def test_save_addresses_empty(order):
    # given
    address_count = Address.objects.count()
    cleaned_input = {}

    # when
    update_fields = save_addresses(order, cleaned_input)

    # then
    assert update_fields == []
    assert Address.objects.count() == address_count
