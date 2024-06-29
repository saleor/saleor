import datetime
from decimal import Decimal
from unittest import mock

import graphene
import pytest
from django.utils import timezone

from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout, CheckoutLine
from .....checkout.utils import (
    add_variant_to_checkout,
    calculate_checkout_quantity,
    invalidate_checkout,
)
from .....discount import RewardValueType
from .....plugins.manager import get_plugins_manager
from .....product.models import ProductChannelListing
from .....warehouse.models import Reservation, Stock
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content
from ...mutations.utils import update_checkout_shipping_method_if_invalid

MUTATION_CHECKOUT_LINES_UPDATE = """
    mutation checkoutLinesUpdate(
            $id: ID, $lines: [CheckoutLineUpdateInput!]!) {
        checkoutLinesUpdate(id: $id, lines: $lines) {
            checkout {
                id
                token
                quantity
                lines {
                    quantity
                    variant {
                        id
                    }
                    undiscountedUnitPrice {
                        amount
                    }
                    unitPrice {
                        gross {
                            amount
                        }
                    }
                }
                totalPrice {
                    gross {
                        amount
                    }
                    net {
                        amount
                    }
                }
                discount {
                    amount
                }
            }
            errors {
                field
                code
                message
                variants
                lines
            }
        }
    }
    """


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_lines_update(
    mocked_invalidate_checkout,
    mocked_update_shipping_method,
    user_api_client,
    checkout_with_item,
):
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3
    previous_last_change = checkout.last_change

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1
    assert calculate_checkout_quantity(lines) == 1

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout.call_count == 1


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_lines_update_using_line_id(
    mocked_update_shipping_method, user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3
    previous_last_change = checkout.last_change

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"lineId": line_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1
    assert calculate_checkout_quantity(lines) == 1

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_lines_update_using_line_id_and_variant_id(
    mocked_update_shipping_method, user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3
    previous_last_change = checkout.last_change

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [
            {"lineId": line_id, "quantity": 1},
            {"variantId": variant_id, "quantity": 1},
        ],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 2
    assert calculate_checkout_quantity(lines) == 2

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change


def test_checkout_lines_update_block_when_variant_id_and_same_variant_in_multiple_lines(
    user_api_client, checkout_with_same_items_in_multiple_lines
):
    # given
    checkout = checkout_with_same_items_in_multiple_lines
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 2
    assert calculate_checkout_quantity(lines) == 2
    line = checkout.lines.first()
    variant = line.variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 2}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]

    # then

    assert data["errors"][0]["code"] == CheckoutErrorCode.INVALID.name
    assert data["errors"][0]["field"] == "variantId"


def test_checkout_lines_update_block_when_variant_id_and_line_id_provided(
    user_api_client, checkout_with_item
):
    # given
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "lineId": line_id, "quantity": 2}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    expected_message = "Argument 'line_id' cannot be combined with 'variant_id'"

    # then
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
    assert data["errors"][0]["message"] == expected_message


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_lines_update_only_stock_in_cc_warehouse(
    mocked_update_shipping_method, user_api_client, checkout_with_item, warehouse_for_cc
):
    """Test that click-and-collect quantities are available if no shipping method is set."""
    # given
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant

    variant.stocks.all().delete()

    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=10
    )

    assert line.quantity == 3
    previous_last_change = checkout.last_change

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1
    assert calculate_checkout_quantity(lines) == 1

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change


def test_checkout_lines_update_only_stock_in_cc_warehouse_delivery_method_set(
    user_api_client, checkout_with_item, warehouse_for_cc, shipping_method
):  # given
    """Test that click-and-collect quantities are unavailable if a non-C&C shipping method is set."""
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant = line.variant

    variant.stocks.all().delete()

    # set stock for a collection point warehouse
    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=10
    )

    checkout.shipping_method = shipping_method
    checkout.save(update_fields=["shipping_method"])

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]
    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert data["errors"][0]["field"] == "quantity"


def test_checkout_lines_update_checkout_with_voucher(
    user_api_client, checkout_with_item, voucher_percentage
):
    # given
    channel = checkout_with_item.channel
    line = checkout_with_item.lines.first()
    variant = line.variant

    channel_listing = variant.channel_listings.get(channel=channel)
    unit_price = variant.get_price(channel_listing)

    voucher_channel_listing = voucher_percentage.channel_listings.get(channel=channel)
    voucher_channel_listing.discount_value = 100
    voucher_channel_listing.save(update_fields=["discount_value"])

    checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.discount_amount = (unit_price * line.quantity).amount
    checkout_with_item.save()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout_data = data["checkout"]
    total_price_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_price_gross_amount == 0
    assert checkout_data["discount"]["amount"] == unit_price.amount

    checkout_with_item.refresh_from_db()
    assert checkout_with_item.discount_amount == unit_price.amount


def test_checkout_lines_update_with_new_reservations(
    site_settings_with_reservations,
    user_api_client,
    checkout_line_with_reservation_in_many_stocks,
):
    assert Reservation.objects.count() == 2
    checkout = checkout_line_with_reservation_in_many_stocks.checkout
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3

    Stock.objects.filter(
        warehouse__shipping_zones__countries__contains="US", product_variant=variant
    ).update(quantity=3)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1
    assert calculate_checkout_quantity(lines) == 1

    reservation = checkout_line_with_reservation_in_many_stocks.reservations.first()
    assert reservation.quantity_reserved == line.quantity

    assert Reservation.objects.count() == 1


def test_checkout_lines_update_against_reserved_stock(
    site_settings_with_reservations,
    user_api_client,
    checkout_line,
    stock,
    channel_USD,
):
    assert Reservation.objects.count() == 0
    checkout = checkout_line.checkout
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    variant = checkout_line.variant
    assert checkout_line.quantity == 3

    other_checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    other_checkout_line = other_checkout.lines.create(
        variant=variant,
        quantity=7,
    )
    reservation = Reservation.objects.create(
        checkout_line=other_checkout_line,
        stock=variant.stocks.first(),
        quantity_reserved=7,
        reserved_until=timezone.now() + datetime.timedelta(minutes=5),
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 5}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert data["errors"]
    assert data["errors"][0]["message"] == (
        "Could not add items 123. Only 3 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"

    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 3
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 3
    reservation.refresh_from_db()
    assert Reservation.objects.count() == 1


def test_checkout_lines_update_other_lines_reservations_expirations(
    site_settings_with_reservations,
    user_api_client,
    checkout_line_with_one_reservation,
    product,
    warehouse,
):
    variant = checkout_line_with_one_reservation.variant
    checkout = checkout_line_with_one_reservation.checkout
    line = checkout_line_with_one_reservation
    reservation = line.reservations.get()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 2

    variant_other = product.variants.create(sku="SKU_B")
    variant_other.channel_listings.create(
        channel=checkout.channel,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=checkout.channel.currency_code,
    )
    Stock.objects.create(
        product_variant=variant_other, warehouse=warehouse, quantity=15
    )
    add_variant_to_checkout(checkout_info, variant_other, 2)
    variant_other_id = graphene.Node.to_global_id("ProductVariant", variant_other.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_other_id, "quantity": 3}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]
    reservation.refresh_from_db()

    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    line.refresh_from_db()
    assert line.variant == variant
    assert line.quantity == 2
    new_line = checkout.lines.get(variant=variant_other)
    assert new_line.variant == variant_other
    assert new_line.quantity == 3
    assert calculate_checkout_quantity(lines) == 5

    other_reservation = Reservation.objects.get(checkout_line__variant=variant_other)
    assert other_reservation.checkout_line == new_line
    assert other_reservation.quantity_reserved == new_line.quantity

    assert reservation.reserved_until == other_reservation.reserved_until


def test_checkout_lines_update_quantity_and_custom_price(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    price = Decimal("22.22")

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"variantId": variant_id, "quantity": 1, "price": price}],
    }
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1
    assert line.price_override == price
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 1


def test_checkout_lines_update_custom_price(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant
    previous_quantity = line.quantity

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    price = Decimal("22.22")

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"variantId": variant_id, "price": price}],
    }
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == previous_quantity
    assert line.price_override == price
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 3


def test_checkout_lines_update_with_custom_price_override_existing_price(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    line.price_override = Decimal("10.12")
    line.save(update_fields=["price_override"])
    variant = line.variant
    assert line.quantity == 3

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    price = Decimal("22.10")

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"variantId": variant_id, "quantity": 1, "price": price}],
    }
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1
    assert line.price_override == price
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 1


def test_checkout_lines_update_with_custom_price_and_fixed_catalogue_promotion(
    app_api_client, checkout_with_item_on_promotion, permission_handle_checkouts
):
    # given
    checkout = checkout_with_item_on_promotion

    assert checkout.lines.count() == 1

    line = checkout.lines.first()
    old_line_qty = line.quantity
    line_qty = 1
    assert line_qty != old_line_qty
    line_discount = line.discounts.first()
    old_line_discount_amount_value = line_discount.amount_value
    reward_value = line_discount.value

    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant_id)
    custom_price = Decimal("15")

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [
            {"variantId": variant_id, "quantity": line_qty, "price": custom_price}
        ],
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE,
        variables,
        permissions=[permission_handle_checkouts],
    )

    # then
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout_data = data["checkout"]
    assert checkout_data["totalPrice"]["gross"]["amount"] == custom_price - reward_value
    assert len(checkout_data["lines"]) == 1
    line_data = data["checkout"]["lines"][0]
    assert line_data["quantity"] == line_qty
    assert line_data["undiscountedUnitPrice"]["amount"] == custom_price
    assert line_data["unitPrice"]["gross"]["amount"] == custom_price - reward_value

    line_discount.refresh_from_db()
    assert line_discount.amount_value == reward_value
    assert line_discount.amount_value != old_line_discount_amount_value


def test_checkout_lines_update_with_custom_price_and_percentage_catalogue_promotion(
    app_api_client, checkout_with_item_on_promotion, permission_handle_checkouts
):
    # given
    checkout = checkout_with_item_on_promotion

    assert checkout.lines.count() == 1

    line = checkout.lines.first()
    old_line_qty = line.quantity
    line_qty = 2
    assert line_qty != old_line_qty
    line_discount = line.discounts.first()
    old_line_discount_amount_value = line_discount.amount_value

    promotion_rule = line_discount.promotion_rule
    reward_value_type = RewardValueType.PERCENTAGE
    reward_value = Decimal("50")
    promotion_rule.reward_value_type = reward_value_type
    promotion_rule.reward_value = reward_value
    promotion_rule.save(update_fields=["reward_value_type", "reward_value"])

    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant_id)
    custom_price = Decimal("40")

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [
            {"variantId": variant_id, "quantity": line_qty, "price": custom_price}
        ],
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE,
        variables,
        permissions=[permission_handle_checkouts],
    )

    # then
    content = get_graphql_content(response)
    unit_discount_amount = custom_price * promotion_rule.reward_value / 100
    discount_amount = unit_discount_amount * line_qty

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout_data = data["checkout"]
    assert (
        checkout_data["totalPrice"]["gross"]["amount"]
        == custom_price * line_qty - discount_amount
    )
    assert len(checkout_data["lines"]) == 1
    line_data = data["checkout"]["lines"][0]
    assert line_data["quantity"] == line_qty
    assert line_data["undiscountedUnitPrice"]["amount"] == custom_price
    assert (
        line_data["unitPrice"]["gross"]["amount"] == custom_price - unit_discount_amount
    )

    line_discount.refresh_from_db()
    assert line_discount.amount_value == discount_amount
    assert line_discount.amount_value != old_line_discount_amount_value
    assert line_discount.value == reward_value
    assert line_discount.value_type == reward_value_type


def test_checkout_lines_update_with_0_custom_price_and_catalogue_promotion(
    app_api_client, checkout_with_item_on_promotion, permission_handle_checkouts
):
    # given
    checkout = checkout_with_item_on_promotion

    assert checkout.lines.count() == 1

    line = checkout.lines.first()
    old_line_qty = line.quantity
    line_qty = 1
    assert line_qty != old_line_qty
    line_discount = line.discounts.first()

    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant_id)
    custom_price = Decimal("0")

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [
            {"variantId": variant_id, "quantity": line_qty, "price": custom_price}
        ],
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE,
        variables,
        permissions=[permission_handle_checkouts],
    )

    # then
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout_data = data["checkout"]
    assert checkout_data["totalPrice"]["gross"]["amount"] == 0
    assert len(checkout_data["lines"]) == 1
    line_data = data["checkout"]["lines"][0]
    assert line_data["quantity"] == line_qty
    assert line_data["undiscountedUnitPrice"]["amount"] == 0
    assert line_data["unitPrice"]["gross"]["amount"] == 0

    line_discount.refresh_from_db()
    assert line_discount.amount_value == 0


def test_checkout_lines_update_clear_custom_price(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    line.price_override = Decimal("10.12")
    line.save(update_fields=["price_override"])
    variant = line.variant
    assert line.quantity == 3

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"variantId": variant_id, "quantity": 1, "price": None}],
    }
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1
    assert line.price_override is None
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 1


def test_checkout_lines_update_set_quantity_to_0_then_update_customer_price(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    line.price_override = Decimal("10.12")
    line.save(update_fields=["price_override"])
    variant = line.variant
    assert line.quantity == 3

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [
            {"variantId": variant_id, "quantity": 0},
            {"variantId": variant_id, "price": 10},
        ],
    }
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 0
    with pytest.raises(CheckoutLine.DoesNotExist):
        line.refresh_from_db()


def test_checkout_lines_update_with_custom_price_by_app_no_perm(
    app_api_client, checkout_with_item
):
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    price = Decimal("22.22")

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"variantId": variant_id, "quantity": 1, "price": price}],
    }
    response = app_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    assert_no_permission(response)


def test_checkout_lines_update_with_custom_price_raise_permission_denied_for_staff(
    staff_api_client, checkout_with_item, permission_handle_checkouts
):
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    price = Decimal("22.22")

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"variantId": variant_id, "quantity": 1, "price": price}],
    }
    response = staff_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE,
        variables,
        permissions=[permission_handle_checkouts],
    )
    assert_no_permission(response)


def test_checkout_lines_update_no_quantity_provided(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [{"variantId": variant_id}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert errors[0]["field"] == "quantity"


def test_checkout_lines_update_with_unavailable_variant(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    previous_last_change = checkout.last_change
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    variant = line.variant
    variant.channel_listings.filter(channel=checkout_with_item.channel).update(
        price_amount=None
    )
    assert line.quantity == 3

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    errors = content["data"]["checkoutLinesUpdate"]["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [variant_id]
    checkout.refresh_from_db()
    assert checkout.last_change == previous_last_change


def test_checkout_lines_update_channel_without_shipping_zones(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    checkout.channel.shipping_zones.clear()
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


def test_checkout_lines_update_variant_quantity_over_avability_stock(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)
    current_stock = line.variant.stocks.first()
    line.quantity = current_stock.quantity - 1
    line.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": current_stock.quantity - 2}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]
    assert data["checkout"]["lines"][0]["quantity"] == variables["lines"][0]["quantity"]


def test_checkout_lines_delete_with_by_zero_quantity_when_variant_out_of_stock(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)
    stock = line.variant.stocks.first()
    stock.quantity = 0
    stock.save(update_fields=["quantity"])
    previous_last_change = checkout.last_change

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 0}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]
    assert not data["checkout"]["lines"]
    checkout.refresh_from_db()
    assert checkout.last_change != previous_last_change


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_line_delete_by_zero_quantity(
    mocked_update_shipping_method, user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3
    previous_last_change = checkout.last_change

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 0}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 0
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_line_delete_by_zero_quantity_when_variant_unavailable_for_purchase(
    mocked_update_shipping_method, user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3
    variant.channel_listings.all().delete()
    variant.product.channel_listings.all().delete()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 0}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 0
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_line_update_by_zero_quantity_dont_create_new_lines(
    mocked_update_shipping_method,
    user_api_client,
    checkout_with_item,
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant = line.variant
    checkout.lines.all().delete()
    assert checkout.lines.count() == 0
    previous_last_change = checkout.last_change

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 0}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 0
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change


def test_checkout_lines_update_with_unpublished_product(
    user_api_client, checkout_with_item, channel_USD
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant = line.variant
    product = variant.product
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)

    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesUpdate"]["errors"][0]
    assert error["code"] == CheckoutErrorCode.PRODUCT_NOT_PUBLISHED.name


def test_checkout_lines_update_invalid_checkout_id(user_api_client):
    variables = {"id": "1234", "lines": []}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]
    assert data["errors"][0]["field"] == "id"


def test_checkout_lines_update_check_lines_quantity(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant = line.variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 11}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert data["errors"][0]["message"] == (
        "Could not add items 123. Only 10 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


def test_checkout_lines_update_with_chosen_shipping(
    user_api_client, checkout, stock, address, shipping_method
):
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()

    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 1


def test_checkout_lines_update_remove_shipping_if_removed_product_with_shipping(
    user_api_client, checkout_with_item, digital_content, address, shipping_method
):
    checkout = checkout_with_item
    digital_variant = digital_content.product_variant
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, digital_variant, 1)
    line = checkout.lines.first()
    variant = line.variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 0}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    assert not checkout.shipping_method


def test_with_active_problems_flow(
    api_client, checkout_with_problems, product_with_single_variant
):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    variant = product_with_single_variant.variants.first()

    checkout_info = fetch_checkout_info(
        checkout_with_problems, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "lines": [{"variantId": to_global_id_or_none(variant), "quantity": 3}],
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutLinesUpdate"]["errors"]


def test_checkout_lines_update_quantity_gift(user_api_client, checkout_with_item):
    # given
    checkout = checkout_with_item
    line = checkout.lines.first()
    line.is_gift = True
    line.save(update_fields=["is_gift"])
    line_id = to_global_id_or_none(line)
    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"lineId": line_id, "quantity": 0}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]
    assert not data["checkout"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lineId"
    assert errors[0]["code"] == CheckoutErrorCode.NON_EDITABLE_GIFT_LINE.name
    assert errors[0]["lines"] == [line_id]
