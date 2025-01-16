from decimal import Decimal

import pytest
from prices import Money, TaxedMoney

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...discount import DiscountType, DiscountValueType
from ...discount.interface import VariantPromotionRuleInfo
from ...giftcard import GiftCardEvents
from ...giftcard.models import GiftCardEvent
from ...graphql.order.utils import OrderLineData
from ...plugins.manager import get_plugins_manager
from ...product.models import VariantChannelListingPromotionRule
from .. import OrderStatus
from ..events import OrderEvents
from ..fetch import OrderLineInfo
from ..models import Order, OrderEvent
from ..utils import (
    add_gift_cards_to_order,
    add_variant_to_order,
    change_order_line_quantity,
    create_order_line_discounts,
    get_order_country,
    get_total_order_discount_excluding_shipping,
    get_valid_shipping_methods_for_order,
    match_orders_with_new_user,
    update_order_display_gross_prices,
)


@pytest.mark.parametrize(
    ("status", "previous_quantity", "new_quantity", "added_count", "removed_count"),
    [
        (OrderStatus.DRAFT, 5, 2, 0, 3),
        (OrderStatus.UNCONFIRMED, 2, 5, 3, 0),
        (OrderStatus.UNCONFIRMED, 2, 0, 0, 2),
        (OrderStatus.DRAFT, 5, 5, 0, 0),
    ],
)
def test_change_quantity_generates_proper_event(
    status,
    previous_quantity,
    new_quantity,
    added_count,
    removed_count,
    order_with_lines,
    staff_user,
):
    assert not OrderEvent.objects.exists()
    order_with_lines.status = status
    order_with_lines.save(update_fields=["status"])

    line = order_with_lines.lines.last()
    line.quantity = previous_quantity

    line_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )
    stock = line.allocations.first().stock
    stock.quantity = 5
    stock.save(update_fields=["quantity"])
    app = None

    change_order_line_quantity(
        staff_user,
        app,
        line_info,
        previous_quantity,
        new_quantity,
        order_with_lines.channel,
        get_plugins_manager(allow_replica=False),
    )

    if removed_count:
        expected_type = OrderEvents.REMOVED_PRODUCTS
        expected_quantity = removed_count
    elif added_count:
        expected_type = OrderEvents.ADDED_PRODUCTS
        expected_quantity = added_count
    else:
        # No event should have occurred
        assert not OrderEvent.objects.exists()
        return

    new_event = OrderEvent.objects.last()  # type: OrderEvent
    assert new_event.type == expected_type
    assert new_event.user == staff_user
    expected_line_pk = None if new_quantity == 0 else str(line.pk)
    assert new_event.parameters == {
        "lines": [
            {
                "quantity": expected_quantity,
                "line_pk": expected_line_pk,
                "item": str(line),
            }
        ]
    }


def test_change_quantity_update_line_fields(
    order_with_lines,
    staff_user,
):
    # given
    line = order_with_lines.lines.last()
    line_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )
    new_quantity = 5
    app = None

    # when
    change_order_line_quantity(
        staff_user,
        app,
        line_info,
        line.quantity,
        new_quantity,
        order_with_lines.channel,
        get_plugins_manager(allow_replica=False),
    )

    # then
    line.refresh_from_db()
    assert line.quantity == new_quantity
    assert line.total_price == line.unit_price * new_quantity
    assert line.undiscounted_total_price == line.undiscounted_unit_price * new_quantity


def test_match_orders_with_new_user(order_list, staff_user, customer_user):
    # given
    for order in order_list[:2]:
        order.user = None
        order.user_email = staff_user.email

    order_with_user = order_list[-1]
    order_with_user.user = customer_user
    order_with_user.user_email = staff_user.email

    Order.objects.bulk_update(order_list, ["user", "user_email"])

    # when
    match_orders_with_new_user(staff_user)

    # then
    for order in order_list[:2]:
        order.refresh_from_db()
        assert order.user == staff_user

    order_with_user.refresh_from_db()
    assert order_with_user.user != staff_user


def test_match_draft_order_with_new_user(customer_user, channel_USD):
    address = customer_user.default_billing_address.get_copy()
    order = Order.objects.create(
        billing_address=address,
        user=None,
        user_email=customer_user.email,
        status=OrderStatus.DRAFT,
        channel=channel_USD,
    )
    match_orders_with_new_user(customer_user)

    order.refresh_from_db()
    assert order.user is None


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
        order,
        order.channel.shipping_method_listings.all(),
        get_plugins_manager(allow_replica=False),
    )

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
        order,
        order.channel.shipping_method_listings.all(),
        get_plugins_manager(allow_replica=False),
    )

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
        order,
        order.channel.shipping_method_listings.all(),
        get_plugins_manager(allow_replica=False),
    )

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
        order,
        order.channel.shipping_method_listings.all(),
        get_plugins_manager(allow_replica=False),
    )

    # then
    assert valid_shipping_methods == []


def test_add_variant_to_order(
    order,
    customer_user,
    variant,
    catalogue_promotion_with_single_rule,
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    quantity = 4

    promotion = catalogue_promotion_with_single_rule
    discount_value = promotion.rules.first().reward_value
    channel_listing = variant.channel_listings.get(channel=order.channel)
    channel_listing.discounted_price_amount = (
        channel_listing.price.amount - discount_value
    )
    channel_listing.save(update_fields=["discounted_price_amount"])

    base_unit_price = variant.get_price(channel_listing)
    unit_price = TaxedMoney(net=base_unit_price, gross=base_unit_price)
    total_price = unit_price * quantity

    undiscounted_base_unit_price = variant.get_base_price(channel_listing)
    undiscounted_unit_price = TaxedMoney(
        net=undiscounted_base_unit_price, gross=undiscounted_base_unit_price
    )
    undiscounted_total_price = undiscounted_unit_price * quantity

    # when
    line_data = OrderLineData(
        variant_id=str(variant.id), variant=variant, quantity=quantity
    )
    line = add_variant_to_order(
        order,
        line_data,
        customer_user,
        None,
        manager,
    )

    # then
    assert line.unit_price == unit_price
    assert line.total_price == total_price
    assert line.undiscounted_unit_price == undiscounted_unit_price
    assert line.undiscounted_total_price == undiscounted_total_price
    assert line.unit_price != line.undiscounted_unit_price
    assert line.undiscounted_unit_price != line.undiscounted_total_price


def test_add_gift_cards_to_order(
    checkout_with_item, gift_card, gift_card_expiry_date, order, staff_user
):
    # given
    checkout = checkout_with_item
    checkout.user = staff_user
    checkout.gift_cards.add(gift_card, gift_card_expiry_date)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    add_gift_cards_to_order(
        checkout_info, order, Money(30, gift_card.currency), staff_user, None
    )

    # then
    gift_card.refresh_from_db()
    gift_card_expiry_date.refresh_from_db()
    assert gift_card.current_balance_amount == 0
    assert gift_card_expiry_date.current_balance_amount == 0
    assert gift_card.used_by == staff_user
    assert gift_card.used_by_email == staff_user.email

    gift_card_events = GiftCardEvent.objects.filter(gift_card_id=gift_card.id)
    assert gift_card_events.count() == 1
    gift_card_event = gift_card_events[0]
    assert gift_card_event.type == GiftCardEvents.USED_IN_ORDER
    assert gift_card_event.user == staff_user
    assert gift_card_event.app is None
    assert gift_card_event.order == order
    assert gift_card_event.parameters == {
        "balance": {
            "currency": "USD",
            "current_balance": "0",
            "old_current_balance": "10.000",
        },
    }

    order_created_event = GiftCardEvent.objects.get(
        gift_card_id=gift_card_expiry_date.id
    )
    assert order_created_event.user == staff_user
    assert order_created_event.app is None
    assert order_created_event.order == order
    assert order_created_event.parameters == {
        "balance": {
            "currency": "USD",
            "current_balance": "0",
            "old_current_balance": "20.000",
        },
    }


def test_add_gift_cards_to_order_with_more_than_total(
    checkout_with_item, gift_card, gift_card_expiry_date, order, staff_user
):
    # given
    checkout = checkout_with_item
    checkout.user = staff_user
    checkout.gift_cards.add(gift_card_expiry_date, gift_card)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    add_gift_cards_to_order(
        checkout_info, order, Money(25, gift_card.currency), staff_user, None
    )

    # then
    gift_card.refresh_from_db()
    gift_card_expiry_date.refresh_from_db()
    assert gift_card.current_balance_amount == Decimal(5)
    assert gift_card_expiry_date.current_balance_amount == 0
    assert gift_card.used_by == staff_user
    assert gift_card.used_by_email == staff_user.email
    assert gift_card_expiry_date.used_by == staff_user
    assert gift_card_expiry_date.used_by_email == staff_user.email


def test_add_gift_cards_to_order_no_checkout_user(
    checkout_with_item, gift_card, gift_card_expiry_date, order, staff_user
):
    # given
    checkout = checkout_with_item
    checkout.user = None
    checkout.email = staff_user.email
    checkout.save(update_fields=["user", "email"])

    checkout.gift_cards.add(gift_card, gift_card_expiry_date)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    add_gift_cards_to_order(
        checkout_info, order, Money(30, gift_card.currency), staff_user, None
    )

    # then
    gift_card.refresh_from_db()
    gift_card_expiry_date.refresh_from_db()
    assert gift_card.current_balance_amount == 0
    assert gift_card_expiry_date.current_balance_amount == 0
    assert gift_card.used_by == staff_user
    assert gift_card.used_by_email == staff_user.email

    gift_card_events = GiftCardEvent.objects.filter(gift_card_id=gift_card.id)
    assert gift_card_events.count() == 1
    gift_card_event = gift_card_events[0]
    assert gift_card_event.type == GiftCardEvents.USED_IN_ORDER
    assert gift_card_event.user == staff_user
    assert gift_card_event.app is None
    assert gift_card_event.order == order
    assert gift_card_event.parameters == {
        "balance": {
            "currency": "USD",
            "current_balance": "0",
            "old_current_balance": "10.000",
        },
    }

    order_created_event = GiftCardEvent.objects.get(
        gift_card_id=gift_card_expiry_date.id
    )
    assert order_created_event.user == staff_user
    assert order_created_event.app is None
    assert order_created_event.order == order
    assert order_created_event.parameters == {
        "balance": {
            "currency": "USD",
            "current_balance": "0",
            "old_current_balance": "20.000",
        },
    }


def test_get_total_order_discount_excluding_shipping(order, voucher_shipping_type):
    # given
    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=Decimal("10.0"),
        name=voucher_shipping_type.code,
        currency="USD",
        amount_value=Decimal("10.0"),
    )
    manual_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=Decimal("10.0"),
        name=voucher_shipping_type.code,
        currency="USD",
        amount_value=Decimal("10.0"),
    )
    currency = order.currency
    total = TaxedMoney(Money(10, currency), Money(10, currency))
    order.voucher = voucher_shipping_type
    order.total = total
    order.undiscounted_total = total
    order.save()

    # when
    discount_amount = get_total_order_discount_excluding_shipping(order)

    # then
    assert discount_amount == Money(manual_discount.amount_value, order.currency)


def test_get_total_order_discount_excluding_shipping_no_shipping_discounts(
    order, voucher
):
    # given
    discount_1 = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=Decimal("10.0"),
        name=voucher.code,
        currency="USD",
        amount_value=Decimal("10.0"),
    )
    discount_2 = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=Decimal("10.0"),
        name=voucher.code,
        currency="USD",
        amount_value=Decimal("10.0"),
    )
    currency = order.currency
    total = TaxedMoney(Money(30, currency), Money(30, currency))
    order.voucher = voucher
    order.total = total
    order.undiscounted_total = total
    order.save()

    # when
    discount_amount = get_total_order_discount_excluding_shipping(order)

    # then
    assert discount_amount == Money(
        discount_1.amount_value + discount_2.amount_value, order.currency
    )


def test_update_order_display_gross_prices_use_default_tax_settings(order):
    # given
    tax_config = order.channel.tax_configuration
    tax_config.display_gross_prices = True
    tax_config.save()
    tax_config.country_exceptions.all().delete()

    order.display_gross_prices = False
    order.save(update_fields=["display_gross_prices"])

    # when
    update_order_display_gross_prices(order)

    # then
    assert order.display_gross_prices


def test_update_order_display_gross_prices_use_country_specific_tax_settings(order):
    # given
    country_code = "PT"
    tax_config = order.channel.tax_configuration
    tax_config.display_gross_prices = False
    tax_config.save()
    tax_config.country_exceptions.create(
        country=country_code, display_gross_prices=True
    )

    order.display_gross_prices = False
    order.save(update_fields=["display_gross_prices"])
    order.shipping_address.country = country_code
    order.shipping_address.save()

    # when
    update_order_display_gross_prices(order)

    # then
    assert order.display_gross_prices


def test_get_total_order_discount_excluding_shipping_no_discounts(order):
    # when
    discount_amount = get_total_order_discount_excluding_shipping(order)

    # then
    assert discount_amount == Money("0", order.currency)


def test_get_order_country_use_channel_country(order):
    # given
    order.shipping_address = order.billing_address = None
    order.save(update_fields=["shipping_address", "billing_address"])

    # when
    country = get_order_country(order)

    # then
    assert country == order.channel.default_country


def test_create_order_line_discounts(
    order_line,
    catalogue_promotion,
    promotion_translation_fr,
    promotion_rule_translation_fr,
):
    # given
    promotion = catalogue_promotion
    rules = promotion.rules.all()
    rule_1 = rules[0]
    rule_2 = rules[1]

    order = order_line.order
    variant = order_line.variant
    variant_channel_listing = variant.channel_listings.get(
        channel_id=order_line.order.channel_id
    )

    (
        listing_promotion_rule_1,
        listing_promotion_rule_2,
    ) = VariantChannelListingPromotionRule.objects.bulk_create(
        [
            VariantChannelListingPromotionRule(
                variant_channel_listing=variant_channel_listing,
                promotion_rule=rule_1,
                discount_amount=Decimal("10.0"),
                currency=order.currency,
            ),
            VariantChannelListingPromotionRule(
                variant_channel_listing=variant_channel_listing,
                promotion_rule=rule_2,
                discount_amount=Decimal("5.0"),
                currency=order.currency,
            ),
        ]
    )

    promotion_rule_translation_fr.promotion_rule = rule_1
    promotion_rule_translation_fr.save(update_fields=["promotion_rule"])

    rules_info = [
        VariantPromotionRuleInfo(
            rule=rule_1,
            variant_listing_promotion_rule=listing_promotion_rule_1,
            promotion=promotion,
            promotion_translation=promotion_translation_fr,
            rule_translation=promotion_rule_translation_fr,
        ),
        VariantPromotionRuleInfo(
            rule=rule_2,
            variant_listing_promotion_rule=listing_promotion_rule_2,
            promotion=promotion,
            promotion_translation=promotion_translation_fr,
            rule_translation=None,
        ),
    ]

    # when
    line_discounts = create_order_line_discounts(order_line, rules_info)

    # then
    assert len(line_discounts) == 2
    discount_1, discount_2 = line_discounts

    for discount in [discount_1, discount_2]:
        assert discount.line == order_line
        assert discount.type == DiscountType.CATALOGUE_PROMOTION
        assert discount.currency == order.currency
        assert discount.reason is None

    assert discount_1.amount_value == listing_promotion_rule_1.discount_amount
    assert discount_1.value_type == rule_1.reward_value_type
    assert discount_1.value == rule_1.reward_value
    assert discount_1.name == f"{promotion.name}: {rule_1.name}"
    assert (
        discount_1.translated_name
        == f"{promotion_translation_fr.name}: {promotion_rule_translation_fr.name}"
    )
    assert discount_1.promotion_rule == rule_1

    assert discount_2.amount_value == listing_promotion_rule_2.discount_amount
    assert discount_2.value_type == rule_2.reward_value_type
    assert discount_2.value == rule_2.reward_value
    assert discount_2.name == f"{promotion.name}: {rule_2.name}"
    assert discount_2.translated_name == f"{promotion_translation_fr.name}"
    assert discount_2.promotion_rule == rule_2
