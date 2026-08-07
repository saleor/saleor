from unittest.mock import patch

import graphene

from .....checkout.error_codes import CheckoutErrorCode
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

LIMIT_PATCH = "saleor.graphql.checkout.mutations.utils.CHECKOUT_LINES_INPUT_LIMIT"

MUTATION_CHECKOUT_LINES_ADD = """
mutation checkoutLinesAdd($id: ID, $lines: [CheckoutLineInput!]!) {
  checkoutLinesAdd(id: $id, lines: $lines) {
    errors {
      field
      code
      message
    }
  }
}
"""

MUTATION_CHECKOUT_LINES_UPDATE = """
mutation checkoutLinesUpdate($id: ID, $lines: [CheckoutLineUpdateInput!]!) {
  checkoutLinesUpdate(id: $id, lines: $lines) {
    errors {
      field
      code
      message
    }
  }
}
"""

MUTATION_CHECKOUT_LINES_DELETE = """
mutation checkoutLinesDelete($id: ID, $linesIds: [ID!]!) {
  checkoutLinesDelete(id: $id, linesIds: $linesIds) {
    errors {
      field
      code
      message
    }
  }
}
"""

MUTATION_CHECKOUT_CREATE = """
mutation checkoutCreate($input: CheckoutCreateInput!) {
  checkoutCreate(input: $input) {
    errors {
      field
      code
      message
    }
  }
}
"""


@patch(LIMIT_PATCH, 1)
def test_checkout_lines_add_rejects_oversized_lines_input(
    user_api_client, checkout_with_item, stock
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [
            {"variantId": variant_id, "quantity": 1},
            {"variantId": variant_id, "quantity": 1},
        ],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesAdd"]["errors"][0]
    assert error["field"] == "lines"
    assert error["code"] == CheckoutErrorCode.INVALID.name
    assert "1" in error["message"]


@patch(LIMIT_PATCH, 1)
def test_checkout_lines_update_rejects_oversized_lines_input(
    user_api_client, checkout_with_item
):
    # given
    line = checkout_with_item.lines.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant_id)
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "lines": [
            {"variantId": variant_id, "quantity": 1},
            {"variantId": variant_id, "quantity": 2},
        ],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesUpdate"]["errors"][0]
    assert error["field"] == "lines"
    assert error["code"] == CheckoutErrorCode.INVALID.name


@patch(LIMIT_PATCH, 1)
def test_checkout_lines_delete_rejects_oversized_lines_input(
    user_api_client, checkout_with_item
):
    # given
    line = checkout_with_item.lines.first()
    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "linesIds": [line_id, line_id],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesDelete"]["errors"][0]
    assert error["field"] == "linesIds"
    assert error["code"] == CheckoutErrorCode.INVALID.name


@patch(LIMIT_PATCH, 1)
def test_checkout_create_rejects_oversized_lines_input(
    user_api_client, stock, channel_USD
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "input": {
            "channel": channel_USD.slug,
            "lines": [
                {"variantId": variant_id, "quantity": 1},
                {"variantId": variant_id, "quantity": 1},
            ],
        }
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["checkoutCreate"]["errors"][0]
    assert error["field"] == "lines"
    assert error["code"] == CheckoutErrorCode.INVALID.name
