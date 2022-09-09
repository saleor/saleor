from ....core.taxes import zero_money
from ... import base_calculations


def test_base_order_shipping(order_with_lines):
    # given
    order = order_with_lines
    channel_listing = order.shipping_method.channel_listings.filter(
        channel_id=order.channel_id
    ).first()

    # when
    order_total = base_calculations.base_order_shipping(order)

    # then
    assert order_total == channel_listing.price


def test_base_order_shipping_without_shipping(order):
    # given

    # when
    order_total = base_calculations.base_order_shipping(order)

    # then
    assert order_total == zero_money(order.currency)


def test_base_order_shipping_shipping_without_channel_listing(order_with_lines):
    # given
    order = order_with_lines
    order.shipping_method.channel_listings.filter(channel_id=order.channel_id).delete()

    # when
    order_total = base_calculations.base_order_shipping(order)

    # then
    assert order_total == zero_money(order.currency)
