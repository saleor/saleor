import uuid
from decimal import Decimal
from unittest import mock
from unittest.mock import ANY, patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from prices import Money, TaxedMoney

from saleor.account.models import User
from saleor.checkout import calculations
from saleor.checkout.error_codes import CheckoutErrorCode
from saleor.checkout.models import Checkout
from saleor.checkout.utils import clean_checkout, is_fully_paid
from saleor.core.payments import PaymentInterface
from saleor.core.taxes import zero_money
from saleor.graphql.checkout.mutations import (
    clean_shipping_method,
    update_checkout_shipping_method_if_invalid,
)
from saleor.order.models import Order
from saleor.payment import TransactionKind
from saleor.payment.interface import GatewayResponse
from saleor.plugins.manager import PluginsManager
from saleor.shipping import ShippingMethodType
from saleor.shipping.models import ShippingMethod
from saleor.warehouse.models import Stock

from ..utils import get_available_quantity_for_stock
from .utils import assert_no_permission, get_graphql_content


@pytest.fixture
def other_shipping_method(shipping_zone):
    return ShippingMethod.objects.create(
        name="DPD",
        minimum_order_price=Money(0, "USD"),
        type=ShippingMethodType.PRICE_BASED,
        price=Money(9, "USD"),
        shipping_zone=shipping_zone,
    )


@pytest.fixture(autouse=True)
def setup_dummy_gateway(settings):
    settings.PLUGINS = ["saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin"]
    return settings


def test_clean_shipping_method_after_shipping_address_changes_stay_the_same(
    checkout_with_single_item, address, shipping_method, other_shipping_method
):
    """Ensure the current shipping method applies to new address.

    If it does, then it doesn't need to be changed.
    """

    checkout = checkout_with_single_item
    checkout.shipping_address = address

    is_valid_method = clean_shipping_method(
        checkout, list(checkout), shipping_method, []
    )
    assert is_valid_method is True


def test_clean_shipping_method_does_nothing_if_no_shipping_method(
    checkout_with_single_item, address, other_shipping_method
):
    """If no shipping method was selected, it shouldn't return an error."""

    checkout = checkout_with_single_item
    checkout.shipping_address = address

    is_valid_method = clean_shipping_method(checkout, list(checkout), None, [])
    assert is_valid_method is True


def test_update_checkout_shipping_method_if_invalid(
    checkout_with_single_item,
    address,
    shipping_method,
    other_shipping_method,
    shipping_zone_without_countries,
):
    """If the shipping method is invalid, it should replace it."""

    checkout = checkout_with_single_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method

    shipping_method.shipping_zone = shipping_zone_without_countries
    shipping_method.save(update_fields=["shipping_zone"])

    update_checkout_shipping_method_if_invalid(checkout, list(checkout), None)

    assert checkout.shipping_method == other_shipping_method

    # Ensure the checkout's shipping method was saved
    checkout.refresh_from_db(fields=["shipping_method"])
    assert checkout.shipping_method == other_shipping_method


MUTATION_CHECKOUT_CREATE = """
    mutation createCheckout($checkoutInput: CheckoutCreateInput!) {
      checkoutCreate(input: $checkoutInput) {
        created
        checkout {
          id
          token
          email
          lines {
            quantity
          }
        }
        errors {
          field
          message
        }
        checkoutErrors {
          field
          message
          code
        }
      }
    }
"""


def test_checkout_create(api_client, stock, graphql_address_data):
    """Create checkout object using GraphQL API."""
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    # Look at the flag to see whether a new checkout was created or not
    assert content["created"] is True

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 1
    assert new_checkout.shipping_address is not None
    assert new_checkout.shipping_address.first_name == shipping_address["firstName"]
    assert new_checkout.shipping_address.last_name == shipping_address["lastName"]
    assert (
        new_checkout.shipping_address.street_address_1
        == shipping_address["streetAddress1"]
    )
    assert (
        new_checkout.shipping_address.street_address_2
        == shipping_address["streetAddress2"]
    )
    assert new_checkout.shipping_address.postal_code == shipping_address["postalCode"]
    assert new_checkout.shipping_address.country == shipping_address["country"]
    assert new_checkout.shipping_address.city == shipping_address["city"].upper()


def test_checkout_create_multiple_warehouse(
    api_client, variant_with_many_stocks, graphql_address_data
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 4, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    # Look at the flag to see whether a new checkout was created or not
    assert content["created"] is True

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 4


def test_checkout_create_with_null_as_addresses(api_client, stock):
    """Create checkout object using GraphQL API."""
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": None,
            "billingAddress": None,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    # Look at the flag to see whether a new checkout was created or not
    assert content["created"] is True

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 1
    assert new_checkout.shipping_address is None
    assert new_checkout.billing_address is None


def test_checkout_create_with_variant_without_inventory_tracking(
    api_client, variant_without_inventory_tracking
):
    """Create checkout object using GraphQL API."""
    variant = variant_without_inventory_tracking
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": None,
            "billingAddress": None,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    # Look at the flag to see whether a new checkout was created or not
    assert content["created"] is True

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 1
    assert new_checkout.shipping_address is None
    assert new_checkout.billing_address is None


@pytest.mark.parametrize(
    "quantity, expected_error_message, error_code",
    (
        (
            -1,
            "The quantity should be higher than zero.",
            CheckoutErrorCode.ZERO_QUANTITY,
        ),
        (
            51,
            "Cannot add more than 50 times this item.",
            CheckoutErrorCode.QUANTITY_GREATER_THAN_LIMIT,
        ),
    ),
)
def test_checkout_create_cannot_add_invalid_quantities(
    api_client,
    stock,
    graphql_address_data,
    quantity,
    expected_error_message,
    error_code,
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": quantity, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]
    assert content["errors"]
    assert content["errors"] == [
        {"field": "quantity", "message": expected_error_message}
    ]

    assert content["checkoutErrors"] == [
        {
            "field": "quantity",
            "message": expected_error_message,
            "code": error_code.name,
        }
    ]


def test_checkout_create_reuse_checkout(checkout, user_api_client, stock):
    # assign user to the checkout
    checkout.user = user_api_client.user
    checkout.save()
    variant = stock.product_variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"checkoutInput": {"lines": [{"quantity": 1, "variantId": variant_id}]}}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    # Look at the flag to see whether a new checkout was created or not
    assert not content["created"]

    # assert that existing checkout was reused and returned by mutation
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(checkout.token)

    # if checkout was reused it should be returned unmodified (e.g. without
    # adding new lines that was passed)
    assert checkout_data["lines"] == []


def test_checkout_create_required_email(api_client, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "",
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)

    errors = content["data"]["checkoutCreate"]["errors"]
    assert errors
    assert errors[0]["field"] == "email"
    assert errors[0]["message"] == "This field cannot be blank."

    checkout_errors = content["data"]["checkoutCreate"]["checkoutErrors"]
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name


def test_checkout_create_required_country_shipping_address(
    api_client, stock, graphql_address_data
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    del shipping_address["country"]
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)

    checkout_errors = content["data"]["checkoutCreate"]["checkoutErrors"]
    assert checkout_errors[0]["field"] == "country"
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name


def test_checkout_create_required_country_billing_address(
    api_client, stock, graphql_address_data
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    billing_address = graphql_address_data
    del billing_address["country"]
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            "billingAddress": billing_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)

    checkout_errors = content["data"]["checkoutCreate"]["checkoutErrors"]
    assert checkout_errors[0]["field"] == "country"
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name


def test_checkout_create_default_email_for_logged_in_customer(user_api_client, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"checkoutInput": {"lines": [{"quantity": 1, "variantId": variant_id}]}}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    customer = user_api_client.user
    content = get_graphql_content(response)
    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["data"]["checkoutCreate"]["checkout"]
    assert checkout_data["email"] == str(customer.email)
    assert new_checkout.user.id == customer.id
    assert new_checkout.email == customer.email


def test_checkout_create_logged_in_customer(user_api_client, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "email": user_api_client.user.email,
            "lines": [{"quantity": 1, "variantId": variant_id}],
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["data"]["checkoutCreate"]["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    checkout_user = new_checkout.user
    customer = user_api_client.user
    assert customer.id == checkout_user.id
    assert customer.default_shipping_address_id != new_checkout.shipping_address_id
    assert (
        customer.default_shipping_address.as_data()
        == new_checkout.shipping_address.as_data()
    )
    assert customer.default_billing_address_id != new_checkout.billing_address_id
    assert (
        customer.default_billing_address.as_data()
        == new_checkout.billing_address.as_data()
    )
    assert customer.email == new_checkout.email


def test_checkout_create_logged_in_customer_custom_email(user_api_client, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    customer = user_api_client.user
    custom_email = "custom@example.com"
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": custom_email,
        }
    }
    assert not Checkout.objects.exists()
    assert not custom_email == customer.email
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["data"]["checkoutCreate"]["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    checkout_user = new_checkout.user
    assert customer.id == checkout_user.id
    assert new_checkout.email == custom_email


def test_checkout_create_logged_in_customer_custom_addresses(
    user_api_client, stock, graphql_address_data
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    billing_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "email": user_api_client.user.email,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "shippingAddress": shipping_address,
            "billingAddress": billing_address,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["data"]["checkoutCreate"]["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    checkout_user = new_checkout.user
    customer = user_api_client.user
    assert customer.id == checkout_user.id
    assert not (
        customer.default_shipping_address_id == new_checkout.shipping_address_id
    )
    assert not (customer.default_billing_address_id == new_checkout.billing_address_id)
    assert new_checkout.shipping_address.first_name == shipping_address["firstName"]
    assert new_checkout.billing_address.first_name == billing_address["firstName"]


def test_checkout_create_check_lines_quantity_multiple_warehouse(
    user_api_client, variant_with_many_stocks, graphql_address_data
):
    variant = variant_with_many_stocks

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 16, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["errors"][0]["message"] == (
        "Could not add item Test product (SKU_A). Only 7 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


def test_checkout_create_check_lines_quantity(
    user_api_client, stock, graphql_address_data
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 16, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["errors"][0]["message"] == (
        "Could not add item Test product (SKU_A). Only 15 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


@pytest.fixture
def expected_dummy_gateway():
    return {
        "id": "mirumee.payments.dummy",
        "name": "Dummy",
        "config": [{"field": "store_customer_card", "value": "false"}],
    }


def test_checkout_available_payment_gateways(
    api_client, checkout_with_item, expected_dummy_gateway
):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           availablePaymentGateways {
               id
               name
               config {
                   field
                   value
               }
           }
        }
    }
    """
    variables = {"token": str(checkout_with_item.token)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["availablePaymentGateways"] == [expected_dummy_gateway]


def test_checkout_available_shipping_methods(
    api_client, checkout_with_item, address, shipping_zone
):
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
            availableShippingMethods {
                name
            }
        }
    }
    """
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    shipping_method = shipping_zone.shipping_methods.first()
    assert data["availableShippingMethods"] == [{"name": shipping_method.name}]


@pytest.mark.parametrize(
    "expected_price_type, expected_price, display_gross_prices",
    (("gross", 13, True), ("net", 10, False)),
)
def test_checkout_available_shipping_methods_with_price_displayed(
    expected_price_type,
    expected_price,
    display_gross_prices,
    monkeypatch,
    api_client,
    checkout_with_item,
    address,
    shipping_zone,
    site_settings,
):
    shipping_method = shipping_zone.shipping_methods.first()
    taxed_price = TaxedMoney(net=Money(10, "USD"), gross=Money(13, "USD"))
    apply_taxes_to_shipping_mock = mock.Mock(return_value=taxed_price)
    monkeypatch.setattr(
        PluginsManager, "apply_taxes_to_shipping", apply_taxes_to_shipping_mock
    )
    site_settings.display_gross_prices = display_gross_prices
    site_settings.save()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
            availableShippingMethods {
                name
                price {
                    amount
                }
            }
        }
    }
    """
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    apply_taxes_to_shipping_mock.assert_called_once_with(
        shipping_method.price, mock.ANY
    )
    assert data["availableShippingMethods"] == [
        {"name": "DHL", "price": {"amount": expected_price}}
    ]


def test_checkout_no_available_shipping_methods_without_address(
    api_client, checkout_with_item
):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
            availableShippingMethods {
                name
            }
        }
    }
    """
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableShippingMethods"] == []


def test_checkout_no_available_shipping_methods_without_lines(api_client, checkout):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
            availableShippingMethods {
                name
            }
        }
    }
    """
    variables = {"token": checkout.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableShippingMethods"] == []


MUTATION_CHECKOUT_LINES_ADD = """
    mutation checkoutLinesAdd(
            $checkoutId: ID!, $lines: [CheckoutLineInput!]!) {
        checkoutLinesAdd(checkoutId: $checkoutId, lines: $lines) {
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
    assert line.quantity == 3
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["errors"]
    checkout.refresh_from_db()
    line = checkout.lines.latest("pk")
    assert line.variant == variant
    assert line.quantity == 1

    mocked_update_shipping_method.assert_called_once_with(
        checkout, list(checkout), mock.ANY
    )


def test_checkout_lines_add_too_many(user_api_client, checkout_with_item, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_with_item.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 51}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)["data"]["checkoutLinesAdd"]

    assert content["errors"]
    assert content["errors"] == [
        {"field": "quantity", "message": "Cannot add more than 50 times this item."}
    ]


def test_checkout_lines_add_empty_checkout(user_api_client, checkout, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
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
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
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
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 16}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert data["errors"][0]["message"] == (
        "Could not add item Test product (SKU_A). Only 15 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


def test_checkout_lines_invalid_variant_id(user_api_client, checkout, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    invalid_variant_id = "InvalidId"
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
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
            $checkoutId: ID!, $lines: [CheckoutLineInput!]!) {
        checkoutLinesUpdate(checkoutId: $checkoutId, lines: $lines) {
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
def test_checkout_lines_update(
    mocked_update_shipping_method, user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    assert checkout.lines.count() == 1
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
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1

    mocked_update_shipping_method.assert_called_once_with(
        checkout, list(checkout), mock.ANY
    )


def test_checkout_lines_update_invalid_checkout_id(user_api_client):
    variables = {"checkoutId": "test", "lines": []}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]
    assert data["errors"][0]["field"] == "checkoutId"


def test_checkout_lines_update_check_lines_quantity(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    line = checkout.lines.first()
    variant = line.variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 11}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert data["errors"][0]["message"] == (
        "Could not add item Test product (123). Only 10 remaining in stock."
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
    assert checkout.quantity == 1


MUTATION_CHECKOUT_LINES_DELETE = """
    mutation checkoutLineDelete($checkoutId: ID!, $lineId: ID!) {
        checkoutLineDelete(checkoutId: $checkoutId, lineId: $lineId) {
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
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.quantity == 3

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)

    variables = {"checkoutId": checkout_id, "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 0
    mocked_update_shipping_method.assert_called_once_with(
        checkout, list(checkout), mock.ANY
    )


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
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 0}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 0
    mocked_update_shipping_method.assert_called_once_with(
        checkout, list(checkout), mock.ANY
    )


def test_checkout_customer_attach(
    api_client, user_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    assert checkout.user is None

    query = """
        mutation checkoutCustomerAttach($checkoutId: ID!, $customerId: ID!) {
            checkoutCustomerAttach(
                    checkoutId: $checkoutId, customerId: $customerId) {
                checkout {
                    token
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"checkoutId": checkout_id, "customerId": customer_id}

    # Mutation should fail for unauthenticated customers
    response = api_client.post_graphql(query, variables)
    assert_no_permission(response)

    # Mutation should succeed for authenticated customer
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user

    # Mutation with ID of a different user should fail as well
    other_customer = User.objects.create_user("othercustomer@example.com", "password")
    variables["customerId"] = graphene.Node.to_global_id("User", other_customer.pk)
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


MUTATION_CHECKOUT_CUSTOMER_DETACH = """
    mutation checkoutCustomerDetach($checkoutId: ID!) {
        checkoutCustomerDetach(checkoutId: $checkoutId) {
            checkout {
                token
            }
            errors {
                field
                message
            }
        }
    }
    """


def test_checkout_customer_detach(user_api_client, checkout_with_item, customer_user):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.save(update_fields=["user"])

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id}

    # Mutation should succeed if the user owns this checkout.
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerDetach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user is None

    # Mutation should fail when user calling it doesn't own the checkout.
    other_user = User.objects.create_user("othercustomer@example.com", "password")
    checkout.user = other_user
    checkout.save()
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH, variables
    )
    assert_no_permission(response)


MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE = """
    mutation checkoutShippingAddressUpdate(
            $checkoutId: ID!, $shippingAddress: AddressInput!) {
        checkoutShippingAddressUpdate(
                checkoutId: $checkoutId, shippingAddress: $shippingAddress) {
            checkout {
                token,
                id
            },
            errors {
                field,
                message,
            }
            checkoutErrors {
                field
                message
                code
            }
        }
    }"""


@mock.patch(
    "saleor.graphql.checkout.mutations.update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_shipping_address_update(
    mocked_update_shipping_method,
    user_api_client,
    checkout_with_item,
    graphql_address_data,
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    shipping_address = graphql_address_data
    variables = {"checkoutId": checkout_id, "shippingAddress": shipping_address}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.shipping_address is not None
    assert checkout.shipping_address.first_name == shipping_address["firstName"]
    assert checkout.shipping_address.last_name == shipping_address["lastName"]
    assert (
        checkout.shipping_address.street_address_1 == shipping_address["streetAddress1"]
    )
    assert (
        checkout.shipping_address.street_address_2 == shipping_address["streetAddress2"]
    )
    assert checkout.shipping_address.postal_code == shipping_address["postalCode"]
    assert checkout.shipping_address.country == shipping_address["country"]
    assert checkout.shipping_address.city == shipping_address["city"].upper()
    mocked_update_shipping_method.assert_called_once_with(
        checkout, list(checkout), mock.ANY
    )


def test_checkout_shipping_address_with_invalid_phone_number_returns_error(
    user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["phone"] = "+33600000"

    response = get_graphql_content(
        user_api_client.post_graphql(
            MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE,
            {
                "checkoutId": graphene.Node.to_global_id("Checkout", checkout.pk),
                "shippingAddress": shipping_address,
            },
        )
    )["data"]["checkoutShippingAddressUpdate"]
    assert response["errors"] == [
        {"field": "phone", "message": "'+33600000' is not a valid phone number."}
    ]
    assert response["checkoutErrors"] == [
        {
            "field": "phone",
            "message": "'+33600000' is not a valid phone number.",
            "code": CheckoutErrorCode.INVALID.name,
        }
    ]


@pytest.mark.parametrize(
    "number", ["+48321321888", "+44 (113) 892-1113", "00 44 (0) 20 7839 1377"]
)
def test_checkout_shipping_address_update_with_phone_country_prefix(
    number, user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    shipping_address = graphql_address_data
    shipping_address["phone"] = number
    variables = {"checkoutId": checkout_id, "shippingAddress": shipping_address}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]


def test_checkout_shipping_address_update_without_phone_country_prefix(
    user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    shipping_address = graphql_address_data
    shipping_address["phone"] = "+1-202-555-0132"
    variables = {"checkoutId": checkout_id, "shippingAddress": shipping_address}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]


def test_checkout_billing_address_update(
    user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    query = """
    mutation checkoutBillingAddressUpdate(
            $checkoutId: ID!, $billingAddress: AddressInput!) {
        checkoutBillingAddressUpdate(
                checkoutId: $checkoutId, billingAddress: $billingAddress) {
            checkout {
                token,
                id
            },
            errors {
                field,
                message
            }
        }
    }
    """
    billing_address = graphql_address_data

    variables = {"checkoutId": checkout_id, "billingAddress": billing_address}

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutBillingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.billing_address is not None
    assert checkout.billing_address.first_name == billing_address["firstName"]
    assert checkout.billing_address.last_name == billing_address["lastName"]
    assert (
        checkout.billing_address.street_address_1 == billing_address["streetAddress1"]
    )
    assert (
        checkout.billing_address.street_address_2 == billing_address["streetAddress2"]
    )
    assert checkout.billing_address.postal_code == billing_address["postalCode"]
    assert checkout.billing_address.country == billing_address["country"]
    assert checkout.billing_address.city == billing_address["city"].upper()


CHECKOUT_EMAIL_UPDATE_MUTATION = """
    mutation checkoutEmailUpdate($checkoutId: ID!, $email: String!) {
        checkoutEmailUpdate(checkoutId: $checkoutId, email: $email) {
            checkout {
                id,
                email
            },
            errors {
                field,
                message
            }
            checkoutErrors {
                field,
                message
                code
            }
        }
    }
"""


def test_checkout_email_update(user_api_client, checkout_with_item):
    checkout = checkout_with_item
    assert not checkout.email
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    email = "test@example.com"
    variables = {"checkoutId": checkout_id, "email": email}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutEmailUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.email == email


def test_checkout_email_update_validation(user_api_client, checkout_with_item):
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_with_item.pk)
    variables = {"checkoutId": checkout_id, "email": ""}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    errors = content["data"]["checkoutEmailUpdate"]["errors"]
    assert errors
    assert errors[0]["field"] == "email"
    assert errors[0]["message"] == "This field cannot be blank."

    checkout_errors = content["data"]["checkoutEmailUpdate"]["checkoutErrors"]
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name


MUTATION_CHECKOUT_COMPLETE = """
    mutation checkoutComplete($checkoutId: ID!, $redirectUrl: String) {
        checkoutComplete(checkoutId: $checkoutId, redirectUrl: $redirectUrl) {
            order {
                id,
                token
            },
            errors {
                field,
                message
            }
            confirmationNeeded
        }
    }
    """


@pytest.mark.integration
def test_checkout_complete(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):

    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    gift_current_balance = checkout.get_total_gift_cards_balance()
    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.token == order_token
    assert order.total.gross == total.gross - gift_current_balance
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money()
    assert gift_card.last_used_on

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_checkout_with_voucher_complete(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    payment_dummy,
    address,
    shipping_method,
):
    voucher_used_count = voucher_percentage.used

    checkout = checkout_with_voucher_percentage
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.token == order_token
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    voucher_percentage.refresh_from_db()
    assert voucher_percentage.used == voucher_used_count + 1

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_checkout_complete_without_inventory_tracking(
    user_api_client,
    checkout_with_variant_without_inventory_tracking,
    payment_dummy,
    address,
    shipping_method,
):
    checkout = checkout_with_variant_without_inventory_tracking
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.token == order_token
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert not order_line.allocations.all()
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


ERROR_GATEWAY_RESPONSE = GatewayResponse(
    is_success=False,
    action_required=False,
    kind=TransactionKind.CAPTURE,
    amount=Decimal(0),
    currency="usd",
    transaction_id="1234",
    error="ERROR",
)


def _process_payment_transaction_returns_error(*args, **kwards):
    return ERROR_GATEWAY_RESPONSE


def _process_payment_raise_error(*args, **kwargs):
    raise Exception("Oops! Something went wrong.")


@pytest.fixture(
    params=[_process_payment_raise_error, _process_payment_transaction_returns_error]
)
def error_side_effect(request):
    return request.param


@pytest.fixture
def fake_manager(mocker):
    return mocker.Mock(spec=PaymentInterface)


@pytest.fixture
def mock_get_manager(mocker, fake_manager):
    manager = mocker.patch(
        "saleor.payment.gateway.get_plugins_manager",
        autospec=True,
        return_value=fake_manager,
    )
    yield fake_manager
    manager.assert_called_once()


def test_checkout_complete_does_not_delete_checkout_after_unsuccessful_payment(
    mock_get_manager,
    error_side_effect,
    user_api_client,
    checkout_with_voucher,
    voucher,
    payment_dummy,
    address,
    shipping_method,
):
    mock_get_manager.process_payment.side_effect = error_side_effect
    expected_voucher_usage_count = voucher.used
    checkout = checkout_with_voucher
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    taxed_total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = taxed_total.gross.amount
    payment.currency = taxed_total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    get_graphql_content(response)

    assert Order.objects.count() == orders_count

    payment.refresh_from_db(fields=["order"])
    transaction = payment.transactions.get()
    assert transaction.error
    assert payment.order is None

    # ensure the voucher usage count was not incremented
    voucher.refresh_from_db(fields=["used"])
    assert voucher.used == expected_voucher_usage_count

    assert Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should not have been deleted"


def test_checkout_complete_invalid_checkout_id(user_api_client):
    checkout_id = "invalidId"
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["message"] == "Couldn't resolve to a node: invalidId"
    assert data["errors"][0]["field"] == "checkoutId"
    assert orders_count == Order.objects.count()


def test_checkout_complete_no_payment(
    user_api_client, checkout_with_item, address, shipping_method
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["message"] == (
        "Provided payment methods can not cover the checkout's total amount"
    )
    assert orders_count == Order.objects.count()


ACTION_REQUIRED_GATEWAY_RESPONSE = GatewayResponse(
    is_success=True,
    action_required=True,
    kind=TransactionKind.CAPTURE,
    amount=Decimal(3.0),
    currency="usd",
    transaction_id="1234",
    error=None,
)

TRANSACTION_CONFIRM_GATEWAY_RESPONSE = GatewayResponse(
    is_success=False,
    action_required=False,
    kind=TransactionKind.CONFIRM,
    amount=Decimal(3.0),
    currency="usd",
    transaction_id="1234",
    error=None,
)


def test_checkout_complete_confirmation_needed(
    mock_get_manager,
    user_api_client,
    checkout_with_item,
    address,
    payment_dummy,
    shipping_method,
):
    mock_get_manager.process_payment.return_value = ACTION_REQUIRED_GATEWAY_RESPONSE
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    orders_count = Order.objects.count()

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    assert data["confirmationNeeded"] is True

    new_orders_count = Order.objects.count()
    assert new_orders_count == orders_count
    checkout.refresh_from_db()
    payment_dummy.refresh_from_db()
    assert payment_dummy.is_active
    assert payment_dummy.to_confirm


def test_checkout_confirm(
    user_api_client,
    mock_get_manager,
    checkout_with_item,
    payment_txn_to_confirm,
    address,
    shipping_method,
):
    mock_get_manager.confirm_payment.return_value = ACTION_REQUIRED_GATEWAY_RESPONSE

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_txn_to_confirm
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    orders_count = Order.objects.count()

    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["errors"]
    assert not data["confirmationNeeded"]

    mock_get_manager.confirm_payment.assert_called_once()

    new_orders_count = Order.objects.count()
    assert new_orders_count == orders_count + 1


def test_checkout_complete_insufficient_stock(
    user_api_client, checkout_with_item, address, payment_dummy, shipping_method
):
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()
    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["message"] == "Insufficient product stock: 123"
    assert orders_count == Order.objects.count()


def test_checkout_complete_without_redirect_url(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):

    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    gift_current_balance = checkout.get_total_gift_cards_balance()
    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.token == order_token
    assert order.total.gross == total.gross - gift_current_balance

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money()
    assert gift_card.last_used_on

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_fetch_checkout_by_token(user_api_client, checkout_with_item):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           token,
           lines {
                variant {
                    product {
                        name
                    }
                }
           }
        }
    }
    """
    variables = {"token": str(checkout_with_item.token)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["token"] == str(checkout_with_item.token)
    assert len(data["lines"]) == checkout_with_item.lines.count()


def test_anonymous_client_cant_fetch_checkout_user(api_client, checkout):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           user {
               id
           }
        }
    }
    """
    variables = {"token": str(checkout.token)}
    response = api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_authorized_access_to_checkout_user_as_customer(
    user_api_client, checkout, customer_user,
):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           user {
               id
           }
        }
    }
    """
    checkout.user = customer_user
    checkout.save()

    variables = {"token": str(checkout.token)}
    customer_user_id = graphene.Node.to_global_id("User", customer_user.id)

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["user"]["id"] == customer_user_id


def test_authorized_access_to_checkout_user_as_staff(
    staff_api_client,
    checkout,
    customer_user,
    permission_manage_users,
    permission_manage_checkouts,
):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           user {
               id
           }
        }
    }
    """
    checkout.user = customer_user
    checkout.save()

    variables = {"token": str(checkout.token)}
    customer_user_id = graphene.Node.to_global_id("User", customer_user.id)

    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_users, permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["user"]["id"] == customer_user_id


def test_authorized_access_to_checkout_user_as_staff_no_permission(
    staff_api_client, checkout, customer_user, permission_manage_checkouts,
):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           user {
               id
           }
        }
    }
    """
    checkout.user = customer_user
    checkout.save()

    variables = {"token": str(checkout.token)}

    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    assert_no_permission(response)


QUERY_CHECKOUT = """
query getCheckout($token: UUID!) {
    checkout(token: $token) {
        token
    }
}
"""


def test_query_anonymous_customer_checkout_as_anonymous_customer(api_client, checkout):
    variables = {"token": str(checkout.token)}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_anonymous_customer_checkout_as_customer(user_api_client, checkout):
    variables = {"token": str(checkout.token)}
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_anonymous_customer_checkout_as_staff_user(
    staff_api_client, checkout, permission_manage_checkouts
):
    variables = {"token": str(checkout.token)}
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_anonymous_customer_checkout_as_app(
    app_api_client, checkout, permission_manage_checkouts
):
    variables = {"token": str(checkout.token)}
    response = app_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_customer_checkout_as_anonymous_customer(
    api_client, checkout, customer_user
):
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"token": str(checkout.token)}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert not content["data"]["checkout"]


def test_query_customer_checkout_as_customer(user_api_client, checkout, customer_user):
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"token": str(checkout.token)}
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_other_customer_checkout_as_customer(
    user_api_client, checkout, staff_user
):
    checkout.user = staff_user
    checkout.save(update_fields=["user"])
    variables = {"token": str(checkout.token)}
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert not content["data"]["checkout"]


def test_query_customer_checkout_as_staff_user(
    app_api_client, checkout, customer_user, permission_manage_checkouts
):
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"token": str(checkout.token)}
    response = app_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_customer_checkout_as_app(
    staff_api_client, checkout, customer_user, permission_manage_checkouts
):
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"token": str(checkout.token)}
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_fetch_checkout_invalid_token(user_api_client):
    variables = {"token": str(uuid.uuid4())}
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data is None


def test_checkout_prices(user_api_client, checkout_with_item):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           token,
           totalPrice {
                currency
                gross {
                    amount
                }
            }
            subtotalPrice {
                currency
                gross {
                    amount
                }
            }
           lines {
                totalPrice {
                    currency
                    gross {
                        amount
                    }
                }
           }
        }
    }
    """
    variables = {"token": str(checkout_with_item.token)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["token"] == str(checkout_with_item.token)
    assert len(data["lines"]) == checkout_with_item.lines.count()
    total = calculations.checkout_total(
        checkout=checkout_with_item, lines=list(checkout_with_item)
    )
    assert data["totalPrice"]["gross"]["amount"] == (total.gross.amount)
    subtotal = calculations.checkout_subtotal(
        checkout=checkout_with_item, lines=list(checkout_with_item)
    )
    assert data["subtotalPrice"]["gross"]["amount"] == (subtotal.gross.amount)


MUTATION_UPDATE_SHIPPING_METHOD = """
    mutation checkoutShippingMethodUpdate(
            $checkoutId:ID!, $shippingMethodId:ID!){
        checkoutShippingMethodUpdate(
            checkoutId:$checkoutId, shippingMethodId:$shippingMethodId) {
            errors {
                field
                message
            }
            checkout {
                id
            }
        }
    }
"""


@pytest.mark.parametrize("is_valid_shipping_method", (True, False))
@patch("saleor.graphql.checkout.mutations.clean_shipping_method")
def test_checkout_shipping_method_update(
    mock_clean_shipping,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    is_valid_shipping_method,
):
    checkout = checkout_with_item
    query = MUTATION_UPDATE_SHIPPING_METHOD
    mock_clean_shipping.return_value = is_valid_shipping_method

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"checkoutId": checkout_id, "shippingMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    mock_clean_shipping.assert_called_once_with(
        checkout=checkout, lines=list(checkout), method=shipping_method, discounts=ANY
    )

    if is_valid_shipping_method:
        assert not data["errors"]
        assert data["checkout"]["id"] == checkout_id
        assert checkout.shipping_method == shipping_method
    else:
        assert data["errors"] == [
            {
                "field": "shippingMethod",
                "message": "This shipping method is not applicable.",
            }
        ]
        assert checkout.shipping_method is None


def test_query_checkout_line(checkout_with_item, user_api_client):
    query = """
    query checkoutLine($id: ID) {
        checkoutLine(id: $id) {
            id
        }
    }
    """
    checkout = checkout_with_item
    line = checkout.lines.first()
    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    variables = {"id": line_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    received_id = content["data"]["checkoutLine"]["id"]
    assert received_id == line_id


def test_query_checkouts(
    checkout_with_item, staff_api_client, permission_manage_checkouts
):
    query = """
    {
        checkouts(first: 20) {
            edges {
                node {
                    token
                }
            }
        }
    }
    """
    checkout = checkout_with_item
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_checkouts]
    )
    content = get_graphql_content(response)
    received_checkout = content["data"]["checkouts"]["edges"][0]["node"]
    assert str(checkout.token) == received_checkout["token"]


def test_query_checkout_lines(
    checkout_with_item, staff_api_client, permission_manage_checkouts
):
    query = """
    {
        checkoutLines(first: 20) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    checkout = checkout_with_item
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_checkouts]
    )
    content = get_graphql_content(response)
    lines = content["data"]["checkoutLines"]["edges"]
    checkout_lines_ids = [line["node"]["id"] for line in lines]
    expected_lines_ids = [
        graphene.Node.to_global_id("CheckoutLine", item.pk) for item in checkout
    ]
    assert expected_lines_ids == checkout_lines_ids


def test_clean_checkout(checkout_with_item, payment_dummy, address, shipping_method):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()
    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    # Shouldn't raise any errors
    clean_checkout(checkout, list(checkout), None)


def test_clean_checkout_no_shipping_method(checkout_with_item, address):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save()

    with pytest.raises(ValidationError) as e:
        clean_checkout(checkout, list(checkout), None)

    msg = "Shipping method is not set"
    assert e.value.error_list[0].message == msg


def test_clean_checkout_no_shipping_address(checkout_with_item, shipping_method):
    checkout = checkout_with_item
    checkout.shipping_method = shipping_method
    checkout.save()

    with pytest.raises(ValidationError) as e:
        clean_checkout(checkout, list(checkout), None)
    msg = "Shipping address is not set"
    assert e.value.error_list[0].message == msg


def test_clean_checkout_invalid_shipping_method(
    checkout_with_item, address, shipping_zone_without_countries
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    shipping_method = shipping_zone_without_countries.shipping_methods.first()
    checkout.shipping_method = shipping_method
    checkout.save()

    with pytest.raises(ValidationError) as e:
        clean_checkout(checkout, list(checkout), None)

    msg = "Shipping method is not valid for your shipping address"
    assert e.value.error_list[0].message == msg


def test_clean_checkout_no_billing_address(
    checkout_with_item, address, shipping_method
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()

    with pytest.raises(ValidationError) as e:
        clean_checkout(checkout, list(checkout), None)
    msg = "Billing address is not set"
    assert e.value.error_list[0].message == msg


def test_clean_checkout_no_payment(checkout_with_item, shipping_method, address):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    with pytest.raises(ValidationError) as e:
        clean_checkout(checkout, list(checkout), None)

    msg = "Provided payment methods can not cover the checkout's total amount"
    assert e.value.error_list[0].message == msg


def test_is_fully_paid(checkout_with_item, payment_dummy):
    checkout = checkout_with_item
    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    is_paid = is_fully_paid(checkout, list(checkout), None)
    assert is_paid


def test_is_fully_paid_many_payments(checkout_with_item, payment_dummy):
    checkout = checkout_with_item
    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount - 1
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    payment2 = payment_dummy
    payment2.pk = None
    payment2.is_active = True
    payment2.order = None
    payment2.total = 1
    payment2.currency = total.gross.currency
    payment2.checkout = checkout
    payment2.save()
    is_paid = is_fully_paid(checkout, list(checkout), None)
    assert is_paid


def test_is_fully_paid_partially_paid(checkout_with_item, payment_dummy):
    checkout = checkout_with_item
    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount - 1
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    is_paid = is_fully_paid(checkout, list(checkout), None)
    assert not is_paid


def test_is_fully_paid_no_payment(checkout_with_item):
    checkout = checkout_with_item
    is_paid = is_fully_paid(checkout, list(checkout), None)
    assert not is_paid
