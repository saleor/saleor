from decimal import Decimal

import graphene
import pytest
from prices import Money

from ....discount import DiscountType, DiscountValueType, RewardType, RewardValueType
from ....discount.models import CheckoutDiscount, CheckoutLineDiscount, Promotion
from ....plugins.manager import get_plugins_manager
from ....product.models import ProductVariantChannelListing
from ...fetch import fetch_checkout_info, fetch_checkout_lines
from ...models import CheckoutLine
from ...utils import add_variant_to_checkout, add_voucher_to_checkout


@pytest.fixture
def checkout_with_item_on_sale(checkout_with_item, promotion_converted_from_sale):
    line = checkout_with_item.lines.first()
    channel = checkout_with_item.channel
    discount_amount = Decimal("5.0")
    variant = line.variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    predicate = {"variantPredicate": {"ids": [variant_id]}}
    rule = promotion_converted_from_sale.rules.first()
    rule.catalogue_predicate = predicate
    rule.reward_value = discount_amount
    rule.save(update_fields=["catalogue_predicate", "reward_value"])
    rule.channels.add(channel)
    channel_listing = variant.channel_listings.get(channel=channel)
    channel_listing.discounted_price_amount = (
        channel_listing.price_amount - discount_amount
    )
    channel_listing.save(update_fields=["discounted_price_amount"])

    CheckoutLineDiscount.objects.create(
        line=line,
        promotion_rule=rule,
        type=DiscountType.SALE,
        value_type=rule.reward_value_type,
        value=discount_amount,
        amount_value=discount_amount * line.quantity,
        currency=channel.currency_code,
    )

    return checkout_with_item


@pytest.fixture
def checkout_with_item_on_promotion(checkout_with_item):
    line = checkout_with_item.lines.first()
    channel = checkout_with_item.channel
    promotion = Promotion.objects.create(name="Checkout promotion")

    variant = line.variant

    reward_value = Decimal("5")
    rule = promotion.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", variant.product.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel)

    variant_channel_listing = variant.channel_listings.get(channel=channel)

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel.currency_code,
    )
    CheckoutLineDiscount.objects.create(
        line=line,
        type=DiscountType.PROMOTION,
        value_type=DiscountValueType.FIXED,
        value=reward_value,
        amount_value=reward_value * line.quantity,
        currency=channel.currency_code,
        promotion_rule=rule,
    )

    return checkout_with_item


@pytest.fixture
def checkout_with_item_and_order_discount(
    checkout_with_item, catalogue_promotion_without_rules
):
    channel = checkout_with_item.channel

    reward_value = Decimal("5")

    rule = catalogue_promotion_without_rules.rules.create(
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 20}}}
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(channel)

    CheckoutDiscount.objects.create(
        checkout=checkout_with_item,
        promotion_rule=rule,
        type=DiscountType.ORDER_PROMOTION,
        value_type=rule.reward_value_type,
        value=rule.reward_value,
        amount_value=rule.reward_value,
        currency=channel.currency_code,
    )
    checkout_with_item.discount_amount = reward_value
    checkout_with_item.save(update_fields=["discount_amount"])

    return checkout_with_item


@pytest.fixture
def checkout_with_item_and_gift_promotion(checkout_with_item, gift_promotion_rule):
    channel = checkout_with_item.channel
    variants = gift_promotion_rule.gifts.all()
    variant_listings = ProductVariantChannelListing.objects.filter(variant__in=variants)
    top_price, variant_id = max(
        variant_listings.values_list("discounted_price_amount", "variant")
    )
    variant_listing = [
        listing for listing in variant_listings if listing.variant_id == variant_id
    ][0]

    line = CheckoutLine.objects.create(
        checkout=checkout_with_item,
        quantity=1,
        variant_id=variant_id,
        is_gift=True,
        currency="USD",
        undiscounted_unit_price_amount=variant_listing.price_amount,
    )

    CheckoutLineDiscount.objects.create(
        line=line,
        promotion_rule=gift_promotion_rule,
        type=DiscountType.ORDER_PROMOTION,
        value_type=RewardValueType.FIXED,
        value=top_price,
        amount_value=top_price,
        currency=channel.currency_code,
    )

    return checkout_with_item


@pytest.fixture
def checkout_with_item_and_voucher(checkout_with_item, voucher):
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    add_voucher_to_checkout(
        manager, checkout_info, lines, voucher, voucher.codes.first()
    )
    checkout_with_item.refresh_from_db()
    return checkout_with_item


@pytest.fixture
def checkout_with_item_and_voucher_specific_products(
    checkout_with_item, voucher_specific_product_type
):
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    add_voucher_to_checkout(
        manager,
        checkout_info,
        lines,
        voucher_specific_product_type,
        voucher_specific_product_type.codes.first(),
    )
    checkout_with_item.refresh_from_db()
    return checkout_with_item


@pytest.fixture
def checkout_with_item_and_voucher_once_per_order(checkout_with_item, voucher):
    voucher.apply_once_per_order = True
    voucher.save()
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    add_voucher_to_checkout(
        manager, checkout_info, lines, voucher, voucher.codes.first()
    )
    checkout_with_item.refresh_from_db()
    return checkout_with_item


@pytest.fixture
def checkout_with_item_and_voucher_and_shipping_method(
    checkout_with_item_and_voucher, shipping_method
):
    checkout = checkout_with_item_and_voucher
    checkout.shipping_method = shipping_method
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_voucher(checkout, product, voucher):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 3)
    checkout.voucher_code = voucher.code
    checkout.discount = Money("20.00", "USD")
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_voucher_percentage(checkout, product, voucher_percentage):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 3)
    checkout.voucher_code = voucher_percentage.code
    checkout.discount = Money("3.00", "USD")
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_voucher_percentage_and_shipping(
    checkout_with_voucher_percentage, shipping_method, address
):
    checkout = checkout_with_voucher_percentage
    checkout.shipping_method = shipping_method
    checkout.shipping_address = address
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_voucher_free_shipping(
    checkout_with_items_and_shipping, voucher_free_shipping
):
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_items_and_shipping)
    checkout_info = fetch_checkout_info(
        checkout_with_items_and_shipping, lines, manager
    )
    add_voucher_to_checkout(
        manager,
        checkout_info,
        lines,
        voucher_free_shipping,
        voucher_free_shipping.codes.first(),
    )
    return checkout_with_items_and_shipping
