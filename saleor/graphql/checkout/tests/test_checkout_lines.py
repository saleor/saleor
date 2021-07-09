import datetime
import uuid
from unittest import mock

import graphene

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import calculate_checkout_quantity
from ....plugins.manager import get_plugins_manager
from ....product.models import ProductChannelListing
from ...tests.utils import get_graphql_content
from ..mutations import update_checkout_shipping_method_if_invalid

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
    "saleor.graphql.checkout.mutations.update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_lines_add(
    mocked_update_shipping_method, user_api_client, checkout_with_item, stock
):
    variant = stock.product_variant
    checkout = checkout_with_item
    line = checkout.lines.first()
    lines = fetch_checkout_lines(checkout)
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
    lines = fetch_checkout_lines(checkout)
    line = checkout.lines.latest("pk")
    assert line.variant == variant
    assert line.quantity == 1
    assert calculate_checkout_quantity(lines) == 4

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)


def test_checkout_lines_add_existing_variant(user_api_client, checkout_with_item):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)

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
    line = checkout.lines.latest("pk")
    assert line.quantity == 10


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
    product.channel_listings.update(available_for_purchase=None)

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
        available_for_purchase=datetime.date.today() + datetime.timedelta(days=1)
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
            "message": "Cannot add more than 50 times this item.",
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
            $token: UUID, $lines: [CheckoutLineInput!]!) {
        checkoutLinesUpdate(token: $token, lines: $lines) {
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
    }
    """


@mock.patch(
    "saleor.graphql.checkout.mutations.update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_lines_update(
    mocked_update_shipping_method, user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    lines = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    assert calculate_checkout_quantity(lines) == 3
    line = checkout.lines.first()
    variant = line.variant
    assert line.quantity == 3

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
    lines = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1
    assert calculate_checkout_quantity(lines) == 1

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)


def test_checkout_lines_update_with_unavailable_variant(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
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


@mock.patch(
    "saleor.graphql.checkout.mutations.update_checkout_shipping_method_if_invalid",
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
    lines = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)


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
    lines = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 1


MUTATION_CHECKOUT_LINES_DELETE = """
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
    "saleor.graphql.checkout.mutations.update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_line_delete(
    mocked_update_shipping_method, user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    lines = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 3
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.quantity == 3

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)

    variables = {"token": checkout.token, "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 0
    assert calculate_checkout_quantity(lines) == 0
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
