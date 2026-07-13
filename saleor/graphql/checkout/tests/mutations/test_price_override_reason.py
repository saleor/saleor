"""Tests for the `priceOverrideReason` field on checkout / order lines.

Feature spec: .context/price-override-reason-scenarios.md

An app with HANDLE_CHECKOUTS may record *why* it set a custom price on a checkout
line. The reason is stored natively, carried onto the order line at completion, and
readable by staff/app (dashboard + subscription webhooks). Strict contract,
per-operation semantics.
"""

from decimal import Decimal

import graphene

from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.models import Checkout
from .....order import OrderOrigin, OrderStatus
from .....order.models import Order
from ....core.utils import to_global_id_or_none
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
)

CHECKOUT_LINES_ADD = """
    mutation checkoutLinesAdd($id: ID, $lines: [CheckoutLineInput!]!) {
        checkoutLinesAdd(id: $id, lines: $lines) {
            checkout { id }
            errors { field code message }
        }
    }
"""

CHECKOUT_CREATE = """
    mutation checkoutCreate($input: CheckoutCreateInput!) {
        checkoutCreate(input: $input) {
            checkout { id token }
            errors { field code message }
        }
    }
"""

CHECKOUT_LINES_UPDATE = """
    mutation checkoutLinesUpdate($id: ID, $lines: [CheckoutLineUpdateInput!]!) {
        checkoutLinesUpdate(id: $id, lines: $lines) {
            checkout { id }
            errors { field code message }
        }
    }
"""

CHECKOUT_LINE_REASON_QUERY = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            lines {
                priceOverrideReason
            }
        }
    }
"""

ORDER_LINE_REASON_QUERY = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    lines {
                        priceOverrideReason
                    }
                }
            }
        }
    }
"""

MUTATION_CHECKOUT_COMPLETE = """
    mutation checkoutComplete($id: ID, $redirectUrl: String) {
        checkoutComplete(id: $id, redirectUrl: $redirectUrl) {
            order { id }
            errors { field message code }
        }
    }
"""


# --- 1. Writing the reason (checkout, app-only) ---------------------------------


def test_lines_add_sets_price_override_reason(
    app_api_client, checkout, stock, permission_handle_checkouts
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    price = Decimal("13.11")
    reason = "Loyalty pricing rule #42"

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [
            {
                "variantId": variant_id,
                "quantity": 1,
                "price": price,
                "priceOverrideReason": reason,
            }
        ],
        "channelSlug": checkout.channel.slug,
    }

    # when
    response = app_api_client.post_graphql(
        CHECKOUT_LINES_ADD, variables, permissions=[permission_handle_checkouts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert data["errors"] == []
    checkout.refresh_from_db()
    line = checkout.lines.last()
    assert line.price_override == price
    assert line.price_override_reason == reason


def test_lines_add_price_without_reason_stores_null(
    app_api_client, checkout, stock, permission_handle_checkouts
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    price = Decimal("13.11")

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 1, "price": price}],
        "channelSlug": checkout.channel.slug,
    }

    # when
    response = app_api_client.post_graphql(
        CHECKOUT_LINES_ADD, variables, permissions=[permission_handle_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkoutLinesAdd"]["errors"] == []
    checkout.refresh_from_db()
    line = checkout.lines.last()
    assert line.price_override == price
    assert line.price_override_reason is None


def test_lines_add_reason_without_override_raises_error(
    app_api_client, checkout, stock, permission_handle_checkouts
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    reason = "Reason without a price"

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [
            {"variantId": variant_id, "quantity": 1, "priceOverrideReason": reason}
        ],
        "channelSlug": checkout.channel.slug,
    }

    # when
    response = app_api_client.post_graphql(
        CHECKOUT_LINES_ADD, variables, permissions=[permission_handle_checkouts]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesAdd"]["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == CheckoutErrorCode.PRICE_OVERRIDE_REASON_WITHOUT_OVERRIDE.name
    )


def test_lines_add_reason_by_app_no_perm(app_api_client, checkout, stock):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [
            {
                "variantId": variant_id,
                "quantity": 1,
                "price": Decimal("13.11"),
                "priceOverrideReason": "not allowed without perm",
            }
        ],
        "channelSlug": checkout.channel.slug,
    }

    # when
    response = app_api_client.post_graphql(CHECKOUT_LINES_ADD, variables)

    # then
    assert_no_permission(response)


def test_create_sets_price_override_reason(
    app_api_client,
    stock,
    graphql_address_data,
    channel_USD,
    permission_handle_checkouts,
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    price = Decimal("12.25")
    reason = "Contract price"

    variables = {
        "input": {
            "channel": channel_USD.slug,
            "lines": [
                {
                    "quantity": 1,
                    "variantId": variant_id,
                    "price": price,
                    "priceOverrideReason": reason,
                }
            ],
            "email": "test@example.com",
            "shippingAddress": graphql_address_data,
        }
    }

    # when
    response = app_api_client.post_graphql(
        CHECKOUT_CREATE, variables, permissions=[permission_handle_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkoutCreate"]["errors"] == []
    checkout_line = Checkout.objects.first().lines.first()
    assert checkout_line.price_override == price
    assert checkout_line.price_override_reason == reason


# --- 2. Normalization -----------------------------------------------------------


def test_lines_add_empty_reason_stored_as_null(
    app_api_client, checkout, stock, permission_handle_checkouts
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    price = Decimal("13.11")

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [
            {
                "variantId": variant_id,
                "quantity": 1,
                "price": price,
                "priceOverrideReason": "   ",
            }
        ],
        "channelSlug": checkout.channel.slug,
    }

    # when
    response = app_api_client.post_graphql(
        CHECKOUT_LINES_ADD, variables, permissions=[permission_handle_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkoutLinesAdd"]["errors"] == []
    checkout.refresh_from_db()
    line = checkout.lines.last()
    assert line.price_override == price
    assert line.price_override_reason is None


# --- 3. Update semantics on checkoutLinesUpdate (per-operation) ------------------


def test_lines_update_new_price_and_reason(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    # given
    checkout = checkout_with_item
    line = checkout.lines.first()
    line.price_override = Decimal("10.00")
    line.price_override_reason = "old"
    line.save(update_fields=["price_override", "price_override_reason"])
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)
    new_price = Decimal("12.00")
    new_reason = "new"

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [
            {
                "variantId": variant_id,
                "quantity": 1,
                "price": new_price,
                "priceOverrideReason": new_reason,
            }
        ],
    }

    # when
    response = app_api_client.post_graphql(
        CHECKOUT_LINES_UPDATE, variables, permissions=[permission_handle_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkoutLinesUpdate"]["errors"] == []
    line.refresh_from_db()
    assert line.price_override == new_price
    assert line.price_override_reason == new_reason


def test_lines_update_new_price_without_reason_nulls_reason(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    # given
    checkout = checkout_with_item
    line = checkout.lines.first()
    line.price_override = Decimal("10.00")
    line.price_override_reason = "old"
    line.save(update_fields=["price_override", "price_override_reason"])
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)
    new_price = Decimal("12.00")

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 1, "price": new_price}],
    }

    # when
    response = app_api_client.post_graphql(
        CHECKOUT_LINES_UPDATE, variables, permissions=[permission_handle_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkoutLinesUpdate"]["errors"] == []
    line.refresh_from_db()
    assert line.price_override == new_price
    assert line.price_override_reason is None


def test_lines_update_clear_price_clears_reason(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    # given
    checkout = checkout_with_item
    line = checkout.lines.first()
    line.price_override = Decimal("10.00")
    line.price_override_reason = "old"
    line.save(update_fields=["price_override", "price_override_reason"])
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "quantity": 1, "price": None}],
    }

    # when
    response = app_api_client.post_graphql(
        CHECKOUT_LINES_UPDATE, variables, permissions=[permission_handle_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkoutLinesUpdate"]["errors"] == []
    line.refresh_from_db()
    assert line.price_override is None
    assert line.price_override_reason is None


def test_lines_update_reason_only_when_override_exists(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    # given
    checkout = checkout_with_item
    line = checkout.lines.first()
    price = Decimal("10.00")
    line.price_override = price
    line.price_override_reason = "old"
    line.save(update_fields=["price_override", "price_override_reason"])
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)
    corrected = "corrected"

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "priceOverrideReason": corrected}],
    }

    # when
    response = app_api_client.post_graphql(
        CHECKOUT_LINES_UPDATE, variables, permissions=[permission_handle_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkoutLinesUpdate"]["errors"] == []
    line.refresh_from_db()
    assert line.price_override == price
    assert line.price_override_reason == corrected


def test_lines_update_reason_only_without_override_raises(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    # given
    checkout = checkout_with_item
    line = checkout.lines.first()
    assert line.price_override is None
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [{"variantId": variant_id, "priceOverrideReason": "orphan"}],
    }

    # when
    response = app_api_client.post_graphql(
        CHECKOUT_LINES_UPDATE, variables, permissions=[permission_handle_checkouts]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesUpdate"]["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == CheckoutErrorCode.PRICE_OVERRIDE_REASON_WITHOUT_OVERRIDE.name
    )


# --- 4. Checkout -> Order conversion --------------------------------------------


def test_complete_copies_price_override_reason_to_order_line(
    user_api_client,
    checkout_with_item,
    address,
    checkout_delivery,
    shipping_method,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    line = checkout.lines.first()
    reason = "rule #42"
    line.price_override = Decimal(2)
    line.price_override_reason = reason
    line.save(update_fields=["price_override", "price_override_reason"])

    channel = checkout.channel
    channel.allow_unpaid_orders = True
    channel.save(update_fields=["allow_unpaid_orders"])

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkoutComplete"]["errors"] == []
    order = Order.objects.get()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.origin == OrderOrigin.CHECKOUT
    order_line = order.lines.get()
    assert order_line.is_price_overridden
    assert order_line.price_override_reason == reason


def test_complete_without_override_leaves_reason_null(
    user_api_client,
    checkout_with_item,
    address,
    checkout_delivery,
    shipping_method,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    channel = checkout.channel
    channel.allow_unpaid_orders = True
    channel.save(update_fields=["allow_unpaid_orders"])

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkoutComplete"]["errors"] == []
    order_line = Order.objects.get().lines.get()
    assert not order_line.is_price_overridden
    assert order_line.price_override_reason is None


# --- 5. Reading the reason ------------------------------------------------------


def test_query_checkout_line_reason_by_staff(
    staff_api_client, checkout_with_item, permission_manage_checkouts
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    line = checkout_with_item.lines.first()
    reason = "rule #42"
    line.price_override = Decimal("10.00")
    line.price_override_reason = reason
    line.save(update_fields=["price_override", "price_override_reason"])
    variables = {"id": to_global_id_or_none(checkout_with_item)}

    # when
    response = staff_api_client.post_graphql(CHECKOUT_LINE_REASON_QUERY, variables)

    # then
    content = get_graphql_content(response)
    lines = content["data"]["checkout"]["lines"]
    assert lines[0]["priceOverrideReason"] == reason


def test_query_checkout_line_reason_by_app(
    app_api_client, checkout_with_item, permission_handle_checkouts
):
    # given
    app_api_client.app.permissions.add(permission_handle_checkouts)
    line = checkout_with_item.lines.first()
    reason = "rule #42"
    line.price_override = Decimal("10.00")
    line.price_override_reason = reason
    line.save(update_fields=["price_override", "price_override_reason"])
    variables = {"id": to_global_id_or_none(checkout_with_item)}

    # when
    response = app_api_client.post_graphql(CHECKOUT_LINE_REASON_QUERY, variables)

    # then
    content = get_graphql_content(response)
    lines = content["data"]["checkout"]["lines"]
    assert lines[0]["priceOverrideReason"] == reason


def test_query_checkout_line_reason_no_permission(user_api_client, checkout_with_item):
    # given
    line = checkout_with_item.lines.first()
    line.price_override = Decimal("10.00")
    line.price_override_reason = "rule #42"
    line.save(update_fields=["price_override", "price_override_reason"])
    variables = {"id": to_global_id_or_none(checkout_with_item)}

    # when
    response = user_api_client.post_graphql(CHECKOUT_LINE_REASON_QUERY, variables)

    # then
    assert_no_permission(response)


def test_query_order_line_reason_by_app(
    app_api_client, order_line, permission_manage_orders
):
    # given
    app_api_client.app.permissions.add(permission_manage_orders)
    reason = "rule #42"
    order_line.is_price_overridden = True
    order_line.price_override_reason = reason
    order_line.save(update_fields=["is_price_overridden", "price_override_reason"])

    # when
    response = app_api_client.post_graphql(ORDER_LINE_REASON_QUERY)

    # then
    content = get_graphql_content(response)
    node = content["data"]["orders"]["edges"][0]["node"]
    assert node["lines"][0]["priceOverrideReason"] == reason
