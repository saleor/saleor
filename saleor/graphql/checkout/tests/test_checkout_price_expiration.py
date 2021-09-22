from unittest.mock import patch

import graphene

from saleor.graphql.tests.utils import get_graphql_content


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_lines_add_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    stock,
):
    query = """
mutation addCheckoutLine($checkoutId: ID!, $line: CheckoutLineInput!){
  checkoutLinesAdd(checkoutId: $checkoutId, lines: [$line]) {
    errors {
      field
      message
    }
  }
}
"""
    variables = {
        "checkoutId": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
        "line": {
            "quantity": 1,
            "variantId": graphene.Node.to_global_id(
                "ProductVariant", stock.product_variant.pk
            ),
        },
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutLinesAdd"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items)


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_lines_update_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    stock,
):
    query = """
mutation updateCheckoutLine($token: UUID, $line: CheckoutLineInput!){
  checkoutLinesUpdate(token: $token, lines: [$line]) {
    errors {
      field
      message
    }
  }
}
"""
    variables = {
        "token": checkout_with_items.token,
        "line": {
            "quantity": 1,
            "variantId": graphene.Node.to_global_id(
                "ProductVariant", stock.product_variant.pk
            ),
        },
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutLinesUpdate"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items)


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_lines_delete_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
):
    query = """
mutation updateCheckoutLine($token: UUID, $lineId: ID){
  checkoutLineDelete(token: $token, lineId: $lineId) {
    errors {
      field
      message
    }
  }
}
"""
    variables = {
        "token": checkout_with_items.token,
        "lineId": graphene.Node.to_global_id(
            "CheckoutLine", checkout_with_items.lines.first().pk
        ),
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutLineDelete"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items)


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_shipping_address_update_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    graphql_address_data,
):
    query = """
mutation UpdateCheckoutShippingAddress($token: UUID, $address: AddressInput!) {
  checkoutShippingAddressUpdate(token: $token, shippingAddress: $address) {
    errors {
      field
      message
    }
  }
}
"""
    variables = {
        "token": checkout_with_items.token,
        "address": graphql_address_data,
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutShippingAddressUpdate"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items)


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_billing_address_update_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    graphql_address_data,
):
    query = """
mutation UpdateCheckoutBillingAddress($token: UUID, $address: AddressInput!) {
  checkoutBillingAddressUpdate(token: $token, billingAddress: $address) {
    errors {
      field
      message
    }
  }
}
"""
    variables = {
        "token": checkout_with_items.token,
        "address": graphql_address_data,
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutBillingAddressUpdate"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items)
