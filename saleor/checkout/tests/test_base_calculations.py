from decimal import Decimal

from prices import Money, TaxedMoney

from ...discount import DiscountValueType, VoucherType
from ...discount.utils import get_product_discount_on_sale
from ...plugins.manager import get_plugins_manager
from ...tax.utils import calculate_tax_rate
from ..base_calculations import (
    base_checkout_total,
    calculate_base_line_total_price,
    calculate_base_line_unit_price,
)
from ..fetch import fetch_checkout_info, fetch_checkout_lines


def test_calculate_base_line_unit_price(checkout_with_single_item):
    # given
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert not checkout_line_info.voucher
    variant = checkout_line_info.variant

    # when
    unit_price = calculate_base_line_unit_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    expected_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    assert unit_price == expected_price


def test_calculate_base_line_unit_price_with_custom_price(checkout_with_single_item):
    # given
    line = checkout_with_single_item.lines.first()
    price_override = Decimal("12.22")
    line.price_override = price_override
    line.save(update_fields=["price_override"])

    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert not checkout_line_info.voucher

    # when
    unit_price = calculate_base_line_unit_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    currency = checkout_line_info.channel_listing.currency
    expected_price = Money(price_override, currency)
    assert unit_price == expected_price


def test_calculate_base_line_unit_price_with_variant_on_sale(
    checkout_with_single_item, discount_info, category
):
    # given
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert not checkout_line_info.voucher
    variant = checkout_line_info.variant
    # set category on sale
    variant.product.category = category
    variant.product.save()
    checkout_line_info.product = variant.product

    # when
    unit_price = calculate_base_line_unit_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[discount_info]
    )

    # then
    expected_undiscounted_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    product_collections = set(pc.id for pc in checkout_line_info.collections)
    _, sale_discount = get_product_discount_on_sale(
        product=checkout_line_info.product,
        product_collections=product_collections,
        discount=discount_info,
        channel=checkout_with_single_item.channel,
        variant_id=variant.id,
    )
    expected_price = sale_discount(expected_undiscounted_price)

    assert unit_price == expected_price


def test_calculate_base_line_unit_price_with_variant_on_sale_custom_price(
    checkout_with_single_item, discount_info, category
):
    # given
    line = checkout_with_single_item.lines.first()
    price_override = Decimal("20.00")
    line.price_override = price_override
    line.save(update_fields=["price_override"])

    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert not checkout_line_info.voucher
    variant = checkout_line_info.variant
    # set category on sale
    variant.product.category = category
    variant.product.save()
    checkout_line_info.product = variant.product

    # when
    unit_price = calculate_base_line_unit_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[discount_info]
    )

    # then
    currency = checkout_line_info.channel_listing.currency
    expected_undiscounted_price = Money(price_override, currency)
    product_collections = set(pc.id for pc in checkout_line_info.collections)
    _, sale_discount = get_product_discount_on_sale(
        product=checkout_line_info.product,
        product_collections=product_collections,
        discount=discount_info,
        channel=checkout_with_single_item.channel,
        variant_id=variant.id,
    )
    expected_price = sale_discount(expected_undiscounted_price)

    assert unit_price == expected_price


def test_calculate_base_line_unit_price_with_fixed_voucher(
    checkout_with_single_item, voucher, channel_USD
):
    # given
    checkout_line = checkout_with_single_item.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout_with_single_item.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher
    variant = checkout_line_info.variant

    # when
    unit_price = calculate_base_line_unit_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    expected_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    assert unit_price == expected_price - voucher_amount


def test_calculate_base_line_unit_price_with_fixed_voucher_custom_prices(
    checkout_with_single_item, voucher, channel_USD
):
    # given
    checkout_line = checkout_with_single_item.lines.first()
    price_override = Decimal("20.00")
    checkout_line.price_override = price_override
    checkout_line.save(update_fields=["price_override"])

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout_with_single_item.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher

    # when
    unit_price = calculate_base_line_unit_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    currency = checkout_line_info.channel_listing.currency
    expected_price = Money(price_override, currency)
    assert unit_price == expected_price - voucher_amount


def test_calculate_base_line_unit_price_with_percentage_voucher(
    checkout_with_single_item, voucher, channel_USD
):
    # given
    checkout_line = checkout_with_single_item.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save()

    voucher_percent_value = Decimal(10)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount_value = voucher_percent_value
    voucher_channel_listing.save()

    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher
    variant = checkout_line_info.variant

    # when
    unit_price = calculate_base_line_unit_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    expected_voucher_amount = Money(Decimal("1"), checkout_with_single_item.currency)
    expected_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    assert unit_price == expected_price - expected_voucher_amount


def test_calculate_base_line_unit_price_with_percentage_voucher_custom_prices(
    checkout_with_single_item, voucher, channel_USD
):
    # given
    checkout_line = checkout_with_single_item.lines.first()
    price_override = Decimal("20.00")
    checkout_line.price_override = price_override
    checkout_line.save(update_fields=["price_override"])

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save()

    voucher_percent_value = Decimal(10)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount_value = voucher_percent_value
    voucher_channel_listing.save()

    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher

    # when
    unit_price = calculate_base_line_unit_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    currency = checkout_line_info.channel_listing.currency
    expected_price = Money(price_override, currency)
    expected_voucher_amount = Money(
        price_override * voucher_percent_value / 100, checkout_with_single_item.currency
    )
    assert unit_price == expected_price - expected_voucher_amount


def test_calculate_base_line_unit_price_with_discounts_apply_once_per_order(
    checkout_with_single_item, voucher, channel_USD
):
    # given
    checkout_line = checkout_with_single_item.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save()

    voucher_percent_value = Decimal(10)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount_value = voucher_percent_value
    voucher_channel_listing.save()

    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher
    variant = checkout_line_info.variant

    # when
    unit_price = calculate_base_line_unit_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    expected_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    expected_voucher_amount = expected_price * voucher_percent_value / 100
    assert unit_price == expected_price - expected_voucher_amount


def test_calculate_base_line_unit_price_with_discounts_once_per_order_custom_prices(
    checkout_with_single_item, voucher, channel_USD
):
    # given
    checkout_line = checkout_with_single_item.lines.first()
    price_override = Decimal("20.00")
    checkout_line.price_override = price_override
    checkout_line.save(update_fields=["price_override"])

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save()

    voucher_percent_value = Decimal(10)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount_value = voucher_percent_value
    voucher_channel_listing.save()

    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher

    # when
    unit_price = calculate_base_line_unit_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    currency = checkout_line_info.channel_listing.currency
    expected_price = Money(price_override, currency)
    expected_voucher_amount = expected_price * voucher_percent_value / 100
    assert unit_price == expected_price - expected_voucher_amount


def test_calculate_base_line_unit_price_with_variant_on_sale_and_voucher(
    checkout_with_single_item, discount_info, category, voucher, channel_USD
):
    # given
    checkout_line = checkout_with_single_item.lines.first()
    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()
    voucher_amount = Money(Decimal(3), checkout_with_single_item.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()
    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher
    variant = checkout_line_info.variant

    # set category on sale
    variant.product.category = category
    variant.product.save()
    checkout_line_info.product = variant.product

    # when
    unit_price = calculate_base_line_unit_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[discount_info]
    )

    # then
    expected_undiscounted_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    product_collections = set(pc.id for pc in checkout_line_info.collections)
    _, sale_discount = get_product_discount_on_sale(
        product=checkout_line_info.product,
        product_collections=product_collections,
        discount=discount_info,
        channel=checkout_with_single_item.channel,
        variant_id=variant.id,
    )
    sale_discount_amount = sale_discount(expected_undiscounted_price)
    expected_price = expected_undiscounted_price - sale_discount_amount

    assert unit_price == expected_price - voucher_amount


def test_calculate_base_line_total_price(checkout_with_single_item):
    # given
    quantity = 3
    checkout_line = checkout_with_single_item.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert not checkout_line_info.voucher
    variant = checkout_line_info.variant

    # when
    total_price = calculate_base_line_total_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    expected_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    assert total_price == expected_price * quantity


def test_calculate_base_line_total_price_with_variant_on_sale(
    checkout_with_single_item, discount_info, category
):
    # given
    quantity = 3
    checkout_line = checkout_with_single_item.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert not checkout_line_info.voucher
    variant = checkout_line_info.variant
    # set category on sale
    variant.product.category = category
    variant.product.save()
    checkout_line_info.product = variant.product

    # when
    total_price = calculate_base_line_total_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[discount_info]
    )

    # then
    expected_undiscounted_unit_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    product_collections = set(pc.id for pc in checkout_line_info.collections)
    _, sale_discount = get_product_discount_on_sale(
        product=checkout_line_info.product,
        product_collections=product_collections,
        discount=discount_info,
        channel=checkout_with_single_item.channel,
        variant_id=variant.id,
    )
    sale_discount_amount = sale_discount(expected_undiscounted_unit_price)
    expected_price = expected_undiscounted_unit_price - sale_discount_amount

    assert total_price == expected_price * quantity


def test_calculate_base_line_total_price_with_fixed_voucher(
    checkout_with_single_item, voucher, channel_USD
):
    # given
    quantity = 3
    checkout_line = checkout_with_single_item.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_line = checkout_with_single_item.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout_with_single_item.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher
    variant = checkout_line_info.variant

    # when
    total_price = calculate_base_line_total_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    expected_unit_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    assert total_price == (expected_unit_price - voucher_amount) * quantity


def test_calculate_base_line_total_price_with_percentage_voucher(
    checkout_with_single_item, voucher, channel_USD
):
    # given
    quantity = 3
    checkout_line = checkout_with_single_item.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_line = checkout_with_single_item.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save()

    voucher_percent_value = Decimal(10)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount_value = voucher_percent_value
    voucher_channel_listing.save()

    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher
    variant = checkout_line_info.variant

    # when
    total_price = calculate_base_line_total_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    expected_voucher_amount = Money(Decimal("1"), checkout_with_single_item.currency)
    expected_unit_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    assert total_price == (expected_unit_price - expected_voucher_amount) * quantity


def test_calculate_base_line_total_price_with_discounts_apply_once_per_order(
    checkout_with_single_item, voucher, channel_USD
):
    # given
    quantity = 3
    checkout_line = checkout_with_single_item.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_line = checkout_with_single_item.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save()

    voucher_percent_value = Decimal(10)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount_value = voucher_percent_value
    voucher_channel_listing.save()

    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher
    variant = checkout_line_info.variant

    # when
    total_price = calculate_base_line_total_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[]
    )

    # then
    expected_voucher_amount = Money(Decimal("1"), checkout_with_single_item.currency)
    expected_unit_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    # apply once per order is applied when calculating line total.
    assert total_price == (expected_unit_price * quantity) - expected_voucher_amount


def test_calculate_base_line_total_price_with_variant_on_sale_and_voucher(
    checkout_with_single_item, discount_info, category, voucher, channel_USD
):
    # given
    quantity = 3
    checkout_line = checkout_with_single_item.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_line = checkout_with_single_item.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout_with_single_item.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher
    variant = checkout_line_info.variant

    # set category on sale
    variant.product.category = category
    variant.product.save()
    checkout_line_info.product = variant.product

    # when
    total_price = calculate_base_line_total_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[discount_info]
    )

    # then
    expected_undiscounted_unit_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    product_collections = set(pc.id for pc in checkout_line_info.collections)
    _, sale_discount = get_product_discount_on_sale(
        product=checkout_line_info.product,
        product_collections=product_collections,
        discount=discount_info,
        channel=checkout_with_single_item.channel,
        variant_id=variant.id,
    )
    sale_discount_amount = sale_discount(expected_undiscounted_unit_price)
    expected_unit_price = expected_undiscounted_unit_price - sale_discount_amount

    assert total_price == (expected_unit_price - voucher_amount) * quantity


def test_calculate_base_line_total_price_with_variant_on_sale_and_voucher_applied_once(
    checkout_with_single_item, discount_info, category, voucher, channel_USD
):
    # given
    quantity = 3
    checkout_line = checkout_with_single_item.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_line = checkout_with_single_item.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.apply_once_per_order = True
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout_with_single_item.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout_with_single_item.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher
    variant = checkout_line_info.variant

    # set category on sale
    variant.product.category = category
    variant.product.save()
    checkout_line_info.product = variant.product

    # when
    total_price = calculate_base_line_total_price(
        checkout_line_info, checkout_with_single_item.channel, discounts=[discount_info]
    )

    # then
    expected_undiscounted_unit_price = variant.get_price(
        product=checkout_line_info.product,
        collections=checkout_line_info.collections,
        channel=checkout_with_single_item.channel,
        channel_listing=checkout_line_info.channel_listing,
        discounts=[],
    )
    product_collections = set(pc.id for pc in checkout_line_info.collections)
    _, sale_discount = get_product_discount_on_sale(
        product=checkout_line_info.product,
        product_collections=product_collections,
        discount=discount_info,
        channel=checkout_with_single_item.channel,
        variant_id=variant.id,
    )
    sale_discount_amount = sale_discount(expected_undiscounted_unit_price)
    expected_unit_price = expected_undiscounted_unit_price - sale_discount_amount

    assert total_price == (expected_unit_price * quantity) - voucher_amount


def test_base_tax_rate_net_price_zero():
    price = TaxedMoney(net=Money(0, "USD"), gross=Money(3, "USD"))
    assert calculate_tax_rate(price) == Decimal("0.0")


def test_base_tax_rate_gross_price_zero():
    price = TaxedMoney(net=Money(3, "USD"), gross=Money(0, "USD"))
    assert calculate_tax_rate(price) == Decimal("0.0")


def test_base_checkout_total(checkout_with_item, shipping_method, voucher_percentage):
    # given
    manager = get_plugins_manager()
    channel = checkout_with_item.channel
    currency = checkout_with_item.currency
    discount_amount = Money(5, currency)
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.discount = discount_amount
    checkout_with_item.save()
    checkout_lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, [], manager)

    # when
    total = base_checkout_total(checkout_info, [], checkout_lines)

    # then
    variant = checkout_with_item.lines.first().variant
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(variant.product, [], channel, channel_listing)
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    expected_price = (
        net * checkout_with_item.lines.first().quantity
        + shipping_channel_listings.price
        - discount_amount
    )
    assert total == expected_price


def test_base_checkout_total_high_discount_on_entire_order(
    checkout_with_item, shipping_method, voucher_percentage
):
    # given
    manager = get_plugins_manager()
    currency = checkout_with_item.currency

    discount_amount = Money(100, currency)
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.discount = discount_amount
    checkout_with_item.save()

    shipping_price = shipping_method.channel_listings.get(
        channel=checkout_with_item.channel
    ).price

    checkout_lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, [], manager)

    # when
    total = base_checkout_total(checkout_info, [], checkout_lines)

    # then
    assert total == shipping_price


def test_base_checkout_total_high_discount_on_shipping(
    checkout_with_item, shipping_method, voucher_shipping_type
):
    # given
    manager = get_plugins_manager()

    channel = checkout_with_item.channel
    shipping_price = shipping_method.channel_listings.get(channel=channel).price

    currency = checkout_with_item.currency
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.voucher_code = voucher_shipping_type.code
    checkout_with_item.discount = shipping_price + Money(10, currency)
    checkout_with_item.save()

    checkout_lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, [], manager)

    # when
    total = base_checkout_total(checkout_info, [], checkout_lines)

    # then
    variant = checkout_with_item.lines.first().variant
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(variant.product, [], channel, channel_listing)
    expected_price = net * checkout_with_item.lines.first().quantity
    assert total == expected_price
