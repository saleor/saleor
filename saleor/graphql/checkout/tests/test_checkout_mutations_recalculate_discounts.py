"""Tests for discounts recalculations.

Checkout mutations that change prices should trigger discounts recalculation.
This file checking that recalculation is called properly.
Recalculation is tested in
`saleor/checkout/tests/test_checkout_discounts_recalculation.py`.
"""
# TODO: ADD tests for new checkout pricing mutation after rebase.

from unittest.mock import ANY, patch

import graphene

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....plugins.manager import get_plugins_manager
from ...tests.utils import get_graphql_content

CHECKOUT_PRICING_FRAGMENT = """
fragment CheckoutPricing on Checkout {
  lines {
    id
    totalPrice {
      gross {
        amount
      }
    }
  }
  shippingPrice {
    gross {
      amount
    }
  }
  discounts {
    value
    amount {
      amount
    }
  }
  discount {
    amount
  }
  totalPrice {
    gross {
      amount
    }
  }
  subtotalPrice {
    gross {
      amount
    }
  }
}
"""

CHECKOUT_LINE_DELETE_MUTATION = (
    CHECKOUT_PRICING_FRAGMENT
    + """
mutation checkoutLineDelete($token: UUID, $lineId: ID!) {
  checkoutLineDelete(token: $token, lineId: $lineId) {
    checkout {
      token
      ...CheckoutPricing
    }
    errors {
      field
      message
    }
  }
}
"""
)


@patch(
    "saleor.graphql.checkout.mutations.checkout_line_delete."
    "recalculate_checkout_discounts"
)
def test_checkout_line_delete_perform_discounts_recalculation(
    recalculate_checkout_discounts_mock, api_client, checkout_with_fixed_discount
):
    # given
    checkout = checkout_with_fixed_discount
    line = checkout_with_fixed_discount.lines.first()
    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    variables = {"token": str(checkout.token), "lineId": line_id}

    # when
    response = api_client.post_graphql(CHECKOUT_LINE_DELETE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    checkout.refresh_from_db()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]

    checkout = data["checkout"]
    assert len(checkout["discounts"]) > 0
    assert len(checkout["lines"]) > 0
    recalculate_checkout_discounts_mock.assert_called_once_with(
        ANY, checkout_info, lines, ANY
    )


CHECKOUT_LINES_DELETE_MUTATION = (
    CHECKOUT_PRICING_FRAGMENT
    + """
mutation checkoutLinesDelete($token: UUID!, $linesIds: [ID!]!) {
  checkoutLinesDelete(token: $token, linesIds: $linesIds) {
    checkout {
      token
      ...CheckoutPricing
    }
    errors {
      field
      message
      code
    }
  }
}
"""
)


@patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete."
    "recalculate_checkout_discounts"
)
def test_checkout_lines_delete_perform_discounts_recalculation(
    recalculate_checkout_discounts_mock, api_client, checkout_with_fixed_discount
):
    # given
    checkout = checkout_with_fixed_discount
    line = checkout_with_fixed_discount.lines.first()
    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    variables = {"token": str(checkout.token), "linesIds": [line_id]}

    # when
    response = api_client.post_graphql(CHECKOUT_LINES_DELETE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    checkout.refresh_from_db()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    data = content["data"]["checkoutLinesDelete"]
    assert not data["errors"]

    checkout = data["checkout"]
    assert len(checkout["discounts"]) > 0
    assert len(checkout["lines"]) > 0
    recalculate_checkout_discounts_mock.assert_called_once_with(
        ANY, checkout_info, lines, ANY
    )


CHECKOUT_LINES_ADD_MUTATION = (
    CHECKOUT_PRICING_FRAGMENT
    + """
mutation checkoutLinesAdd($token: UUID, $lines: [CheckoutLineInput!]!) {
  checkoutLinesAdd(token: $token, lines: $lines) {
    checkout {
      token
      ...CheckoutPricing
    }
    errors {
      field
      message
      code
    }
  }
}
"""
)


@patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "recalculate_checkout_discounts"
)
def test_checkout_lines_add_perform_discounts_recalculation(
    recalculate_checkout_discounts_mock,
    api_client,
    checkout_with_fixed_discount,
    stock,
):
    # given
    checkout = checkout_with_fixed_discount
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": str(checkout.token),
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }

    # when
    response = api_client.post_graphql(CHECKOUT_LINES_ADD_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    checkout.refresh_from_db()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    data = content["data"]["checkoutLinesAdd"]
    assert not data["errors"]

    checkout = data["checkout"]
    assert len(checkout["discounts"]) > 0
    assert len(checkout["lines"]) > 0
    recalculate_checkout_discounts_mock.assert_called_once_with(
        ANY, checkout_info, lines, ANY
    )


CHECKOUT_LINES_UPDATE_MUTATION = (
    CHECKOUT_PRICING_FRAGMENT
    + """
mutation checkoutLinesUpdate($token: UUID, $lines: [CheckoutLineInput!]!) {
  checkoutLinesUpdate(token: $token, lines: $lines) {
    checkout {
      token
      ...CheckoutPricing
    }
    errors {
      field
      message
      code
    }
  }
}
"""
)


@patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add."
    "recalculate_checkout_discounts"
)
def test_checkout_lines_update_perform_discounts_recalculation(
    recalculate_checkout_discounts_mock,
    api_client,
    checkout_with_fixed_discount,
):
    # given
    checkout = checkout_with_fixed_discount
    line = checkout.lines.first()
    variant = line.variant
    quantity = line.quantity
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "token": str(checkout.token),
        "lines": [{"variantId": variant_id, "quantity": quantity + 1}],
    }

    # when
    response = api_client.post_graphql(CHECKOUT_LINES_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    checkout.refresh_from_db()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]

    checkout = data["checkout"]
    assert len(checkout["discounts"]) > 0
    assert len(checkout["lines"]) > 0
    recalculate_checkout_discounts_mock.assert_called_once_with(
        ANY, checkout_info, lines, ANY
    )


CHECKOUT_SHIPPING_ADDRESS_UPDATE_MUTATION = (
    CHECKOUT_PRICING_FRAGMENT
    + """
mutation checkoutShippingAddressUpdate(
  $token: UUID
  $shippingAddress: AddressInput!
) {
  checkoutShippingAddressUpdate(
    token: $token
    shippingAddress: $shippingAddress
  ) {
    checkout {
      token
      ...CheckoutPricing
    }
    errors {
      field
      message
      code
    }
  }
}
"""
)


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "recalculate_checkout_discounts"
)
def test_checkout_shipping_addres_update_perform_discounts_recalculation(
    recalculate_checkout_discounts_mock,
    api_client,
    checkout_with_fixed_discount,
    graphql_address_data,
):
    # given
    checkout = checkout_with_fixed_discount

    variables = {"token": str(checkout.token), "shippingAddress": graphql_address_data}

    # when
    response = api_client.post_graphql(
        CHECKOUT_SHIPPING_ADDRESS_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)

    # then
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)

    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]

    checkout = data["checkout"]
    assert len(checkout["discounts"]) > 0
    assert len(checkout["lines"]) > 0
    recalculate_checkout_discounts_mock.assert_called_once_with(ANY, ANY, lines, ANY)


CHECKOUT_SHIPPING_METHOD_UPDATE_MUTATION = (
    CHECKOUT_PRICING_FRAGMENT
    + """
mutation checkoutShippingMethodUpdate($token: UUID, $shippingMethodId: ID!) {
  checkoutShippingMethodUpdate(
    token: $token
    shippingMethodId: $shippingMethodId
  ) {
    checkout {
      token
      ...CheckoutPricing
    }
    errors {
      field
      message
      code
    }
  }
}
"""
)


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "recalculate_checkout_discounts"
)
def test_checkout_shipping_method_update_perform_discounts_recalculation(
    recalculate_checkout_discounts_mock,
    api_client,
    checkout_with_fixed_discount,
    shipping_method,
):
    # given
    checkout = checkout_with_fixed_discount
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    variables = {"token": str(checkout.token), "shippingMethodId": method_id}

    # when
    response = api_client.post_graphql(
        CHECKOUT_SHIPPING_METHOD_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)

    # then
    checkout.refresh_from_db()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    data = content["data"]["checkoutShippingMethodUpdate"]
    assert not data["errors"]

    checkout = data["checkout"]
    assert len(checkout["discounts"]) > 0
    assert len(checkout["lines"]) > 0
    recalculate_checkout_discounts_mock.assert_called_once_with(
        ANY, checkout_info, lines, ANY
    )


CHECKOUT_DELIVERY_METHOD_UPDATE_MUTATION = (
    CHECKOUT_PRICING_FRAGMENT
    + """
mutation checkoutDeliveryMethodUpdate($token: UUID, $deliveryMethodId: ID) {
  checkoutDeliveryMethodUpdate(
    token: $token
    deliveryMethodId: $deliveryMethodId
  ) {
    checkout {
      token
      ...CheckoutPricing
    }
    errors {
      field
      message
      code
    }
  }
}
"""
)


@patch(
    "saleor.graphql.checkout.mutations.checkout_delivery_method_update."
    "recalculate_checkout_discounts"
)
def test_checkout_delivery_method_update_perform_discounts_recalculation(
    recalculate_checkout_discounts_mock,
    api_client,
    checkout_with_fixed_discount,
    shipping_method,
):
    # given
    checkout = checkout_with_fixed_discount
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    variables = {"token": str(checkout.token), "deliveryMethodId": method_id}

    # when
    response = api_client.post_graphql(
        CHECKOUT_DELIVERY_METHOD_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)

    # then
    checkout.refresh_from_db()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    data = content["data"]["checkoutDeliveryMethodUpdate"]
    assert not data["errors"]

    checkout = data["checkout"]
    assert len(checkout["discounts"]) > 0
    assert len(checkout["lines"]) > 0
    recalculate_checkout_discounts_mock.assert_called_once_with(
        ANY, checkout_info, lines, ANY
    )
