from decimal import Decimal
from functools import partial

import graphene
import pytest
from django.conf import settings
from prices import Money, TaxedMoney, fixed_discount

from ....core.taxes import zero_money
from ....discount import DiscountType, DiscountValueType, RewardType, RewardValueType
from ....discount.models import VoucherCode
from ....discount.utils.voucher import (
    create_or_update_discount_object_from_order_level_voucher,
)
from ....product.models import VariantChannelListingPromotionRule
from ....warehouse.models import Allocation, PreorderAllocation, Stock
from ... import OrderOrigin, OrderStatus
from ...base_calculations import base_order_subtotal
from ...models import Order


@pytest.fixture
def draft_order(order_with_lines):
    Allocation.objects.filter(order_line__order=order_with_lines).delete()
    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.origin = OrderOrigin.DRAFT
    order_with_lines.save(update_fields=["status", "origin"])
    return order_with_lines


@pytest.fixture
def draft_order_with_fixed_discount_order(draft_order):
    value = Decimal("20")
    discount = partial(fixed_discount, discount=Money(value, draft_order.currency))
    draft_order.total = discount(draft_order.total)
    draft_order.discounts.create(
        value_type=DiscountValueType.FIXED,
        type=DiscountType.MANUAL,
        value=value,
        reason="Discount reason",
        amount=(draft_order.undiscounted_total - draft_order.total).gross,
    )
    draft_order.save()
    return draft_order


@pytest.fixture
def draft_order_with_voucher(
    draft_order_with_fixed_discount_order, voucher_multiple_use
):
    order = draft_order_with_fixed_discount_order
    voucher_code = voucher_multiple_use.codes.first()
    discount = order.discounts.first()
    discount.type = DiscountType.VOUCHER
    discount.voucher = voucher_multiple_use
    discount.voucher_code = voucher_code.code
    discount.save(update_fields=["type", "voucher", "voucher_code"])

    order.voucher = voucher_multiple_use
    order.voucher_code = voucher_code.code
    order.save(update_fields=["voucher", "voucher_code"])

    channel = order.channel
    channel.include_draft_order_in_voucher_usage = True
    channel.save(update_fields=["include_draft_order_in_voucher_usage"])

    return order


@pytest.fixture
def draft_order_with_free_shipping_voucher(
    draft_order_with_fixed_discount_order, voucher_free_shipping
):
    order = draft_order_with_fixed_discount_order
    voucher_code = voucher_free_shipping.codes.first()
    discount = order.discounts.first()
    discount.type = DiscountType.VOUCHER
    discount.voucher = voucher_free_shipping
    discount.voucher_code = voucher_code.code
    discount.save(update_fields=["type", "voucher", "voucher_code"])

    channel = order.channel
    channel.include_draft_order_in_voucher_usage = True
    channel.save(update_fields=["include_draft_order_in_voucher_usage"])

    order.voucher = voucher_free_shipping
    order.voucher_code = voucher_code.code
    create_or_update_discount_object_from_order_level_voucher(
        order, settings.DATABASE_CONNECTION_DEFAULT_NAME
    )

    subtotal = base_order_subtotal(order, order.lines.all())
    shipping_price = order.base_shipping_price
    order.subtotal = TaxedMoney(gross=subtotal, net=subtotal)
    order.shipping_price = TaxedMoney(net=shipping_price, gross=shipping_price)
    total = subtotal + shipping_price
    order.total = TaxedMoney(net=total, gross=total)
    order.save()

    return order


@pytest.fixture
def draft_order_without_inventory_tracking(order_with_line_without_inventory_tracking):
    order_with_line_without_inventory_tracking.status = OrderStatus.DRAFT
    order_with_line_without_inventory_tracking.origin = OrderStatus.DRAFT
    order_with_line_without_inventory_tracking.save(update_fields=["status", "origin"])
    return order_with_line_without_inventory_tracking


@pytest.fixture
def draft_order_with_preorder_lines(order_with_preorder_lines):
    PreorderAllocation.objects.filter(
        order_line__order=order_with_preorder_lines
    ).delete()
    order_with_preorder_lines.status = OrderStatus.DRAFT
    order_with_preorder_lines.origin = OrderOrigin.DRAFT
    order_with_preorder_lines.save(update_fields=["status", "origin"])
    return order_with_preorder_lines


@pytest.fixture
def draft_order_list_with_multiple_use_voucher(draft_order_list, voucher_multiple_use):
    codes = voucher_multiple_use.codes.values_list("code", flat=True)
    for idx, order in enumerate(draft_order_list):
        order.voucher_code = codes[idx]
    Order.objects.bulk_update(draft_order_list, ["voucher_code"])
    return draft_order_list


@pytest.fixture
def draft_order_list_with_single_use_voucher(draft_order_list, voucher_single_use):
    voucher_codes = voucher_single_use.codes.all()
    codes = voucher_codes.values_list("code", flat=True)
    for idx, order in enumerate(draft_order_list):
        order.voucher_code = codes[idx]
    for voucher_code in voucher_codes:
        voucher_code.is_active = False
    Order.objects.bulk_update(draft_order_list, ["voucher_code"])
    VoucherCode.objects.bulk_update(voucher_codes, ["is_active"])
    return draft_order_list


@pytest.fixture
def draft_order_list(order_list):
    for order in order_list:
        order.status = OrderStatus.DRAFT
        order.origin = OrderOrigin.DRAFT

    Order.objects.bulk_update(order_list, ["status", "origin"])
    return order_list


@pytest.fixture
def draft_orders_in_different_channels(
    draft_order_list, channel_USD, channel_JPY, channel_PLN
):
    draft_order_list[0].channel = channel_USD
    draft_order_list[1].channel = channel_JPY
    draft_order_list[2].channel = channel_PLN

    Order.objects.bulk_update(draft_order_list, ["channel"])
    return draft_order_list


@pytest.fixture
def draft_order_and_promotions(
    order_with_lines,
    order_promotion_without_rules,
    catalogue_promotion_without_rules,
    channel_USD,
):
    # given
    order = order_with_lines
    line_1 = order.lines.get(quantity=3)
    line_2 = order.lines.get(quantity=2)

    # prepare catalogue promotions
    catalogue_promotion = catalogue_promotion_without_rules
    variant_1 = line_1.variant
    variant_2 = line_2.variant
    rule_catalogue = catalogue_promotion.rules.create(
        name="Catalogue rule fixed",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant_2.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(3),
    )
    rule_catalogue.channels.add(channel_USD)

    listing = variant_2.channel_listings.first()
    listing.discounted_price_amount = Decimal(17)
    listing.save(update_fields=["discounted_price_amount"])

    currency = order.currency
    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule_catalogue,
        discount_amount=Decimal(3),
        currency=currency,
    )

    # prepare order promotion - subtotal
    order_promotion = order_promotion_without_rules
    rule_total = order_promotion.rules.create(
        name="Fixed subtotal rule",
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(25),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule_total.channels.add(channel_USD)

    # prepare order promotion - gift
    rule_gift = order_promotion.rules.create(
        name="Gift subtotal rule",
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
        },
        reward_type=RewardType.GIFT,
    )
    rule_gift.channels.add(channel_USD)
    rule_gift.gifts.set([variant_1, variant_2])
    Stock.objects.update(quantity=100)

    # reset prices
    order.total = TaxedMoney(net=zero_money(currency), gross=zero_money(currency))
    order.subtotal = TaxedMoney(net=zero_money(currency), gross=zero_money(currency))
    order.undiscounted_total = TaxedMoney(
        net=zero_money(currency), gross=zero_money(currency)
    )
    order.status = OrderStatus.DRAFT
    order.save()

    return order, rule_catalogue, rule_total, rule_gift
