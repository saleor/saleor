from ...shipping.models import ShippingMethod, ShippingMethodType
from ..delivery_context import (
    get_all_shipping_methods_for_order,
    get_valid_shipping_methods_for_order,
)


def test_get_valid_shipping_methods_for_order(order_line_with_one_allocation, address):
    # given
    order = order_line_with_one_allocation.order
    order_line_with_one_allocation.is_shipping_required = True
    order_line_with_one_allocation.save(update_fields=["is_shipping_required"])

    order.currency = "USD"
    order.shipping_address = address
    order.save(update_fields=["shipping_address"])

    # when
    valid_shipping_methods = get_valid_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all(), None
    ).get()

    # then
    assert len(valid_shipping_methods) == 1


def test_get_valid_shipping_methods_for_order_no_channel_shipping_zones(
    order_line_with_one_allocation, address
):
    # given
    order = order_line_with_one_allocation.order
    order.channel.shipping_zones.clear()
    order_line_with_one_allocation.is_shipping_required = True
    order_line_with_one_allocation.save(update_fields=["is_shipping_required"])

    order.currency = "USD"
    order.shipping_address = address
    order.save(update_fields=["shipping_address"])

    # when
    valid_shipping_methods = get_valid_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all(), None
    ).get()
    # then
    assert len(valid_shipping_methods) == 0


def test_get_valid_shipping_methods_for_order_no_shipping_address(
    order_line_with_one_allocation, address
):
    # given
    order = order_line_with_one_allocation.order
    order_line_with_one_allocation.is_shipping_required = True
    order_line_with_one_allocation.save(update_fields=["is_shipping_required"])

    order.currency = "USD"

    # when
    valid_shipping_methods = get_valid_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all(), None
    ).get()

    # then
    assert valid_shipping_methods == []


def test_get_valid_shipping_methods_for_order_shipping_not_required(
    order_line_with_one_allocation, address
):
    # given
    order = order_line_with_one_allocation.order
    order_line_with_one_allocation.is_shipping_required = False
    order_line_with_one_allocation.save(update_fields=["is_shipping_required"])

    order.currency = "USD"
    order.shipping_address = address
    order.save(update_fields=["shipping_address"])

    # when
    valid_shipping_methods = get_valid_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all(), None
    ).get()

    # then
    assert valid_shipping_methods == []


def test_get_all_shipping_methods_returns_empty_when_shipping_not_required(
    order_with_lines, address
):
    # given
    order = order_with_lines
    order.lines.update(is_shipping_required=False)

    order.shipping_address = address
    order.save(update_fields=["shipping_address"])

    # when
    result = get_all_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all()
    )

    # then
    assert result == []


def test_get_all_shipping_methods_returns_empty_when_no_shipping_address(
    order_with_lines,
):
    # given
    order = order_with_lines
    order.shipping_address = None
    order.save(update_fields=["shipping_address"])

    # when
    result = get_all_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all()
    )

    # then
    assert result == []


def test_get_all_shipping_methods_returns_applicable_methods_with_listings(
    order_with_lines, address, shipping_zone
):
    # given
    order = order_with_lines

    order.shipping_address = address
    order.save(update_fields=["shipping_address"])

    shipping_method = shipping_zone.shipping_methods.first()

    # when
    result = get_all_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all()
    )

    # then
    assert len(result) == 1
    assert result[0].id == str(shipping_method.id)


def test_get_all_shipping_methods_excludes_methods_without_channel_listing(
    order_with_lines, address, shipping_zone
):
    # given
    order = order_with_lines

    order.shipping_address = address
    order.save(update_fields=["shipping_address"])

    method_without_listing = ShippingMethod.objects.create(
        name="No Listing Method",
        shipping_zone=shipping_zone,
        type=ShippingMethodType.PRICE_BASED,
    )

    # when
    result = get_all_shipping_methods_for_order(
        order, order.channel.shipping_method_listings.all()
    )

    # then
    assert len(result) == 1
    existing_method = shipping_zone.shipping_methods.first()
    assert result[0].id == str(existing_method.id)
    assert method_without_listing.id not in [int(m.id) for m in result]
