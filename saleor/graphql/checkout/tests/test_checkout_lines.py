import datetime
import uuid
from decimal import Decimal
from unittest import mock

import graphene
import pytest
import pytz
from django.utils import timezone

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.models import Checkout, CheckoutLine
from ....checkout.utils import add_variant_to_checkout, calculate_checkout_quantity
from ....plugins.manager import get_plugins_manager
from ....product.models import ProductChannelListing
from ....warehouse import WarehouseClickAndCollectOption
from ....warehouse.models import Reservation, Stock
from ....warehouse.tests.utils import get_available_quantity_for_stock
from ...tests.utils import assert_no_permission, get_graphql_content
from ..mutations.utils import (
    CheckoutLineData,
    group_quantity_and_custom_prices_by_variants,
    update_checkout_shipping_method_if_invalid,
)

MUTATION_CHECKOUT_LINES_ADD = """
    mutation checkoutLinesAdd(
            $token: UUID, $lines: [CheckoutLineInput!]!) {
        checkoutLinesAdd(token: $token, lines: $lines) {
            checkout {
                token
                quantity
                lines {
                    quantity
                    variant {
                        id
                    }
                }
            }
            errors {
                field
                code
                message
                variants
            }
        }
    }"""


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_lines_add(
    mocked_update_shipping_method, user_api_client, checkout_with_item, stock
):
    variant = stock.product_variant
    checkout = checkout_with_item
    line = checkout.lines.first()
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 3
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    previous_last_change = checkout.last_change

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    line = checkout.lines.last()
    assert line.variant == variant
    assert line.quantity == 1
    assert calculate_checkout_quantity(lines) == 4
    assert not Reservation.objects.exists()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change


def test_checkout_lines_add_with_reservations(
    site_settings_with_reservations, user_api_client, checkout_with_item, stock
):
    variant = stock.product_variant
    checkout = checkout_with_item
    line = checkout.lines.first()
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 3
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    line = checkout.lines.last()
    assert line.variant == variant
    assert line.quantity == 1
    assert calculate_checkout_quantity(lines) == 4

    reservation = line.reservations.get()
    assert reservation
    assert reservation.checkout_line == line
    assert reservation.quantity_reserved == line.quantity


def test_checkout_lines_add_updates_reservation(
    site_settings_with_reservations,
    user_api_client,
    checkout_line_with_one_reservation,
    stock,
):
    variant = checkout_line_with_one_reservation.variant
    checkout = checkout_line_with_one_reservation.checkout
    line = checkout_line_with_one_reservation
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 2
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    line = checkout.lines.last()
    assert line.variant == variant
    assert line.quantity == 3
    assert calculate_checkout_quantity(lines) == 3

    reservation = line.reservations.get()
    assert reservation
    assert reservation.checkout_line == line
    assert reservation.quantity_reserved == line.quantity


def test_checkout_lines_add_new_variant_updates_other_lines_reservations_expirations(
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
    variant_other_id = graphene.Node.to_global_id("ProductVariant", variant_other.pk)

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_other_id, "quantity": 3}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
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

    updated_reservation = Reservation.objects.get(checkout_line__variant=variant)
    assert updated_reservation.checkout_line == line
    assert updated_reservation.quantity_reserved == line.quantity
    assert updated_reservation.reserved_until > reservation.reserved_until

    other_reservation = Reservation.objects.get(checkout_line__variant=variant_other)
    assert other_reservation.checkout_line == new_line
    assert other_reservation.quantity_reserved == new_line.quantity
    assert other_reservation.reserved_until > reservation.reserved_until

    assert updated_reservation.reserved_until == other_reservation.reserved_until

    with pytest.raises(Reservation.DoesNotExist):
        reservation.refresh_from_db()


def test_checkout_lines_add_existing_variant(user_api_client, checkout_with_item):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)
    previous_last_change = checkout.last_change

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 7}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["errors"]
    checkout.refresh_from_db()
    line = checkout.lines.last()
    assert line.quantity == 10
    assert checkout.last_change != previous_last_change


def test_checkout_lines_add_custom_price(
    app_api_client, checkout, stock, permission_handle_checkouts
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    price = Decimal("13.11")

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1, "price": price}],
        "channelSlug": checkout.channel.slug,
    }
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_ADD,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["errors"]
    checkout.refresh_from_db()
    line = checkout.lines.last()
    assert line.variant == variant
    assert line.quantity == 1
    assert line.price_override == price


def test_checkout_lines_add_existing_variant_with_custom_price(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)
    price = Decimal("13.11")

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 7, "price": price}],
        "channelSlug": checkout.channel.slug,
    }
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_ADD,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["errors"]
    checkout.refresh_from_db()
    line = checkout.lines.last()
    assert line.quantity == 10
    assert line.price_override == price


def test_checkout_lines_add_existing_variant_override_previous_custom_price(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    line.price_override = 8.22
    line.save(update_fields=["price_override"])

    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)
    price = Decimal("13.11")

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 7, "price": price}],
        "channelSlug": checkout.channel.slug,
    }
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_ADD,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["errors"]
    checkout.refresh_from_db()
    line = checkout.lines.last()
    assert line.quantity == 10
    assert line.price_override == price


def test_checkout_lines_add_custom_price_app_no_perm(app_api_client, checkout, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    price = Decimal("13.11")

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1, "price": price}],
        "channelSlug": checkout.channel.slug,
    }
    response = app_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    assert_no_permission(response)


def test_checkout_lines_add_custom_price_permission_denied_for_staff_user(
    staff_api_client, checkout, stock, permission_handle_checkouts
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    price = Decimal("13.11")

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1, "price": price}],
        "channelSlug": checkout.channel.slug,
    }
    response = staff_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_ADD,
        variables,
        permissions=[permission_handle_checkouts],
    )
    assert_no_permission(response)


def test_checkout_lines_add_existing_variant_over_allowed_stock(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)
    current_stock = line.variant.stocks.first()

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": current_stock.quantity - 1}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesAdd"]["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name


def test_checkout_lines_add_with_unavailable_variant(
    user_api_client, checkout_with_item, stock
):
    variant = stock.product_variant
    variant.channel_listings.filter(channel=checkout_with_item.channel).update(
        price_amount=None
    )
    checkout = checkout_with_item
    line = checkout.lines.first()
    assert line.quantity == 3
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesAdd"]["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [variant_id]


def test_checkout_lines_add_with_insufficient_stock(
    user_api_client, checkout_with_item, stock
):
    variant = stock.product_variant
    checkout = checkout_with_item
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 49}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesAdd"]["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


def test_checkout_lines_add_with_reserved_insufficient_stock(
    site_settings_with_reservations,
    user_api_client,
    checkout_with_item,
    stock,
    channel_USD,
):
    variant = stock.product_variant
    checkout = checkout_with_item
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    quantity_available = get_available_quantity_for_stock(stock)

    other_checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    other_checkout_line = other_checkout.lines.create(
        variant=variant,
        quantity=quantity_available - 1,
    )
    Reservation.objects.create(
        checkout_line=other_checkout_line,
        stock=stock,
        quantity_reserved=quantity_available - 1,
        reserved_until=timezone.now() + datetime.timedelta(minutes=5),
    )

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 2}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesAdd"]["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


@pytest.mark.parametrize(
    "cc_option",
    [
        WarehouseClickAndCollectOption.ALL_WAREHOUSES,
        WarehouseClickAndCollectOption.LOCAL_STOCK,
    ],
)
def test_checkout_lines_for_click_and_collect_insufficient_stock(
    user_api_client, checkout_with_item_for_cc, warehouse_for_cc, cc_option
):
    checkout = checkout_with_item_for_cc
    checkout.collection_point = warehouse_for_cc

    warehouse_for_cc.click_and_collect_option = cc_option
    warehouse_for_cc.save(update_fields=["click_and_collect_option"])
    checkout.refresh_from_db()

    variant = checkout.lines.last().variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 42}],
        "channelSlug": checkout.channel.slug,
    }

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesAdd"]["errors"]

    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


def test_checkout_lines_add_with_zero_quantity(
    user_api_client, checkout_with_item, stock
):
    variant = stock.product_variant
    checkout = checkout_with_item
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 0}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesAdd"]["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.ZERO_QUANTITY.name
    assert errors[0]["field"] == "quantity"


def test_checkout_lines_add_no_channel_shipping_zones(
    user_api_client, checkout_with_item, stock
):
    variant = stock.product_variant
    checkout = checkout_with_item
    checkout.channel.shipping_zones.clear()
    line = checkout.lines.first()
    assert line.quantity == 3
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesAdd"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


def test_checkout_lines_add_with_unpublished_product(
    user_api_client, checkout_with_item, stock, channel_USD
):
    variant = stock.product_variant
    product = variant.product
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout_with_item.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
        "channelSlug": checkout_with_item.channel.slug,
    }

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)

    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesAdd"]["errors"][0]
    assert error["code"] == CheckoutErrorCode.PRODUCT_NOT_PUBLISHED.name


def test_checkout_lines_add_with_unavailable_for_purchase_product(
    user_api_client, checkout_with_item, stock
):
    # given
    variant = stock.product_variant
    product = stock.product_variant.product
    product.channel_listings.update(available_for_purchase_at=None)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout_with_item.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesAdd"]["errors"][0]
    assert error["field"] == "lines"
    assert error["code"] == CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name
    assert error["variants"] == [variant_id]


def test_checkout_lines_add_with_available_for_purchase_from_tomorrow_product(
    user_api_client, checkout_with_item, stock
):
    # given
    variant = stock.product_variant
    product = stock.product_variant.product
    product.channel_listings.update(
        available_for_purchase_at=datetime.datetime.now(pytz.UTC)
        + datetime.timedelta(days=1)
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout_with_item.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesAdd"]["errors"][0]
    assert error["field"] == "lines"
    assert error["code"] == CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name
    assert error["variants"] == [variant_id]


def test_checkout_lines_add_too_many(user_api_client, checkout_with_item, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout_with_item.token,
        "lines": [{"variantId": variant_id, "quantity": 51}],
        "channelSlug": checkout_with_item.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)["data"]["checkoutLinesAdd"]

    assert content["errors"]
    assert content["errors"] == [
        {
            "field": "quantity",
            "message": "Cannot add more than 50 times this item: SKU_A.",
            "code": "QUANTITY_GREATER_THAN_LIMIT",
            "variants": None,
        }
    ]


@pytest.mark.parametrize("is_preorder", [True, False])
def test_checkout_lines_add_too_many_after_two_trials(
    user_api_client, checkout_with_item, stock, is_preorder
):
    variant = stock.product_variant
    variant.is_preorder = is_preorder
    variant.preorder_end_date = timezone.now() + datetime.timedelta(days=1)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stock.quantity = 200
    stock.save(update_fields=["quantity"])
    variant.save(update_fields=["is_preorder", "preorder_end_date"])

    variables = {
        "token": checkout_with_item.token,
        "lines": [{"variantId": variant_id, "quantity": 26}],
        "channelSlug": checkout_with_item.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)["data"]["checkoutLinesAdd"]

    assert not content["errors"]

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)["data"]["checkoutLinesAdd"]

    assert content["errors"] == [
        {
            "field": "quantity",
            "message": "Cannot add more than 50 times this item: SKU_A.",
            "code": "QUANTITY_GREATER_THAN_LIMIT",
            "variants": None,
        }
    ]


def test_checkout_lines_add_empty_checkout(user_api_client, checkout, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["errors"]
    checkout.refresh_from_db()
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1


def test_checkout_lines_add_variant_without_inventory_tracking(
    user_api_client, checkout, variant_without_inventory_tracking
):
    variant = variant_without_inventory_tracking
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["errors"]
    checkout.refresh_from_db()
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1


def test_checkout_lines_add_check_lines_quantity(user_api_client, checkout, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 16}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert data["errors"][0]["message"] == (
        "Could not add items SKU_A. Only 15 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


def test_checkout_lines_invalid_variant_id(user_api_client, checkout, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    invalid_variant_id = "InvalidId"

    variables = {
        "token": checkout.token,
        "lines": [
            {"variantId": variant_id, "quantity": 1},
            {"variantId": invalid_variant_id, "quantity": 3},
        ],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    error_msg = "Could not resolve to a node with the global id list of '%s'."
    assert data["errors"][0]["message"] == error_msg % [invalid_variant_id]
    assert data["errors"][0]["field"] == "variantId"


MUTATION_CHECKOUT_LINES_UPDATE = """
    mutation checkoutLinesUpdate(
            $token: UUID, $lines: [CheckoutLineUpdateInput!]!) {
        checkoutLinesUpdate(token: $token, lines: $lines) {
            checkout {
                id
                token
                quantity
                lines {
                    quantity
                    variant {
                        id
                    }
                }
            }
            errors {
                field
                code
                message
                variants
            }
        }
    }
    """


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_lines_update(
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

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout_with_item.token,
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

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change


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
        "token": checkout.token,
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
        "token": checkout.token,
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
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
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
        "token": checkout.token,
        "lines": [{"variantId": variant_other_id, "quantity": 3}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]
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

    updated_reservation = Reservation.objects.get(checkout_line__variant=variant)
    assert updated_reservation.checkout_line == line
    assert updated_reservation.quantity_reserved == line.quantity
    assert updated_reservation.reserved_until > reservation.reserved_until

    other_reservation = Reservation.objects.get(checkout_line__variant=variant_other)
    assert other_reservation.checkout_line == new_line
    assert other_reservation.quantity_reserved == new_line.quantity

    assert updated_reservation.reserved_until == other_reservation.reserved_until

    with pytest.raises(Reservation.DoesNotExist):
        reservation.refresh_from_db()


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
        "token": checkout_with_item.token,
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
        "token": checkout_with_item.token,
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
        "token": checkout_with_item.token,
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
        "token": checkout_with_item.token,
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
    """Ensure an error is not raised and the line is deleted when the line quantity
    is set to 0 firstly and then the custom price is changed."""

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
        "token": checkout_with_item.token,
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
        "token": checkout_with_item.token,
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
        "token": checkout_with_item.token,
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
        "token": checkout_with_item.token,
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
        "token": checkout.token,
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
        "token": checkout.token,
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
        "token": checkout.token,
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
        "token": checkout.token,
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
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 0}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 0
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
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
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 0}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 0
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
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
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 0}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 0
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
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
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)

    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesUpdate"]["errors"][0]
    assert error["code"] == CheckoutErrorCode.PRODUCT_NOT_PUBLISHED.name


def test_checkout_lines_update_invalid_checkout_id(user_api_client):
    variables = {"token": uuid.uuid4(), "lines": []}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]
    assert data["errors"][0]["field"] == "token"


def test_checkout_lines_update_check_lines_quantity(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant = line.variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": checkout.token,
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
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 1


MUTATION_CHECKOUT_LINE_DELETE = """
    mutation checkoutLineDelete($token: UUID, $lineId: ID!) {
        checkoutLineDelete(token: $token, lineId: $lineId) {
            checkout {
                token
                lines {
                    quantity
                    variant {
                        id
                    }
                }
            }
            errors {
                field
                message
            }
        }
    }
"""


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_line_delete."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_line_delete(
    mocked_update_shipping_method,
    user_api_client,
    checkout_line_with_reservation_in_many_stocks,
):
    assert Reservation.objects.count() == 2
    checkout = checkout_line_with_reservation_in_many_stocks.checkout
    previous_last_change = checkout.last_change
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 3
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.quantity == 3

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)

    variables = {"token": checkout.token, "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINE_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 0
    assert calculate_checkout_quantity(lines) == 0
    assert Reservation.objects.count() == 0
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change


MUTATION_CHECKOUT_LINES_DELETE = """
    mutation checkoutLinesDelete($token: UUID!, $linesIds: [ID!]!) {
        checkoutLinesDelete(token: $token, linesIds: $linesIds) {
            checkout {
                token
                lines {
                    id
                    quantity
                    variant {
                        id
                    }
                }
            }
            errors {
                  message
                  code
                  field
                  lines
            }
        }
    }
"""


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_lines_delete(
    mocked_update_shipping_method, user_api_client, checkout_with_items
):
    checkout = checkout_with_items
    checkout_lines_count = checkout.lines.count()
    previous_last_change = checkout.last_change
    line = checkout.lines.first()
    second_line = checkout.lines.last()

    first_line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    second_line_id = graphene.Node.to_global_id("CheckoutLine", second_line.pk)
    lines_list = [first_line_id, second_line_id]

    variables = {"token": checkout.token, "linesIds": lines_list}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() + len(lines_list) == checkout_lines_count
    remaining_lines = data["checkout"]["lines"]
    lines_ids = [line["id"] for line in remaining_lines]
    assert lines_list not in lines_ids
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change


def test_checkout_lines_delete_invalid_checkout_token(
    user_api_client, checkout_with_items
):
    checkout = checkout_with_items
    previous_last_change = checkout.last_change
    line = checkout.lines.first()
    second_line = checkout.lines.last()

    first_line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    second_line_id = graphene.Node.to_global_id("CheckoutLine", second_line.pk)
    lines_list = [first_line_id, second_line_id]

    variables = {
        "token": "bd159cc8-9dd6-4529-a6f6-8a5dee169806",
        "linesIds": lines_list,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesDelete"]["errors"][0]
    assert errors["code"] == CheckoutErrorCode.NOT_FOUND.name
    checkout.refresh_from_db()
    assert checkout.last_change == previous_last_change


def tests_checkout_lines_delete_invalid_lines_ids(user_api_client, checkout_with_items):
    checkout = checkout_with_items
    previous_last_change = checkout.last_change
    line = checkout.lines.first()

    first_line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    lines_list = [first_line_id, "Q2hlY2tvdXRMaW5lOjE8"]

    variables = {"token": checkout.token, "linesIds": lines_list}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["errors"][0]
    assert errors["extensions"]["exception"]["code"] == "GraphQLError"
    assert checkout.last_change == previous_last_change


@pytest.mark.parametrize(
    "lines, expected",
    [
        (
            [
                {"quantity": 6, "variant_id": "abc", "price": 1.22},
                {"quantity": 6, "variant_id": "abc"},
                {"quantity": 1, "variant_id": "def", "price": 33.2},
                {"quantity": 1, "variant_id": "def", "price": 10},
            ],
            [
                CheckoutLineData(
                    quantity=12,
                    quantity_to_update=True,
                    custom_price=1.22,
                    custom_price_to_update=True,
                ),
                CheckoutLineData(
                    quantity=2,
                    quantity_to_update=True,
                    custom_price=10,
                    custom_price_to_update=True,
                ),
            ],
        ),
        (
            [
                {"quantity": 8, "variant_id": "ghi"},
                {"quantity": 2, "variant_id": "ghi"},
                {"quantity": 6, "variant_id": "abc"},
                {"quantity": 1, "variant_id": "def"},
                {"quantity": 6, "variant_id": "abc"},
                {"quantity": 1, "variant_id": "def"},
                {"quantity": 8, "variant_id": "ghi"},
                {"quantity": 2, "variant_id": "ghi"},
                {"quantity": 922, "variant_id": "xyz"},
                {"quantity": 6, "variant_id": "abc"},
                {"quantity": 1, "variant_id": "def"},
                {"quantity": 6, "variant_id": "abc"},
                {"quantity": 1, "variant_id": "def"},
                {"quantity": 1000, "variant_id": "jkl"},
                {"quantity": 999, "variant_id": "zzz"},
            ],
            [
                CheckoutLineData(
                    quantity=quantity,
                    quantity_to_update=True,
                    custom_price=None,
                    custom_price_to_update=False,
                )
                for quantity in [20, 24, 4, 922, 1000, 999]
            ],
        ),
        (
            [
                {"quantity": 100, "variant_id": name}
                for name in (l1 + l2 for l1 in "abcdef" for l2 in "ghijkl")
            ],
            [
                CheckoutLineData(
                    quantity=100,
                    quantity_to_update=True,
                    custom_price=None,
                    custom_price_to_update=False,
                )
            ]
            * 36,
        ),
    ],
)
def test_group_by_variants(lines, expected):
    assert expected == group_quantity_and_custom_prices_by_variants(lines)
