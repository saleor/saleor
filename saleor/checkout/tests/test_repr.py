from types import SimpleNamespace

from prices import Money

from ...shipping.interface import ShippingMethodData
from ..delivery_context import ShippingMethodInfo
from ..fetch import CheckoutInfo, CheckoutLineInfo


def test_shipping_method_data_repr_omits_metadata():
    shipping_method = ShippingMethodData(
        id="shipping-1",
        name="Express",
        price=Money("12.00", "USD"),
        metadata={"internal": "value"},
    )

    result = repr(shipping_method)

    assert result == (
        "ShippingMethodData(id='shipping-1', name='Express', price=12.00 USD, "
        "active=True)"
    )
    assert "internal" not in result


def test_shipping_method_info_repr_uses_address_id():
    shipping_method = ShippingMethodData("shipping-1", Money("12.00", "USD"))

    result = repr(ShippingMethodInfo(shipping_method, SimpleNamespace(pk=42)))

    assert result == (
        "ShippingMethodInfo(delivery_method=ShippingMethodData(id='shipping-1', "
        "name=None, price=12.00 USD, active=True), shipping_address_id=42, "
        "store_as_customer_address=True)"
    )


def test_checkout_info_repr_is_compact():
    checkout_info = CheckoutInfo.__new__(CheckoutInfo)
    checkout_info.checkout = SimpleNamespace(pk=10)
    checkout_info.user = SimpleNamespace(pk=11)
    checkout_info.channel = SimpleNamespace(pk=12)
    checkout_info.lines = [object(), object()]
    checkout_info.discounts = [object()]

    assert repr(checkout_info) == (
        "CheckoutInfo(checkout_id=10, user_id=11, channel_id=12, lines=2, discounts=1)"
    )


def test_checkout_line_info_repr_is_compact():
    checkout_line_info = CheckoutLineInfo.__new__(CheckoutLineInfo)
    checkout_line_info.line = SimpleNamespace(pk=20, quantity=3)
    checkout_line_info.variant = SimpleNamespace(pk=21)
    checkout_line_info.discounts = [object(), object()]

    assert repr(checkout_line_info) == (
        "CheckoutLineInfo(line_id=20, variant_id=21, quantity=3, discounts=2)"
    )
