from decimal import Decimal

import pytest

from .....checkout import calculations
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.utils import add_voucher_code_to_checkout
from .....discount import DiscountValueType, RewardValueType
from .....discount.models import PromotionRule
from .....order import OrderOrigin, OrderStatus
from .....order.models import Order
from .....plugins.manager import get_plugins_manager
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_CHECKOUT_COMPLETE = """
    mutation checkoutComplete(
        $id: ID,
        $redirectUrl: String,
    ) {
        checkoutComplete(
            id: $id,
            redirectUrl: $redirectUrl,
        ) {
            order {
                id
            }
            errors {
                field,
                message,
                code
            }
        }
    }
    """


def test_checkout_complete_price_override(
    user_api_client,
    checkout_with_item,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    line = checkout.lines.first()
    price_override = Decimal(2)
    line.price_override = price_override
    line.save(update_fields=["price_override"])
    quantity = line.quantity

    channel = checkout.channel
    channel.allow_unpaid_orders = True
    channel.save(update_fields=["allow_unpaid_orders"])

    shipping_price = shipping_method.channel_listings.get().price_amount
    subtotal = price_override * quantity
    total = subtotal + shipping_price

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.get()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.origin == OrderOrigin.CHECKOUT
    assert order.subtotal_net_amount == subtotal
    assert order.shipping_price_net_amount == shipping_price
    assert order.total_net_amount == total
    assert order.undiscounted_total_net_amount == total

    order_line = order.lines.get()
    assert order_line.is_price_overridden
    assert order_line.base_unit_price_amount == price_override
    assert order_line.total_price_net_amount == subtotal
    assert order_line.undiscounted_total_price_net_amount == subtotal
    assert order_line.undiscounted_unit_price_net_amount == price_override


@pytest.mark.parametrize(("price_override", "reward"), [(100, 30), (2, 10), (5, 5)])
def test_checkout_complete_with_price_override_and_catalogue_promotion_fixed(
    price_override,
    reward,
    user_api_client,
    checkout_with_item_on_promotion,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_item_on_promotion
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    line = checkout.lines.first()
    line.price_override = price_override
    line.save(update_fields=["price_override"])
    quantity = line.quantity

    channel = checkout.channel
    channel.allow_unpaid_orders = True
    channel.save(update_fields=["allow_unpaid_orders"])

    rule = PromotionRule.objects.get()
    assert rule.reward_value_type == RewardValueType.FIXED
    rule.reward_value = reward
    rule.save(update_fields=["reward_value"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    _ = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    shipping_price = shipping_method.channel_listings.get().price_amount
    base_unit_price = max(price_override - reward, Decimal(0))
    subtotal = base_unit_price * quantity
    total = subtotal + shipping_price
    undiscounted_subtotal = price_override * quantity
    undiscounted_total = undiscounted_subtotal + shipping_price
    discount_amount = undiscounted_subtotal - subtotal

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.get()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.origin == OrderOrigin.CHECKOUT
    assert order.subtotal_net_amount == subtotal
    assert order.shipping_price_net_amount == shipping_price
    assert order.total_net_amount == total
    assert order.undiscounted_total_net_amount == undiscounted_total

    order_line = order.lines.get()
    assert order_line.is_price_overridden
    assert order_line.undiscounted_base_unit_price_amount == price_override
    assert order_line.base_unit_price_amount == base_unit_price
    assert order_line.total_price_net_amount == subtotal
    assert order_line.undiscounted_total_price_net_amount == undiscounted_subtotal
    assert order_line.unit_discount_amount == min(price_override, reward)

    line_discount = order_line.discounts.get()
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.value == reward
    assert line_discount.amount_value == discount_amount


@pytest.mark.parametrize(("price_override", "reward"), [(40, 50), (4, 25), (7, 100)])
def test_checkout_complete_with_price_override_and_catalogue_promotion_percentage(
    price_override,
    reward,
    user_api_client,
    checkout_with_item_on_promotion,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_item_on_promotion
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    line = checkout.lines.first()
    line.price_override = price_override
    line.save(update_fields=["price_override"])
    quantity = line.quantity

    channel = checkout.channel
    channel.allow_unpaid_orders = True
    channel.save(update_fields=["allow_unpaid_orders"])

    rule = PromotionRule.objects.get()
    rule.reward_value_type = RewardValueType.PERCENTAGE
    rule.reward_value = reward
    rule.save(update_fields=["reward_value", "reward_value_type"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    _ = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    shipping_price = shipping_method.channel_listings.get().price_amount
    unit_discount = Decimal(price_override * reward / 100)
    base_unit_price = price_override - unit_discount
    subtotal = base_unit_price * quantity
    total = subtotal + shipping_price
    undiscounted_subtotal = Decimal(price_override * quantity)
    undiscounted_total = undiscounted_subtotal + shipping_price
    discount_amount = undiscounted_subtotal - subtotal

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.get()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.origin == OrderOrigin.CHECKOUT
    assert order.subtotal_net_amount == subtotal
    assert order.shipping_price_net_amount == shipping_price
    assert order.total_net_amount == total
    assert order.undiscounted_total_net_amount == undiscounted_total

    order_line = order.lines.get()
    assert order_line.is_price_overridden
    assert order_line.undiscounted_base_unit_price_amount == price_override
    assert order_line.base_unit_price_amount == base_unit_price
    assert order_line.total_price_net_amount == subtotal
    assert order_line.undiscounted_total_price_net_amount == undiscounted_subtotal
    assert order_line.unit_discount_amount == unit_discount

    line_discount = order_line.discounts.get()
    assert line_discount.value_type == DiscountValueType.PERCENTAGE
    assert line_discount.value == reward
    assert line_discount.amount_value == discount_amount


@pytest.mark.parametrize(("price_override", "reward"), [(30, 60), (5, 60), (5, 12)])
def test_checkout_complete_with_price_override_and_voucher_entire_order(
    price_override,
    reward,
    user_api_client,
    checkout_with_item,
    address,
    shipping_method,
    voucher,
):
    # given
    voucher_channel_listings = voucher.channel_listings.first()
    voucher_channel_listings.discount_value = reward
    voucher_channel_listings.save(update_fields=["discount_value"])
    voucher_code = voucher.codes.first().code

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.voucher_code = voucher_code
    checkout.save()

    line = checkout.lines.first()
    line.price_override = price_override
    line.save(update_fields=["price_override"])
    quantity = line.quantity

    channel = checkout.channel
    channel.allow_unpaid_orders = True
    channel.save(update_fields=["allow_unpaid_orders"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    add_voucher_code_to_checkout(manager, checkout_info, lines, voucher_code)

    shipping_price = shipping_method.channel_listings.get().price_amount
    base_unit_price = price_override
    subtotal = max(base_unit_price * quantity - reward, Decimal(0))
    total = subtotal + shipping_price
    undiscounted_subtotal = price_override * quantity
    undiscounted_total = undiscounted_subtotal + shipping_price
    unit_discount = Decimal((undiscounted_subtotal - subtotal) / quantity)
    discount_amount = undiscounted_subtotal - subtotal

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.get()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.origin == OrderOrigin.CHECKOUT
    assert order.subtotal_net_amount == subtotal
    assert order.shipping_price_net_amount == shipping_price
    assert order.total_net_amount == total
    assert order.undiscounted_total_net_amount == undiscounted_total

    order_line = order.lines.get()
    assert order_line.is_price_overridden
    assert order_line.undiscounted_base_unit_price_amount == price_override
    assert order_line.base_unit_price_amount == base_unit_price
    assert order_line.total_price_net_amount == subtotal
    assert order_line.undiscounted_total_price_net_amount == undiscounted_subtotal
    assert order_line.unit_discount_amount == unit_discount

    order_discount = order.discounts.get()
    assert order_discount.value == discount_amount
    assert order_discount.amount_value == discount_amount


def test_checkout_complete_with_price_override_and_voucher_free_shipping(
    user_api_client,
    checkout_with_item,
    address,
    shipping_method,
    voucher_free_shipping,
):
    # given
    voucher_code = voucher_free_shipping.codes.first().code

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.voucher_code = voucher_code
    checkout.save()

    line = checkout.lines.first()
    price_override = Decimal(1)
    line.price_override = price_override
    line.save(update_fields=["price_override"])
    quantity = line.quantity

    channel = checkout.channel
    channel.allow_unpaid_orders = True
    channel.save(update_fields=["allow_unpaid_orders"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    add_voucher_code_to_checkout(manager, checkout_info, lines, voucher_code)

    undiscounted_shipping_price = shipping_method.channel_listings.get().price_amount
    shipping_price = Decimal(0)
    base_unit_price = price_override
    subtotal = base_unit_price * quantity
    total = subtotal + shipping_price
    undiscounted_subtotal = price_override * quantity
    undiscounted_total = undiscounted_subtotal + undiscounted_shipping_price
    unit_discount = Decimal((undiscounted_subtotal - subtotal) / quantity)

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.get()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.origin == OrderOrigin.CHECKOUT
    assert order.subtotal_net_amount == subtotal
    assert order.shipping_price_net_amount == shipping_price
    assert order.total_net_amount == total
    assert order.undiscounted_total_net_amount == undiscounted_total

    order_line = order.lines.get()
    assert order_line.is_price_overridden
    assert order_line.undiscounted_base_unit_price_amount == price_override
    assert order_line.base_unit_price_amount == base_unit_price
    assert order_line.total_price_net_amount == subtotal
    assert order_line.undiscounted_total_price_net_amount == undiscounted_subtotal
    assert order_line.unit_discount_amount == unit_discount

    order_discount = order.discounts.get()
    assert order_discount.value == undiscounted_shipping_price
    assert order_discount.amount_value == undiscounted_shipping_price


@pytest.mark.parametrize(("price_override", "reward"), [(100, 30), (30, 100), (5, 5)])
def test_checkout_complete_with_price_override_and_voucher_specific_product(
    price_override,
    reward,
    user_api_client,
    checkout_with_item,
    address,
    shipping_method,
    voucher_specific_product_type,
):
    # given
    voucher = voucher_specific_product_type
    voucher_code = voucher.codes.first().code
    voucher_channel_listings = voucher.channel_listings.first()
    voucher_channel_listings.discount_value = reward
    voucher_channel_listings.save(update_fields=["discount_value"])

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.voucher_code = voucher_code
    checkout.save()

    line = checkout.lines.first()
    line.price_override = price_override
    line.save(update_fields=["price_override"])
    quantity = line.quantity

    channel = checkout.channel
    channel.allow_unpaid_orders = True
    channel.save(update_fields=["allow_unpaid_orders"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    add_voucher_code_to_checkout(manager, checkout_info, lines, voucher_code)

    shipping_price = shipping_method.channel_listings.get().price_amount
    unit_discount = Decimal(price_override * reward / 100)
    base_unit_price = price_override - unit_discount
    subtotal = base_unit_price * quantity
    total = subtotal + shipping_price
    undiscounted_subtotal = Decimal(price_override * quantity)
    undiscounted_total = undiscounted_subtotal + shipping_price

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.get()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.origin == OrderOrigin.CHECKOUT
    assert order.subtotal_net_amount == subtotal
    assert order.shipping_price_net_amount == shipping_price
    assert order.total_net_amount == total
    assert order.undiscounted_total_net_amount == undiscounted_total

    order_line = order.lines.get()
    assert order_line.is_price_overridden
    assert order_line.undiscounted_base_unit_price_amount == price_override
    assert order_line.base_unit_price_amount == base_unit_price
    assert order_line.total_price_net_amount == subtotal
    assert order_line.undiscounted_total_price_net_amount == undiscounted_subtotal
    assert order_line.unit_discount_amount == unit_discount

    # TODO: fix OrderDiscount object values for specific product voucher with overriden
    #  prices
    # order_discount = order.discounts.get()
    # assert order_discount.amount_value == unit_discount * quantity


@pytest.mark.parametrize(
    ("price_override", "reward", "threshold"),
    [(30, 60, 50), (5, 60, 10), (5, 12, 10), (5, 12, 100)],
)
def test_checkout_complete_with_price_override_and_order_promotion(
    price_override,
    reward,
    threshold,
    user_api_client,
    checkout_with_item,
    order_promotion_with_rule,
    address,
    shipping_method,
):
    # given
    promotion = order_promotion_with_rule
    rule = promotion.rules.first()
    rule.order_predicate = {
        "discountedObjectPredicate": {
            "baseSubtotalPrice": {"range": {"gte": threshold}}
        }
    }
    rule.reward_value = reward
    rule.save(update_fields=["order_predicate", "reward_value"])

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    line = checkout.lines.first()
    line.price_override = price_override
    line.save(update_fields=["price_override"])
    quantity = line.quantity

    channel = checkout.channel
    channel.allow_unpaid_orders = True
    channel.save(update_fields=["allow_unpaid_orders"])

    shipping_price = shipping_method.channel_listings.get().price_amount
    base_unit_price = price_override
    undiscounted_subtotal = price_override * quantity
    reward = reward if undiscounted_subtotal > threshold else Decimal(0)
    subtotal = max(base_unit_price * quantity - reward, Decimal(0))
    total = subtotal + shipping_price
    undiscounted_total = undiscounted_subtotal + shipping_price
    discount_amount = undiscounted_subtotal - subtotal
    unit_discount = Decimal(discount_amount / quantity)

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.get()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.origin == OrderOrigin.CHECKOUT
    assert order.subtotal_net_amount == subtotal
    assert order.shipping_price_net_amount == shipping_price
    assert order.total_net_amount == total
    assert order.undiscounted_total_net_amount == undiscounted_total

    order_line = order.lines.get()
    assert order_line.is_price_overridden
    assert order_line.undiscounted_base_unit_price_amount == price_override
    assert order_line.base_unit_price_amount == base_unit_price
    assert order_line.total_price_net_amount == subtotal
    assert order_line.undiscounted_total_price_net_amount == undiscounted_subtotal
    assert order_line.unit_discount_amount == unit_discount

    if undiscounted_subtotal > threshold:
        order_discount = order.discounts.get()
        assert order_discount.value == reward
        assert order_discount.amount_value == discount_amount


@pytest.mark.parametrize(("price_override"), [30, 5])
def test_checkout_complete_with_price_override_and_gift_promotion(
    price_override,
    user_api_client,
    checkout_with_item,
    gift_promotion_rule,
    address,
    shipping_method,
    digital_content,
):
    # given
    rule = gift_promotion_rule
    gift = digital_content.product_variant
    rule.gifts.set([gift])
    gift_price = Decimal(10)
    assert gift.channel_listings.get().price_amount == gift_price
    threshold = rule.order_predicate["discountedObjectPredicate"]["baseSubtotalPrice"][
        "range"
    ]["gte"]
    assert threshold == Decimal(20)

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    line = checkout.lines.first()
    line.price_override = price_override
    line.save(update_fields=["price_override"])
    quantity = line.quantity

    channel = checkout.channel
    channel.allow_unpaid_orders = True
    channel.save(update_fields=["allow_unpaid_orders"])

    shipping_price = shipping_method.channel_listings.get().price_amount
    base_unit_price = price_override
    subtotal = base_unit_price * quantity
    total = subtotal + shipping_price
    reward = gift_price if threshold <= subtotal else Decimal(0)
    undiscounted_subtotal = subtotal + reward
    undiscounted_total = undiscounted_subtotal + shipping_price

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.get()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.origin == OrderOrigin.CHECKOUT
    assert order.subtotal_net_amount == subtotal
    assert order.shipping_price_net_amount == shipping_price
    assert order.total_net_amount == total
    assert order.undiscounted_total_net_amount == undiscounted_total

    order_lines = order.lines.all()
    order_line = order_lines.filter(quantity=quantity).get()
    assert order_line.is_price_overridden
    assert order_line.undiscounted_base_unit_price_amount == price_override
    assert order_line.base_unit_price_amount == base_unit_price
    assert order_line.total_price_net_amount == subtotal
    assert order_line.undiscounted_total_price_net_amount == subtotal
    assert order_line.unit_discount_amount == Decimal(0)

    if subtotal >= threshold:
        gift_line = order_lines.filter(is_gift=True).get()
        assert not gift_line.is_price_overridden
        assert gift_line.undiscounted_base_unit_price_amount == gift_price
        assert gift_line.undiscounted_total_price_net_amount == gift_price
        assert gift_line.base_unit_price_amount == Decimal(0)
        assert gift_line.total_price_net_amount == Decimal(0)
        assert gift_line.unit_discount_amount == gift_price
        assert gift_line.unit_discount_value == gift_price


def test_checkout_complete_with_price_override_and_catalogue_promotion_and_entire_order_voucher(
    user_api_client,
    checkout_with_item_on_promotion,
    address,
    shipping_method,
    voucher,
):
    # given
    price_override = 30
    catalogue_reward = 10
    voucher_reward = 30

    voucher_channel_listings = voucher.channel_listings.first()
    voucher_channel_listings.discount_value = voucher_reward
    voucher_channel_listings.save(update_fields=["discount_value"])
    voucher_code = voucher.codes.first().code

    checkout = checkout_with_item_on_promotion
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    line = checkout.lines.first()
    line.price_override = price_override
    line.save(update_fields=["price_override"])
    quantity = line.quantity

    channel = checkout.channel
    channel.allow_unpaid_orders = True
    channel.save(update_fields=["allow_unpaid_orders"])

    rule = PromotionRule.objects.get()
    assert rule.reward_value_type == RewardValueType.FIXED
    rule.reward_value = catalogue_reward
    rule.save(update_fields=["reward_value"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    add_voucher_code_to_checkout(manager, checkout_info, lines, voucher_code)
    _ = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    shipping_price = shipping_method.channel_listings.get().price_amount
    base_unit_price = max(price_override - catalogue_reward, Decimal(0))
    undiscounted_subtotal = price_override * quantity
    undiscounted_total = undiscounted_subtotal + shipping_price
    subtotal = base_unit_price * quantity - voucher_reward
    total = subtotal + shipping_price

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.get()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.origin == OrderOrigin.CHECKOUT
    assert order.subtotal_net_amount == subtotal
    assert order.shipping_price_net_amount == shipping_price
    assert order.total_net_amount == total
    assert order.undiscounted_total_net_amount == undiscounted_total

    order_line = order.lines.get()
    assert order_line.is_price_overridden
    assert order_line.undiscounted_base_unit_price_amount == price_override
    assert order_line.base_unit_price_amount == base_unit_price
    assert order_line.total_price_net_amount == subtotal
    assert order_line.undiscounted_total_price_net_amount == undiscounted_subtotal
    assert (
        order_line.unit_discount_amount == catalogue_reward + voucher_reward / quantity
    )

    line_discount = order_line.discounts.get()
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.value == catalogue_reward
    assert line_discount.amount_value == quantity * catalogue_reward

    order_discount = order.discounts.get()
    assert order_discount.value == voucher_reward
    assert order_discount.amount_value == voucher_reward
