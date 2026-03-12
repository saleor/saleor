from unittest.mock import MagicMock

from ...checkout.models import Checkout
from ...order.models import Order
from ...tax.defer_conditions import (
    ADDRESS_MISSING,
    _is_address_missing,
    should_defer_webhook,
)

# Tests for should_defer_webhook


def test_should_defer_webhook_returns_true_when_condition_met():
    # given
    checkout = MagicMock(spec=Checkout)
    checkout.is_shipping_required.return_value = True
    checkout.shipping_address_id = None

    # when
    result = should_defer_webhook([ADDRESS_MISSING], checkout)

    # then
    assert result is True


def test_should_defer_webhook_returns_false_when_no_condition_met():
    # given
    checkout = MagicMock(spec=Checkout)
    checkout.is_shipping_required.return_value = True
    checkout.shipping_address_id = 1

    # when
    result = should_defer_webhook([ADDRESS_MISSING], checkout)

    # then
    assert result is False


def test_should_defer_webhook_returns_false_for_empty_conditions():
    # given
    checkout = MagicMock(spec=Checkout)
    checkout.shipping_address_id = None

    # when
    result = should_defer_webhook([], checkout)

    # then
    assert result is False


def test_should_defer_webhook_ignores_unknown_conditions():
    # given
    checkout = MagicMock(spec=Checkout)
    checkout.shipping_address_id = None

    # when
    result = should_defer_webhook(["UNKNOWN_CONDITION"], checkout)

    # then
    assert result is False


def test_should_defer_webhook_returns_true_if_any_condition_met():
    # given
    checkout = MagicMock(spec=Checkout)
    checkout.is_shipping_required.return_value = True
    checkout.shipping_address_id = None

    # when
    result = should_defer_webhook(["UNKNOWN_CONDITION", ADDRESS_MISSING], checkout)

    # then
    assert result is True


# Tests for _is_address_missing with Checkout


def test_is_address_missing_checkout_shipping_required_no_shipping_address():
    # given
    checkout = MagicMock(spec=Checkout)
    checkout.is_shipping_required.return_value = True
    checkout.shipping_address_id = None

    # when
    result = _is_address_missing(checkout)

    # then
    assert result is True


def test_is_address_missing_checkout_shipping_required_with_shipping_address():
    # given
    checkout = MagicMock(spec=Checkout)
    checkout.is_shipping_required.return_value = True
    checkout.shipping_address_id = 1

    # when
    result = _is_address_missing(checkout)

    # then
    assert result is False


def test_is_address_missing_checkout_no_shipping_required_no_billing_address():
    # given
    checkout = MagicMock(spec=Checkout)
    checkout.is_shipping_required.return_value = False
    checkout.billing_address_id = None

    # when
    result = _is_address_missing(checkout)

    # then
    assert result is True


def test_is_address_missing_checkout_no_shipping_required_with_billing_address():
    # given
    checkout = MagicMock(spec=Checkout)
    checkout.is_shipping_required.return_value = False
    checkout.billing_address_id = 1

    # when
    result = _is_address_missing(checkout)

    # then
    assert result is False


# Tests for _is_address_missing with Order


def test_is_address_missing_order_shipping_required_no_shipping_address():
    # given
    order = MagicMock(spec=Order)
    order.is_shipping_required.return_value = True
    order.shipping_address_id = None

    # when
    result = _is_address_missing(order)

    # then
    assert result is True


def test_is_address_missing_order_shipping_required_with_shipping_address():
    # given
    order = MagicMock(spec=Order)
    order.is_shipping_required.return_value = True
    order.shipping_address_id = 1

    # when
    result = _is_address_missing(order)

    # then
    assert result is False


def test_is_address_missing_order_no_shipping_required_no_billing_address():
    # given
    order = MagicMock(spec=Order)
    order.is_shipping_required.return_value = False
    order.billing_address_id = None

    # when
    result = _is_address_missing(order)

    # then
    assert result is True


def test_is_address_missing_order_no_shipping_required_with_billing_address():
    # given
    order = MagicMock(spec=Order)
    order.is_shipping_required.return_value = False
    order.billing_address_id = 1

    # when
    result = _is_address_missing(order)

    # then
    assert result is False


# Tests for _is_address_missing with unknown object types


def test_is_address_missing_unknown_object_returns_false():
    # given
    obj = MagicMock()

    # when
    result = _is_address_missing(obj)

    # then
    assert result is False


def test_is_address_missing_none_returns_false():
    # when
    result = _is_address_missing(None)

    # then
    assert result is False
