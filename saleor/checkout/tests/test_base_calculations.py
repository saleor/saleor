from decimal import Decimal

from prices import Money, TaxedMoney

from ...discount import DiscountValueType, RewardValueType, VoucherType
from ...discount.models import PromotionRule
from ...plugins.manager import get_plugins_manager
from ...tax.utils import calculate_tax_rate
from ..base_calculations import (
    base_checkout_total,
    calculate_base_line_total_price,
    calculate_base_line_unit_price,
    checkout_total,
)
from ..fetch import fetch_checkout_info, fetch_checkout_lines


def test_calculate_base_line_unit_price(checkout_with_single_item):
    # given
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_single_item)
    checkout_line_info = checkout_lines_info[0]
    assert not checkout_line_info.voucher
    variant = checkout_line_info.variant

    # when
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    expected_price = variant.get_price(
        channel_listing=checkout_line_info.channel_listing,
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
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    currency = checkout_line_info.channel_listing.currency
    expected_price = Money(price_override, currency)
    assert unit_price == expected_price


def test_calculate_base_line_unit_price_with_variant_on_sale(
    checkout_with_item_on_sale,
):
    # given
    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_item_on_sale)

    checkout_line_info = checkout_lines_info[0]
    assert not checkout_line_info.voucher
    variant = checkout_line_info.variant
    checkout_line_info.product = variant.product

    # when
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    assert unit_price == checkout_line_info.channel_listing.discounted_price


def test_calculate_base_line_unit_price_with_variant_on_sale_custom_price(
    checkout_with_item_on_sale,
):
    # given
    line = checkout_with_item_on_sale.lines.first()
    price_override = Decimal("20.00")
    line.price_override = price_override
    line.save(update_fields=["price_override"])

    checkout_lines_info, _ = fetch_checkout_lines(checkout_with_item_on_sale)
    checkout_line_info = checkout_lines_info[0]

    # when
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    discount = line.discounts.first()
    expected_price = price_override - discount.value
    assert unit_price.amount == expected_price


def test_calculate_base_line_unit_price_with_variant_on_promotion(
    checkout_with_item_on_promotion, category
):
    # given
    checkout = checkout_with_item_on_promotion
    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_line_info = checkout_lines_info[0]

    # when
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    assert unit_price == checkout_line_info.channel_listing.discounted_price


def test_calculate_base_line_unit_price_with_variant_on_promotion_custom_price(
    checkout_with_item_on_promotion, category
):
    # given
    checkout = checkout_with_item_on_promotion
    line = checkout.lines.first()
    price_override = Decimal("20.00")
    line.price_override = price_override
    line.save(update_fields=["price_override"])

    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_line_info = checkout_lines_info[0]

    # when
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    discount = line.discounts.first()
    expected_price = price_override - discount.value
    assert unit_price.amount == expected_price


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
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    expected_price = variant.get_price(
        channel_listing=checkout_line_info.channel_listing,
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
    unit_price = calculate_base_line_unit_price(checkout_line_info)

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
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    expected_voucher_amount = Money(Decimal("1"), checkout_with_single_item.currency)
    expected_price = variant.get_price(
        channel_listing=checkout_line_info.channel_listing,
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
    unit_price = calculate_base_line_unit_price(checkout_line_info)

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
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    expected_price = variant.get_price(
        channel_listing=checkout_line_info.channel_listing,
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
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    currency = checkout_line_info.channel_listing.currency
    expected_price = Money(price_override, currency)
    expected_voucher_amount = expected_price * voucher_percent_value / 100
    assert unit_price == expected_price - expected_voucher_amount


def test_calculate_base_line_unit_price_with_variant_on_sale_and_voucher(
    checkout_with_single_item, category, voucher, channel_USD
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

    # when
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    expected_unit_price = checkout_line_info.channel_listing.discounted_price
    assert unit_price == expected_unit_price - voucher_amount


def test_calculate_base_line_unit_price_with_variant_on_promotion_and_voucher(
    checkout_with_item_on_promotion, voucher, channel_USD
):
    # given
    checkout = checkout_with_item_on_promotion
    checkout_line = checkout.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout.voucher_code = voucher.code

    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_line_info = checkout_lines_info[0]

    assert checkout_line_info.voucher

    # when
    unit_price = calculate_base_line_unit_price(checkout_line_info)

    # then
    expected_price = checkout_line_info.channel_listing.discounted_price

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
    total_price = calculate_base_line_total_price(checkout_line_info)

    # then
    expected_price = variant.get_price(
        channel_listing=checkout_line_info.channel_listing,
    )
    assert total_price == expected_price * quantity


def test_calculate_base_line_total_price_with_variant_on_sale(
    checkout_with_item_on_sale,
):
    # given
    quantity = 3
    checkout = checkout_with_item_on_sale
    checkout_line = checkout.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_line_info = checkout_lines_info[0]

    # when
    total_price = calculate_base_line_total_price(checkout_line_info)

    # then
    expected_unit_price = checkout_line_info.channel_listing.discounted_price
    assert total_price == expected_unit_price * quantity


def test_calculate_base_line_total_price_with_variant_on_promotion(
    checkout_with_item_on_promotion,
):
    # given
    quantity = 3
    checkout = checkout_with_item_on_promotion
    checkout_line = checkout.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_line_info = checkout_lines_info[0]
    assert not checkout_line_info.voucher

    # when
    total_price = calculate_base_line_total_price(checkout_line_info)

    # then
    assert total_price == checkout_line_info.channel_listing.discounted_price * quantity


def test_calculate_base_line_total_price_with_1_cent_variant_on_10_percentage_discount(
    checkout_with_item_on_promotion,
):
    # given
    quantity = 10
    checkout = checkout_with_item_on_promotion
    checkout_line = checkout.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    rule = PromotionRule.objects.first()
    rule.reward_value = Decimal("10")
    rule.reward_value_type = RewardValueType.PERCENTAGE

    # Set product price to 0.01 USD
    variant = checkout_line.variant
    variant_channel_listing = variant.channel_listings.get()
    variant_channel_listing.price_amount = Decimal("0.01")
    variant_channel_listing.discounted_price_amount = Decimal("0.01")
    variant_channel_listing.save()

    listing_rule = variant_channel_listing.variantlistingpromotionrule.first()
    listing_rule.discount_amount = (
        rule.reward_value * variant_channel_listing.price_amount / 100
    )
    listing_rule.save(update_fields=["discount_amount"])

    discount = checkout_line.discounts.first()
    discount.amount_value = listing_rule.discount_amount * quantity
    discount.save(update_fields=["amount_value"])

    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_line_info = checkout_lines_info[0]

    # when
    total_price = calculate_base_line_total_price(checkout_line_info)

    # then
    variant_channel_listing.refresh_from_db()
    assert variant_channel_listing.price_amount == Decimal("0.01")
    assert total_price == Money(Decimal("0.09"), checkout_line.currency)


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
    total_price = calculate_base_line_total_price(checkout_line_info)

    # then
    expected_unit_price = variant.get_price(
        channel_listing=checkout_line_info.channel_listing,
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
    total_price = calculate_base_line_total_price(checkout_line_info)

    # then
    expected_voucher_amount = Money(Decimal("1"), checkout_with_single_item.currency)
    expected_unit_price = variant.get_price(
        channel_listing=checkout_line_info.channel_listing,
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
    total_price = calculate_base_line_total_price(checkout_line_info)

    # then
    expected_voucher_amount = Money(Decimal("1"), checkout_with_single_item.currency)
    expected_unit_price = variant.get_price(
        channel_listing=checkout_line_info.channel_listing,
    )
    # apply once per order is applied when calculating line total.
    assert total_price == (expected_unit_price * quantity) - expected_voucher_amount


def test_calculate_base_line_total_price_with_variant_on_sale_and_voucher(
    checkout_with_item_on_sale, category, voucher, channel_USD
):
    # given
    quantity = 3
    checkout = checkout_with_item_on_sale
    checkout_line = checkout.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_line = checkout.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout.voucher_code = voucher.code

    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_line_info = checkout_lines_info[0]

    # when
    total_price = calculate_base_line_total_price(checkout_line_info)

    # then
    expected_unit_price = checkout_line_info.channel_listing.discounted_price
    assert total_price == (expected_unit_price - voucher_amount) * quantity


def test_calculate_base_line_total_price_with_variant_on_sale_and_voucher_applied_once(
    checkout_with_item_on_sale, category, voucher, channel_USD
):
    # given
    quantity = 3
    checkout = checkout_with_item_on_sale
    checkout_line = checkout.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout.voucher_code = voucher.code
    checkout.save(update_fields=["voucher_code"])

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.apply_once_per_order = True
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_line_info = checkout_lines_info[0]

    # when
    total_price = calculate_base_line_total_price(checkout_line_info)

    # then
    expected_unit_price = checkout_line_info.channel_listing.discounted_price
    assert total_price == (expected_unit_price * quantity) - voucher_amount


def test_calculate_base_line_total_price_with_variant_on_promotion_and_voucher(
    checkout_with_item_on_promotion, voucher, channel_USD
):
    # given
    quantity = 3
    checkout = checkout_with_item_on_promotion
    checkout_line = checkout.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_line = checkout.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher

    # when
    total_price = calculate_base_line_total_price(checkout_line_info)

    # then
    expected_unit_price = checkout_line_info.channel_listing.discounted_price

    assert total_price == (expected_unit_price - voucher_amount) * quantity


def test_calculate_base_line_total_price_variant_on_promotion_and_voucher_applied_once(
    checkout_with_item_on_promotion, category, voucher, channel_USD
):
    # given
    quantity = 3
    checkout = checkout_with_item_on_promotion
    checkout_line = checkout.lines.first()
    checkout_line.quantity = quantity
    checkout_line.save()

    checkout_line = checkout.lines.first()

    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.apply_once_per_order = True
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout.voucher_code = voucher.code
    checkout_lines_info, _ = fetch_checkout_lines(checkout)
    checkout_line_info = checkout_lines_info[0]
    assert checkout_line_info.voucher
    variant = checkout_line_info.variant

    # set category on sale
    variant.product.category = category
    variant.product.save()
    checkout_line_info.product = variant.product

    # when
    total_price = calculate_base_line_total_price(checkout_line_info)

    # then
    expected_unit_price = checkout_line_info.channel_listing.discounted_price

    assert total_price == (expected_unit_price * quantity) - voucher_amount


def test_base_tax_rate_net_price_zero():
    price = TaxedMoney(net=Money(0, "USD"), gross=Money(3, "USD"))
    assert calculate_tax_rate(price) == Decimal("0.0")


def test_base_tax_rate_gross_price_zero():
    price = TaxedMoney(net=Money(3, "USD"), gross=Money(0, "USD"))
    assert calculate_tax_rate(price) == Decimal("0.0")


def test_base_checkout_total(checkout_with_item, shipping_method, voucher_percentage):
    # given
    manager = get_plugins_manager(allow_replica=False)
    channel = checkout_with_item.channel
    currency = checkout_with_item.currency

    checkout_with_item.shipping_method = shipping_method
    # only line vouchers are applied on based price so this discount won't be included
    # in base price
    discount_amount = Money(5, currency)
    checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.discount = discount_amount
    checkout_with_item.save()

    checkout_lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, manager)

    # when
    total = base_checkout_total(checkout_info, checkout_lines)

    # then
    variant = checkout_with_item.lines.first().variant
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    expected_price = (
        net * checkout_with_item.lines.first().quantity
        + shipping_channel_listings.price
    )
    assert total == expected_price


def test_base_checkout_total_high_discount_on_entire_order_apply_once_per_order(
    checkout_with_item, shipping_method, voucher_percentage
):
    # given
    voucher_percentage.apply_once_per_order = True
    voucher_percentage.save(update_fields=["apply_once_per_order"])

    voucher_channel_listing = voucher_percentage.channel_listings.first()
    voucher_channel_listing.discount_value = 100
    voucher_channel_listing.save(update_fields=["discount_value"])

    manager = get_plugins_manager(allow_replica=False)

    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.save(update_fields=["shipping_method", "voucher_code"])

    line = checkout_with_item.lines.first()
    line.quantity = 1
    line.save(update_fields=["quantity"])

    shipping_price = shipping_method.channel_listings.get(
        channel=checkout_with_item.channel
    ).price

    checkout_lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, manager)

    # when
    total = base_checkout_total(checkout_info, checkout_lines)

    # then
    assert total == shipping_price


def test_base_checkout_total_high_discount_on_shipping(
    checkout_with_item, shipping_method, voucher_shipping_type
):
    # given
    manager = get_plugins_manager(allow_replica=False)

    channel = checkout_with_item.channel
    shipping_price = shipping_method.channel_listings.get(channel=channel).price

    currency = checkout_with_item.currency
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.voucher_code = voucher_shipping_type.code
    checkout_with_item.discount = shipping_price + Money(10, currency)
    checkout_with_item.save()

    checkout_lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, manager)

    # when
    total = base_checkout_total(checkout_info, checkout_lines)

    # then
    variant = checkout_with_item.lines.first().variant
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    expected_price = net * checkout_with_item.lines.first().quantity
    assert total == expected_price


def test_base_checkout_total_order_discount(
    checkout_with_item_and_order_discount, shipping_method
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item_and_order_discount
    channel = checkout.channel

    checkout.shipping_method = shipping_method
    checkout_lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)

    # when
    total = base_checkout_total(checkout_info, checkout_lines)

    # then
    variant = checkout.lines.first().variant
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    # order promotion discount shouldn't be included
    expected_price = (
        net * checkout.lines.first().quantity + shipping_channel_listings.price
    )
    assert total == expected_price


def test_checkout_total_order_discount(
    checkout_with_item_and_order_discount, shipping_method
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item_and_order_discount
    channel = checkout.channel

    checkout.shipping_method = shipping_method
    checkout_lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)

    # when
    total = checkout_total(checkout_info, checkout_lines)

    # then
    variant = checkout.lines.first().variant
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    # order promotion discount should be included
    expected_price = (
        net * checkout.lines.first().quantity
        + shipping_channel_listings.price
        - checkout.discount
    )
    assert total == expected_price


def test_base_checkout_total_gift_promotion(
    checkout_with_item_and_gift_promotion, shipping_method
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item_and_gift_promotion
    channel = checkout.channel

    checkout.shipping_method = shipping_method
    checkout_lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)

    # when
    total = base_checkout_total(checkout_info, checkout_lines)

    # then
    variant = checkout.lines.get(is_gift=False).variant
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    # the gift line price should not be included, the price should be equal to the sum
    # of the shipping price and the price of the variants that are not a gift
    expected_price = (
        net * checkout.lines.first().quantity + shipping_channel_listings.price
    )
    assert total == expected_price


def test_checkout_total_gift_promotion(
    checkout_with_item_and_gift_promotion, shipping_method
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item_and_gift_promotion
    channel = checkout.channel

    checkout.shipping_method = shipping_method
    checkout_lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)

    # when
    total = checkout_total(checkout_info, checkout_lines)

    # then
    variant = checkout.lines.first().variant
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    # the gift line price should not be included, the price should be equal to the sum
    # of the shipping price and the price of the variants that are not a gift
    expected_price = (
        net * checkout.lines.first().quantity + shipping_channel_listings.price
    )
    assert total == expected_price
