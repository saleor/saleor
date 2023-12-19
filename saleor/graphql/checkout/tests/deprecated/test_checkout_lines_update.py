from unittest import mock

import graphene

from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.utils import calculate_checkout_quantity
from .....plugins.manager import get_plugins_manager
from ....tests.utils import get_graphql_content
from ...mutations.utils import update_checkout_shipping_method_if_invalid

MUTATION_CHECKOUT_LINES_UPDATE = """
    mutation checkoutLinesUpdate(
            $checkoutId: ID, $token: UUID, $lines: [CheckoutLineUpdateInput!]!) {
        checkoutLinesUpdate(checkoutId: $checkoutId, token: $token, lines: $lines) {
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

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
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


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_lines_update_with_token(
    mocked_update_shipping_method, user_api_client, checkout_with_item
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)


def test_checkout_lines_update_neither_token_and_id_given(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant = line.variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_lines_update_both_token_and_id_given(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant = line.variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
        "token": checkout.token,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
