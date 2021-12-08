from datetime import timedelta
from unittest.mock import patch

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from ...tests.utils import get_graphql_content
from ..mutations import invalidate_checkout_prices

ADD_CHECKOUT_LINE = """
mutation addCheckoutLine($checkoutId: ID!, $line: CheckoutLineInput!) {
  checkoutLinesAdd(checkoutId: $checkoutId, lines: [$line]) {
    errors {
      field
      message
    }
  }
}
"""


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_lines_add_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    stock,
):
    # given
    query = ADD_CHECKOUT_LINE
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
    mocked_function.assert_called_once_with(checkout_with_items, save=True)


UPDATE_CHECKOUT_LINE = """
mutation updateCheckoutLine($token: UUID, $line: CheckoutLineInput!) {
  checkoutLinesUpdate(token: $token, lines: [$line]) {
    errors {
      field
      message
    }
  }
}
"""


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_lines_update_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    stock,
):
    # given
    query = UPDATE_CHECKOUT_LINE
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
    mocked_function.assert_called_once_with(checkout_with_items, save=True)


DELETE_CHECKOUT_LINE = """
mutation deleteCheckoutLine($token: UUID, $lineId: ID){
  checkoutLineDelete(token: $token, lineId: $lineId) {
    errors {
      field
      message
    }
  }
}
"""


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_lines_delete_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
):
    # given
    query = DELETE_CHECKOUT_LINE
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
    mocked_function.assert_called_once_with(checkout_with_items, save=True)


UPDATE_CHECKOUT_SHIPPING_ADDRESS = """
mutation UpdateCheckoutShippingAddress($token: UUID, $address: AddressInput!) {
  checkoutShippingAddressUpdate(token: $token, shippingAddress: $address) {
    errors {
      field
      message
    }
  }
}
"""


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_shipping_address_update_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    graphql_address_data,
):
    # given
    query = UPDATE_CHECKOUT_SHIPPING_ADDRESS
    variables = {
        "token": checkout_with_items.token,
        "address": graphql_address_data,
    }
    mocked_function.return_value = []

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutShippingAddressUpdate"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items, save=False)


UPDATE_CHECKOUT_BILLING_ADDRESS = """
mutation UpdateCheckoutBillingAddress($token: UUID, $address: AddressInput!) {
  checkoutBillingAddressUpdate(token: $token, billingAddress: $address) {
    errors {
      field
      message
    }
  }
}
"""


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_billing_address_update_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    graphql_address_data,
):
    # given
    query = UPDATE_CHECKOUT_BILLING_ADDRESS
    variables = {
        "token": checkout_with_items.token,
        "address": graphql_address_data,
    }
    mocked_function.return_value = []

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutBillingAddressUpdate"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items, save=False)


@freeze_time("2020-12-12 12:00:00")
@pytest.mark.parametrize("save, minutes", [(True, 0), (False, 5)])
def test_invalidate_checkout_prices(checkout, save, minutes):
    # given
    checkout.price_expiration = timezone.now() + timedelta(minutes=5)
    checkout.save(update_fields=["price_expiration"])

    # when
    updated_fields = invalidate_checkout_prices(checkout, save=save)

    # then
    checkout.refresh_from_db()
    assert checkout.price_expiration == timezone.now() + timedelta(minutes=minutes)
    assert updated_fields == ["price_expiration"]
