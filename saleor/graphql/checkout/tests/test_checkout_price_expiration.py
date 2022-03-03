from datetime import timedelta
from unittest import mock
from unittest.mock import patch

import graphene
from django.utils import timezone
from freezegun import freeze_time

from ....checkout.utils import invalidate_checkout_prices
from ...tests.utils import get_graphql_content

ADD_CHECKOUT_LINES = """
mutation addCheckoutLines($checkoutId: ID!, $line: CheckoutLineInput!) {
  checkoutLinesAdd(checkoutId: $checkoutId, lines: [$line]) {
    errors {
      field
      message
    }
  }
}
"""


@patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add.invalidate_checkout_prices"
)
def test_checkout_lines_add_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    stock,
):
    # given
    query = ADD_CHECKOUT_LINES
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


UPDATE_CHECKOUT_LINES = """
mutation updateCheckoutLines($token: UUID!, $line: CheckoutLineInput!) {
  checkoutLinesUpdate(token: $token, lines: [$line]) {
    errors {
      field
      message
    }
  }
}
"""


@patch(
    "saleor.graphql.checkout.mutations.checkout_lines_add.invalidate_checkout_prices"
)
def test_checkout_lines_update_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    stock,
):
    # given
    query = UPDATE_CHECKOUT_LINES
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


DELETE_CHECKOUT_LINES = """
mutation deleteCheckoutLines($token: UUID!, $lineId: ID){
  checkoutLinesDelete(token: $token, linesIds: [$lineId]) {
    errors {
      field
      message
    }
  }
}
"""


@patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete.invalidate_checkout_prices"
)
def test_checkout_lines_delete_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
):
    # given
    query = DELETE_CHECKOUT_LINES
    variables = {
        "token": checkout_with_items.token,
        "lineId": graphene.Node.to_global_id(
            "CheckoutLine", checkout_with_items.lines.first().pk
        ),
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutLinesDelete"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items, save=True)


DELETE_CHECKOUT_LINE = """
mutation deleteCheckoutLine($token: UUID!, $lineId: ID){
  checkoutLineDelete(token: $token, lineId: $lineId) {
    errors {
      field
      message
    }
  }
}
"""


@patch(
    "saleor.graphql.checkout.mutations.checkout_line_delete.invalidate_checkout_prices"
)
def test_checkout_line_delete_invalidate_prices(
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


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update"
    ".invalidate_checkout_prices"
)
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


@patch(
    "saleor.graphql.checkout.mutations.checkout_billing_address_update"
    ".invalidate_checkout_prices"
)
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


UPDATE_CHECKOUT_SHIPPING_METHOD = """
mutation updateCheckoutShippingOptions($token: UUID, $shippingMethodId: ID!) {
  checkoutShippingMethodUpdate(token: $token, shippingMethodId: $shippingMethodId) {
    errors {
      field
      message
    }
  }
}
"""


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "invalidate_checkout_prices",
    wraps=invalidate_checkout_prices,
)
def test_checkout_shipping_method_update_invalidate_prices(
    mocked_invalidate_checkout_prices,
    api_client,
    checkout_with_shipping_address,
    shipping_method,
):
    # given
    checkout = checkout_with_shipping_address
    checkout.price_expiration = timezone.now()
    checkout.save(update_fields=["price_expiration"])
    query = UPDATE_CHECKOUT_SHIPPING_METHOD
    variables = {
        "token": checkout.token,
        "shippingMethodId": graphene.Node.to_global_id(
            "ShippingMethod", shipping_method.pk
        ),
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    checkout.refresh_from_db()
    assert not response["data"]["checkoutShippingMethodUpdate"]["errors"]
    assert mocked_invalidate_checkout_prices.call_count == 1


UPDATE_CHECKOUT_DELIVERY_METHOD = """
mutation updateCheckoutDeliveryOptions($token: UUID, $deliveryMethodId: ID) {
  checkoutDeliveryMethodUpdate(token: $token, deliveryMethodId: $deliveryMethodId) {
    errors {
      field
      message
    }
  }
}
"""


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_delivery_method_update."
    "invalidate_checkout_prices",
    wraps=invalidate_checkout_prices,
)
def test_checkout_delivery_method_update_invalidate_prices(
    mocked_invalidate_checkout_prices,
    api_client,
    checkout_with_shipping_address_for_cc,
    warehouses_for_cc,
):
    checkout = checkout_with_shipping_address_for_cc
    checkout.price_expiration = timezone.now()
    checkout.save(update_fields=["price_expiration"])
    query = UPDATE_CHECKOUT_DELIVERY_METHOD
    variables = {
        "token": checkout.token,
        "deliveryMethodId": graphene.Node.to_global_id(
            "Warehouse", warehouses_for_cc[1].pk
        ),
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    checkout.refresh_from_db()
    assert not response["data"]["checkoutDeliveryMethodUpdate"]["errors"]
    assert mocked_invalidate_checkout_prices.call_count == 1


@freeze_time("2020-12-12 12:00:00")
def test_invalidate_checkout_prices_with_save(checkout):
    # given
    checkout.price_expiration = timezone.now() + timedelta(minutes=5)
    checkout.save(update_fields=["price_expiration"])

    # when
    updated_fields = invalidate_checkout_prices(checkout, save=True)

    # then
    checkout.refresh_from_db()
    assert checkout.price_expiration == timezone.now()
    assert updated_fields == ["price_expiration", "last_change"]


@freeze_time("2020-12-12 12:00:00")
def test_invalidate_checkout_prices_without_save(checkout):
    # given
    original_expiration = checkout.price_expiration = timezone.now() + timedelta(
        minutes=5
    )
    checkout.save(update_fields=["price_expiration"])

    # when
    updated_fields = invalidate_checkout_prices(checkout, save=False)

    # then
    checkout.refresh_from_db()
    assert checkout.price_expiration == original_expiration
    assert updated_fields == ["price_expiration", "last_change"]
