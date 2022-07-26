from datetime import timedelta

import pytest
from django.utils import timezone
from measurement.measures import Weight
from prices import Money, TaxedMoney

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...plugins.manager import get_plugins_manager
from ...product.models import Category
from .. import calculations, utils
from ..models import Checkout
from ..utils import add_variant_to_checkout, calculate_checkout_quantity


@pytest.fixture()
def anonymous_checkout(db, channel_USD):
    return Checkout.objects.get_or_create(user=None, channel=channel_USD)[0]


def test_get_user_checkout(
    anonymous_checkout, user_checkout, admin_user, customer_user
):
    checkout = utils.get_user_checkout(customer_user)
    assert Checkout.objects.all().count() == 2
    assert checkout == user_checkout


def test_adding_zero_quantity(checkout, product):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 0)
    assert checkout.lines.count() == 0


def test_adding_same_variant(checkout, product):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    add_variant_to_checkout(checkout_info, variant, 2)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_quantity = calculate_checkout_quantity(lines)
    assert checkout.lines.count() == 1
    assert checkout_quantity == 3
    subtotal = TaxedMoney(Money("30.00", "USD"), Money("30.00", "USD"))
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    manager = get_plugins_manager()
    assert (
        calculations.checkout_subtotal(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            address=checkout.shipping_address,
        )
        == subtotal
    )


def test_replacing_same_variant(checkout, product):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1, replace=True)
    add_variant_to_checkout(checkout_info, variant, 2, replace=True)
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 2


def test_adding_invalid_quantity(checkout, product):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    with pytest.raises(ValueError):
        add_variant_to_checkout(checkout_info, variant, -1)


def test_getting_line(checkout, product):
    variant = product.variants.get()
    assert checkout.get_line(variant) is None
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant)
    assert checkout.lines.get() == checkout.get_line(variant)


def test_shipping_detection(checkout, product):
    assert not checkout.is_shipping_required()
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, replace=True)
    assert checkout.is_shipping_required()


def test_get_prices_of_discounted_specific_product(
    priced_checkout_with_item,
    collection,
    voucher_specific_product_type,
):
    checkout = priced_checkout_with_item
    voucher = voucher_specific_product_type
    line = checkout.lines.first()
    product = line.variant.product
    category = product.category
    channel = checkout.channel
    variant_channel_listing = line.variant.channel_listings.get(channel=channel)

    product.collections.add(collection)
    voucher.products.add(product)
    voucher.collections.add(collection)
    voucher.categories.add(category)

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    prices = utils.get_prices_of_discounted_specific_product(
        manager, checkout_info, lines, voucher
    )

    expected_value = [
        line.variant.get_price(
            product, [collection], channel, variant_channel_listing, []
        )
        for item in range(line.quantity)
    ]

    assert prices == expected_value


def test_get_prices_of_discounted_specific_product_only_product(
    priced_checkout_with_item,
    voucher_specific_product_type,
    product_with_default_variant,
):
    checkout = priced_checkout_with_item
    voucher = voucher_specific_product_type
    line = checkout.lines.first()
    product = line.variant.product
    product2 = product_with_default_variant
    channel = checkout.channel
    variant_channel_listing = line.variant.channel_listings.get(channel=channel)

    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, [], [], manager)
    add_variant_to_checkout(checkout_info, product2.variants.get(), 1)
    voucher.products.add(product)
    # assume that cache is correct
    checkout.price_expiration = timezone.now() + timedelta(days=1)
    checkout.save()

    lines, _ = fetch_checkout_lines(checkout)
    prices = utils.get_prices_of_discounted_specific_product(
        manager, checkout_info, lines, voucher
    )

    expected_value = [
        line.variant.get_price(product, [], channel, variant_channel_listing, [])
        for item in range(line.quantity)
    ]

    assert checkout.lines.count() > 1
    assert prices == expected_value


def test_get_prices_of_discounted_specific_product_only_collection(
    priced_checkout_with_item,
    collection,
    voucher_specific_product_type,
    product_with_default_variant,
):
    checkout = priced_checkout_with_item
    voucher = voucher_specific_product_type
    line = checkout.lines.first()
    product = line.variant.product
    product2 = product_with_default_variant
    channel = checkout.channel
    variant_channel_listing = line.variant.channel_listings.get(channel=channel)

    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, [], [], manager)
    add_variant_to_checkout(checkout_info, product2.variants.get(), 1)
    product.collections.add(collection)
    voucher.collections.add(collection)
    # assume that cache is correct
    checkout.price_expiration = timezone.now() + timedelta(days=1)
    checkout.save()

    lines, _ = fetch_checkout_lines(checkout)
    prices = utils.get_prices_of_discounted_specific_product(
        manager, checkout_info, lines, voucher
    )

    expected_value = [
        line.variant.get_price(
            product, [collection], channel, variant_channel_listing, []
        )
        for item in range(line.quantity)
    ]

    assert checkout.lines.count() > 1
    assert prices == expected_value


def test_get_prices_of_discounted_specific_product_only_category(
    priced_checkout_with_item,
    voucher_specific_product_type,
    product_with_default_variant,
):
    checkout = priced_checkout_with_item
    voucher = voucher_specific_product_type
    line = checkout.lines.first()
    product = line.variant.product
    product2 = product_with_default_variant
    category = product.category
    category2 = Category.objects.create(name="Cat", slug="cat")
    channel = checkout.channel
    variant_channel_listing = line.variant.channel_listings.get(channel=channel)

    product2.category = category2
    product2.save()
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, [], [], manager)
    add_variant_to_checkout(checkout_info, product2.variants.get(), 1)
    voucher.categories.add(category)
    # assume that cache is correct
    checkout.price_expiration = timezone.now() + timedelta(days=1)
    checkout.save()

    lines, _ = fetch_checkout_lines(checkout)
    prices = utils.get_prices_of_discounted_specific_product(
        manager, checkout_info, lines, voucher
    )

    expected_value = [
        line.variant.get_price(product, [], channel, variant_channel_listing, [])
        for item in range(line.quantity)
    ]

    assert checkout.lines.count() > 1
    assert prices == expected_value


def test_get_prices_of_discounted_specific_product_all_products(
    priced_checkout_with_item,
    voucher_specific_product_type,
):
    checkout = priced_checkout_with_item
    voucher = voucher_specific_product_type
    line = checkout.lines.first()
    product = line.variant.product
    channel = checkout.channel
    variant_channel_listing = line.variant.channel_listings.get(channel=channel)

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    prices = utils.get_prices_of_discounted_specific_product(
        manager, checkout_info, lines, voucher
    )

    expected_value = [
        line.variant.get_price(product, [], channel, variant_channel_listing, [])
        for item in range(line.quantity)
    ]

    assert prices == expected_value


def test_checkout_line_repr(product, checkout_with_single_item):
    variant = product.variants.get()
    line = checkout_with_single_item.lines.first()
    assert repr(line) == "CheckoutLine(variant=%r, quantity=%r)" % (
        variant,
        line.quantity,
    )


def test_checkout_line_state(product, checkout_with_single_item):
    variant = product.variants.get()
    line = checkout_with_single_item.lines.first()

    assert line.__getstate__() == (variant, line.quantity)

    line.__setstate__((variant, 2))

    assert line.quantity == 2


def test_get_total_weight(checkout_with_item):
    line = checkout_with_item.lines.first()
    variant = line.variant
    variant.weight = Weight(kg=10)
    variant.save()
    line.quantity = 6
    line.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    assert checkout_with_item.get_total_weight(lines) == Weight(kg=60)
