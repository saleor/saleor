import pytest
from django_countries.fields import Country
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from saleor.checkout.utils import add_variant_to_checkout
from saleor.core.taxes import interface
from saleor.shipping import ShippingMethodType


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross",
    [(True, "15.00", "15.00"), (False, "30.00", "30.00")],
)
def test_calculate_checkout_line_total(
    with_discount, expected_net, expected_gross, discount_info, checkout_with_item
):
    line = checkout_with_item.lines.first()
    discounts = [discount_info] if with_discount else None
    total = interface.calculate_checkout_line_total(line, discounts)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, voucher_amount",
    [
        (True, "25.00", "25.00", "0.0"),
        (True, "20.00", "20.00", "5.0"),
        (False, "40.00", "40.00", "0.0"),
        (False, "37.00", "37.00", "3.0"),
    ],
)
def test_calculate_checkout_total(
    with_discount,
    expected_net,
    expected_gross,
    voucher_amount,
    checkout_with_item,
    discount_info,
    shipping_zone,
):
    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.discount_amount = voucher_amount
    checkout_with_item.save()
    discounts = [discount_info] if with_discount else None
    total = interface.calculate_checkout_total(checkout_with_item, discounts)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


def test_calculate_checkout_shipping(checkout_with_item, shipping_zone, discount_info):
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    shipping_price = interface.calculate_checkout_shipping(
        checkout_with_item, discount_info
    )
    assert shipping_price == TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.00", "USD")
    )


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross",
    [(True, "25.00", "25.00"), (False, "50.00", "50.00")],
)
def test_calculate_checkout_subtotal(
    with_discount,
    expected_net,
    expected_gross,
    discount_info,
    checkout_with_item,
    variant,
):
    discounts = [discount_info] if with_discount else None
    add_variant_to_checkout(checkout_with_item, variant, 2)
    total = interface.calculate_checkout_subtotal(checkout_with_item, discounts)

    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


def test_calculate_order_shipping(order, shipping_zone):
    order.shipping_address = order.billing_address.get_copy()
    method = shipping_zone.shipping_methods.get()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()
    price = interface.calculate_order_shipping(order)
    assert price == TaxedMoney(net=Money("10.00", "USD"), gross=Money("10.00", "USD"))


def test_calculate_order_line_unit(order_line):
    assert interface.calculate_order_line_unit(order_line) == order_line.unit_price


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross",
    [(True, "5.00", "5.00"), (False, "10.00", "10.00")],
)
def test_apply_taxes_to_product(
    with_discount, expected_net, expected_gross, discount_info, variant
):
    country = Country("PL")
    discounts = [discount_info] if with_discount else None
    price = interface.apply_taxes_to_product(
        variant.product, variant.get_price(discounts), country
    )
    assert price == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


def test_apply_taxes_to_shipping(shipping_zone, address):
    method = shipping_zone.shipping_methods.get()
    net = method.get_total()
    price = interface.apply_taxes_to_shipping(net, address)
    assert price == TaxedMoney(net=Money("10.00", "USD"), gross=Money("10.00", "USD"))


def test_apply_taxes_to_shipping_price_range(shipping_zone, address):
    shipping_zone.shipping_methods.create(
        name="Super_DHL",
        minimum_order_price=Money(0, "USD"),
        type=ShippingMethodType.PRICE_BASED,
        price=Money(20, "USD"),
        shipping_zone=shipping_zone,
    )
    methods = shipping_zone.shipping_methods.all()
    shipping_methods = methods.values_list("price", flat=True)
    prices = MoneyRange(start=min(shipping_methods), stop=max(shipping_methods))
    price_range = interface.apply_taxes_to_shipping_price_range(prices, address)
    start = TaxedMoney(net=Money("10.00", "USD"), gross=Money("10.00", "USD"))
    stop = TaxedMoney(net=Money("20.00", "USD"), gross=Money("20.00", "USD"))
    assert price_range == TaxedMoneyRange(start, stop)
