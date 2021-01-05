import datetime
import uuid
import warnings
from decimal import Decimal
from unittest import mock
from unittest.mock import ANY, patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from django_countries.fields import Country
from prices import Money, TaxedMoney

from ....account.models import User
from ....channel.utils import DEPRECATION_WARNING_MESSAGE
from ....checkout import calculations
from ....checkout.checkout_cleaner import (
    clean_checkout_payment,
    clean_checkout_shipping,
)
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.models import Checkout
from ....checkout.utils import add_variant_to_checkout, fetch_checkout_lines
from ....core.payments import PaymentInterface
from ....payment import TransactionKind
from ....payment.interface import GatewayResponse
from ....plugins.manager import PluginsManager, get_plugins_manager
from ....plugins.tests.sample_plugins import ActiveDummyPaymentGateway
from ....product.models import ProductChannelListing
from ....shipping import models as shipping_models
from ....warehouse.models import Stock
from ...tests.utils import assert_no_permission, get_graphql_content
from ..mutations import (
    clean_shipping_method,
    update_checkout_shipping_method_if_invalid,
)


def test_clean_shipping_method_after_shipping_address_changes_stay_the_same(
    checkout_with_single_item, address, shipping_method, other_shipping_method
):
    """Ensure the current shipping method applies to new address.

    If it does, then it doesn't need to be changed.
    """

    checkout = checkout_with_single_item
    checkout.shipping_address = address

    lines = fetch_checkout_lines(checkout)
    is_valid_method = clean_shipping_method(checkout, lines, shipping_method, [])
    assert is_valid_method is True


def test_clean_shipping_method_does_nothing_if_no_shipping_method(
    checkout_with_single_item, address, other_shipping_method
):
    """If no shipping method was selected, it shouldn't return an error."""

    checkout = checkout_with_single_item
    checkout.shipping_address = address
    lines = fetch_checkout_lines(checkout)
    is_valid_method = clean_shipping_method(checkout, lines, None, [])
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

    lines = fetch_checkout_lines(checkout)
    update_checkout_shipping_method_if_invalid(checkout, lines, None)

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
        checkoutErrors {
          field
          message
          code
          variants
        }
      }
    }
"""


@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_checkout_create_triggers_webhooks(
    mocked_webhook_trigger,
    user_api_client,
    stock,
    graphql_address_data,
    settings,
    channel_USD,
):
    """Create checkout object using GraphQL API."""
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": user_api_client.user.email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    get_graphql_content(response)

    assert mocked_webhook_trigger.called


def test_checkout_create_with_default_channel(
    api_client, stock, graphql_address_data, channel_USD
):
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
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
        content = get_graphql_content(response)["data"]["checkoutCreate"]

    assert content["created"] is True

    new_checkout = Checkout.objects.first()

    assert new_checkout.channel == channel_USD

    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_checkout_create_with_inactive_channel(
    api_client, stock, graphql_address_data, channel_USD
):
    channel = channel_USD
    channel.is_active = False
    channel.save()

    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["checkoutErrors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.CHANNEL_INACTIVE.name


def test_checkout_create_with_inactive_default_channel(
    api_client, stock, graphql_address_data, channel_USD
):
    channel_USD.is_active = False
    channel_USD.save()

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
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
        content = get_graphql_content(response)["data"]["checkoutCreate"]

    assert content["created"] is True

    new_checkout = Checkout.objects.first()

    assert new_checkout.channel == channel_USD

    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_checkout_create_with_inactive_and_active_default_channel(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN
):
    channel_PLN.is_active = False
    channel_PLN.save()

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
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
        content = get_graphql_content(response)["data"]["checkoutCreate"]

    assert content["created"] is True

    new_checkout = Checkout.objects.first()

    assert new_checkout.channel == channel_USD

    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_checkout_create_with_inactive_and_two_active_default_channel(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN, other_channel_USD
):
    channel_USD.is_active = False
    channel_USD.save()

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

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["checkoutErrors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.MISSING_CHANNEL_SLUG.name


def test_checkout_create_with_many_active_default_channel(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN
):
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

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["checkoutErrors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.MISSING_CHANNEL_SLUG.name


def test_checkout_create_with_many_inactive_default_channel(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN
):
    channel_USD.is_active = False
    channel_USD.save()
    channel_PLN.is_active = False
    channel_PLN.save()
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

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["checkoutErrors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.MISSING_CHANNEL_SLUG.name


def test_checkout_create_with_multiple_channel_without_channel_slug(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN
):
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

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["checkoutErrors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.MISSING_CHANNEL_SLUG.name


def test_checkout_create_with_multiple_channel_with_channel_slug(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    content = get_graphql_content(response)["data"]["checkoutCreate"]

    assert content["created"] is True

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    assert new_checkout.channel == channel_USD
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 1


def test_checkout_create_with_existing_checkout_in_other_channel(
    user_api_client, stock, graphql_address_data, channel_USD, user_checkout_PLN
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    old_checkout = Checkout.objects.first()

    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    content = get_graphql_content(response)["data"]["checkoutCreate"]
    assert content["created"] is True

    checkout_data = content["checkout"]
    assert checkout_data["token"] != str(old_checkout.token)


def test_checkout_create_with_inactive_channel_slug(
    api_client, stock, graphql_address_data, channel_USD
):
    channel = channel_USD
    channel.is_active = False
    channel.save()
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["checkoutErrors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.CHANNEL_INACTIVE.name


def test_checkout_create(api_client, stock, graphql_address_data, channel_USD):
    """Create checkout object using GraphQL API."""
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
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


def test_checkout_create_with_invalid_channel_slug(
    api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    invalid_slug = "invalid-slug"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": invalid_slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]
    error = content["checkoutErrors"][0]

    assert error["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert error["field"] == "channel"


def test_checkout_create_multiple_warehouse(
    api_client, variant_with_many_stocks, graphql_address_data, channel_USD
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
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


def test_checkout_create_with_null_as_addresses(api_client, stock, channel_USD):
    """Create checkout object using GraphQL API."""
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
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
    api_client, variant_without_inventory_tracking, channel_USD
):
    """Create checkout object using GraphQL API."""
    variant = variant_without_inventory_tracking
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
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
    channel_USD,
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
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]
    assert content["checkoutErrors"]
    assert content["checkoutErrors"] == [
        {
            "field": "quantity",
            "message": expected_error_message,
            "code": error_code.name,
            "variants": None,
        }
    ]


def test_checkout_create_reuse_checkout(checkout, user_api_client, stock):
    # assign user to the checkout
    checkout.user = user_api_client.user
    checkout.save()
    variant = stock.product_variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "channel": checkout.channel.slug,
        },
    }
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


def test_checkout_create_required_email(api_client, stock, channel_USD):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "",
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)

    errors = content["data"]["checkoutCreate"]["checkoutErrors"]
    assert errors
    assert errors[0]["field"] == "email"
    assert errors[0]["message"] == "This field cannot be blank."

    checkout_errors = content["data"]["checkoutCreate"]["checkoutErrors"]
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name


def test_checkout_create_required_country_shipping_address(
    api_client, stock, graphql_address_data, channel_USD
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
            "channel": channel_USD.slug,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)

    checkout_errors = content["data"]["checkoutCreate"]["checkoutErrors"]
    assert checkout_errors[0]["field"] == "country"
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name


def test_checkout_create_required_country_billing_address(
    api_client, stock, graphql_address_data, channel_USD
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
            "channel": channel_USD.slug,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)

    checkout_errors = content["data"]["checkoutCreate"]["checkoutErrors"]
    assert checkout_errors[0]["field"] == "country"
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name


def test_checkout_create_default_email_for_logged_in_customer(
    user_api_client, stock, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "channel": channel_USD.slug,
        }
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    customer = user_api_client.user
    content = get_graphql_content(response)
    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["data"]["checkoutCreate"]["checkout"]
    assert checkout_data["email"] == str(customer.email)
    assert new_checkout.user.id == customer.id
    assert new_checkout.email == customer.email


def test_checkout_create_logged_in_customer(user_api_client, stock, channel_USD):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
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


def test_checkout_create_logged_in_customer_custom_email(
    user_api_client, stock, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    customer = user_api_client.user
    custom_email = "custom@example.com"
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
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
    user_api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    billing_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
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
    user_api_client, variant_with_many_stocks, graphql_address_data, channel_USD
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
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["checkoutErrors"][0]["message"] == (
        "Could not add item Test product (SKU_A). Only 7 remaining in stock."
    )
    assert data["checkoutErrors"][0]["field"] == "quantity"


@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_create_sets_country_from_shipping_address_country(
    user_api_client,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
    channel_USD,
):
    variant = variant_with_many_stocks_different_shipping_zones
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = 10001
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["created"] is True
    checkout = Checkout.objects.first()
    assert checkout.country == "US"


@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_create_check_lines_quantity_for_zone_insufficient_stocks(
    user_api_client,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
    channel_USD,
):
    """Check if insufficient stock exception will be raised.
    If item from checkout will not have enough quantity in correct shipping zone for
    shipping address INSUFICIENT_STOCK checkout error should be raised."""
    variant = variant_with_many_stocks_different_shipping_zones
    Stock.objects.filter(
        warehouse__shipping_zones__countries__contains="US", product_variant=variant
    ).update(quantity=0)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = 10001
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert not data["checkout"]
    errors = data["checkoutErrors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


def test_checkout_create_check_lines_quantity(
    user_api_client, stock, graphql_address_data, channel_USD
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
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["checkoutErrors"][0]["message"] == (
        "Could not add item Test product (SKU_A). Only 15 remaining in stock."
    )
    assert data["checkoutErrors"][0]["field"] == "quantity"


def test_checkout_create_unavailable_for_purchase_product(
    user_api_client, stock, graphql_address_data, channel_USD
):
    # given
    variant = stock.product_variant
    product = variant.product

    product.channel_listings.update(available_for_purchase=None)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 10, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]

    errors = data["checkoutErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name
    assert errors[0]["variants"] == [variant_id]


def test_checkout_create_available_for_purchase_from_tomorrow_product(
    user_api_client, stock, graphql_address_data, channel_USD
):
    # given
    variant = stock.product_variant
    product = variant.product

    product.channel_listings.update(
        available_for_purchase=datetime.date.today() + datetime.timedelta(days=1)
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 10, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]

    errors = data["checkoutErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name
    assert errors[0]["variants"] == [variant_id]


@pytest.fixture
def expected_dummy_gateway():
    return {
        "id": "mirumee.payments.dummy",
        "name": "Dummy",
        "config": [{"field": "store_customer_card", "value": "false"}],
        "currencies": ["USD", "PLN"],
    }


GET_CHECKOUT_PAYMENTS_QUERY = """
query getCheckoutPayments($token: UUID!) {
    checkout(token: $token) {
        availablePaymentGateways {
            id
            name
            config {
                field
                value
            }
            currencies
        }
    }
}
"""


def test_checkout_available_payment_gateways(
    api_client,
    checkout_with_item,
    expected_dummy_gateway,
):
    query = GET_CHECKOUT_PAYMENTS_QUERY
    variables = {"token": str(checkout_with_item.token)}
    response = api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["availablePaymentGateways"] == [
        expected_dummy_gateway,
    ]


def test_checkout_available_payment_gateways_currency_specified_USD(
    api_client,
    checkout_with_item,
    expected_dummy_gateway,
    sample_gateway,
):
    checkout_with_item.currency = "USD"
    checkout_with_item.save(update_fields=["currency"])

    query = GET_CHECKOUT_PAYMENTS_QUERY

    variables = {"token": str(checkout_with_item.token)}
    response = api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert {gateway["id"] for gateway in data["availablePaymentGateways"]} == {
        expected_dummy_gateway["id"],
        ActiveDummyPaymentGateway.PLUGIN_ID,
    }


def test_checkout_available_payment_gateways_currency_specified_EUR(
    api_client, checkout_with_item, expected_dummy_gateway, sample_gateway
):
    checkout_with_item.currency = "EUR"
    checkout_with_item.save(update_fields=["currency"])

    query = GET_CHECKOUT_PAYMENTS_QUERY

    variables = {"token": str(checkout_with_item.token)}
    response = api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert (
        data["availablePaymentGateways"][0]["id"] == ActiveDummyPaymentGateway.PLUGIN_ID
    )


GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS = """
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


def test_checkout_available_shipping_methods(
    api_client, checkout_with_item, address, shipping_zone
):
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    shipping_method = shipping_zone.shipping_methods.first()
    assert data["availableShippingMethods"][0]["name"] == shipping_method.name


def test_checkout_available_shipping_methods_excluded_zip_codes(
    api_client, checkout_with_item, address, shipping_zone
):
    address.country = Country("GB")
    address.postal_code = "BH16 7HF"
    address.save()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_method.zip_code_rules.create(start="BH16 7HA", end="BH16 7HG")

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["availableShippingMethods"] == []


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
    shipping_price = shipping_method.channel_listings.get(
        channel_id=checkout_with_item.channel_id
    ).price
    taxed_price = TaxedMoney(net=Money(10, "USD"), gross=Money(13, "USD"))
    apply_taxes_to_shipping_mock = mock.Mock(return_value=taxed_price)
    monkeypatch.setattr(
        PluginsManager, "apply_taxes_to_shipping", apply_taxes_to_shipping_mock
    )
    site_settings.display_gross_prices = display_gross_prices
    site_settings.save()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS

    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    apply_taxes_to_shipping_mock.assert_called_once_with(shipping_price, mock.ANY)
    assert data["availableShippingMethods"] == [
        {"name": "DHL", "price": {"amount": expected_price}}
    ]


def test_checkout_no_available_shipping_methods_without_address(
    api_client, checkout_with_item
):
    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableShippingMethods"] == []


def test_checkout_no_available_shipping_methods_without_lines(api_client, checkout):
    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS

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
            checkoutErrors {
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
    assert line.quantity == 3
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 1}],
        "channelSlug": checkout.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["checkoutErrors"]
    checkout.refresh_from_db()
    line = checkout.lines.latest("pk")
    assert line.variant == variant
    assert line.quantity == 1

    lines = fetch_checkout_lines(checkout)
    mocked_update_shipping_method.assert_called_once_with(checkout, lines, mock.ANY)


def test_checkout_lines_add_with_unpublished_product(
    user_api_client, checkout_with_item, stock, channel_USD
):
    variant = stock.product_variant
    product = variant.product
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_with_item.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 1}],
        "channelSlug": checkout_with_item.channel.slug,
    }

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)

    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesAdd"]["checkoutErrors"][0]
    assert error["code"] == CheckoutErrorCode.PRODUCT_NOT_PUBLISHED.name


def test_checkout_lines_add_with_unavailable_for_purchase_product(
    user_api_client, checkout_with_item, stock
):
    # given
    variant = stock.product_variant
    product = stock.product_variant.product
    product.channel_listings.update(available_for_purchase=None)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_with_item.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesAdd"]["checkoutErrors"][0]
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
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_with_item.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesAdd"]["checkoutErrors"][0]
    assert error["field"] == "lines"
    assert error["code"] == CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name
    assert error["variants"] == [variant_id]


def test_checkout_lines_add_too_many(user_api_client, checkout_with_item, stock):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_with_item.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 51}],
        "channelSlug": checkout_with_item.channel.slug,
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)["data"]["checkoutLinesAdd"]

    assert content["checkoutErrors"]
    assert content["checkoutErrors"] == [
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
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesAdd"]
    assert not data["checkoutErrors"]
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
    assert not data["checkoutErrors"]
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
    assert data["checkoutErrors"][0]["message"] == (
        "Could not add item Test product (SKU_A). Only 15 remaining in stock."
    )
    assert data["checkoutErrors"][0]["field"] == "quantity"


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
    assert data["checkoutErrors"][0]["message"] == error_msg % [invalid_variant_id]
    assert data["checkoutErrors"][0]["field"] == "variantId"


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
            checkoutErrors {
                field
                code
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
    assert not data["checkoutErrors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.variant == variant
    assert line.quantity == 1

    lines = fetch_checkout_lines(checkout)
    mocked_update_shipping_method.assert_called_once_with(checkout, lines, mock.ANY)


def test_create_checkout_with_unpublished_product(
    user_api_client, checkout_with_item, stock, channel_USD
):
    variant = stock.product_variant
    product = variant.product
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    query = """
            mutation CreateCheckout($checkoutInput: CheckoutCreateInput!) {
              checkoutCreate(input: $checkoutInput) {
                checkoutErrors {
                  code
                  message
                }
                checkout {
                  id
                }
              }
            }
        """
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "email": "test@example.com",
            "lines": [{"variantId": variant_id, "quantity": 1}],
        }
    }
    response = get_graphql_content(user_api_client.post_graphql(query, variables))
    error = response["data"]["checkoutCreate"]["checkoutErrors"][0]
    assert error["code"] == CheckoutErrorCode.PRODUCT_NOT_PUBLISHED.name


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
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)

    content = get_graphql_content(response)
    error = content["data"]["checkoutLinesUpdate"]["checkoutErrors"][0]
    assert error["code"] == CheckoutErrorCode.PRODUCT_NOT_PUBLISHED.name


def test_checkout_lines_update_invalid_checkout_id(user_api_client):
    variables = {"checkoutId": "test", "lines": []}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutLinesUpdate"]
    assert data["checkoutErrors"][0]["field"] == "checkoutId"


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
    assert data["checkoutErrors"][0]["message"] == (
        "Could not add item Test product (123). Only 10 remaining in stock."
    )
    assert data["checkoutErrors"][0]["field"] == "quantity"


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
    assert not data["checkoutErrors"]
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
    lines = fetch_checkout_lines(checkout)
    mocked_update_shipping_method.assert_called_once_with(checkout, lines, mock.ANY)


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
    assert not data["checkoutErrors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 0
    lines = fetch_checkout_lines(checkout)
    mocked_update_shipping_method.assert_called_once_with(checkout, lines, mock.ANY)


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
    lines = fetch_checkout_lines(checkout)
    mocked_update_shipping_method.assert_called_once_with(checkout, lines, mock.ANY)


@mock.patch(
    "saleor.graphql.checkout.mutations.update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_changes_checkout_country(
    mocked_update_shipping_method,
    user_api_client,
    channel_USD,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
):
    variant = variant_with_many_stocks_different_shipping_zones
    checkout = Checkout.objects.create(channel=channel_USD)
    checkout.set_country("PL", commit=True)
    add_variant_to_checkout(checkout, variant, 1)
    assert checkout.shipping_address is None
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
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
    lines = fetch_checkout_lines(checkout)
    mocked_update_shipping_method.assert_called_once_with(checkout, lines, mock.ANY)
    assert checkout.country == shipping_address["country"]


@mock.patch(
    "saleor.graphql.checkout.mutations.update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_insufficient_stocks(
    mocked_update_shipping_method,
    channel_USD,
    user_api_client,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
):
    variant = variant_with_many_stocks_different_shipping_zones
    checkout = Checkout.objects.create(channel=channel_USD)
    checkout.set_country("PL", commit=True)
    add_variant_to_checkout(checkout, variant, 1)
    Stock.objects.filter(
        warehouse__shipping_zones__countries__contains="US", product_variant=variant
    ).update(quantity=0)
    assert checkout.shipping_address is None
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {"checkoutId": checkout_id, "shippingAddress": shipping_address}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    errors = data["checkoutErrors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


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


TRANSACTION_CONFIRM_GATEWAY_RESPONSE = GatewayResponse(
    is_success=False,
    action_required=False,
    kind=TransactionKind.CONFIRM,
    amount=Decimal(3.0),
    currency="usd",
    transaction_id="1234",
    error=None,
)


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
    variables = {
        "token": str(checkout_with_item.token),
        "channel": checkout_with_item.channel.slug,
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["token"] == str(checkout_with_item.token)
    assert len(data["lines"]) == checkout_with_item.lines.count()


QUERY_CHECKOUT_USER_ID = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           user {
               id
           }
        }
    }
    """


def test_anonymous_client_cant_fetch_checkout_user(api_client, checkout):
    query = QUERY_CHECKOUT_USER_ID
    variables = {"token": str(checkout.token)}
    response = api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_authorized_access_to_checkout_user_as_customer(
    user_api_client,
    checkout,
    customer_user,
):
    query = QUERY_CHECKOUT_USER_ID
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
    query = QUERY_CHECKOUT_USER_ID
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
    staff_api_client,
    checkout,
    customer_user,
    permission_manage_checkouts,
):
    query = QUERY_CHECKOUT_USER_ID

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
    variables = {"token": str(checkout.token), "channel": checkout.channel.slug}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


QUERY_CHECKOUT_CHANNEL_SLUG = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
            token
            channel {
                slug
            }
        }
    }
"""


def test_query_anonymous_customer_channel_checkout_as_anonymous_customer(
    api_client, checkout
):
    query = QUERY_CHECKOUT_CHANNEL_SLUG
    checkout_token = str(checkout.token)
    channel_slug = checkout.channel.slug
    variables = {"token": checkout_token}

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    assert content["data"]["checkout"]["token"] == checkout_token
    assert content["data"]["checkout"]["channel"]["slug"] == channel_slug


def test_query_anonymous_customer_channel_checkout_as_customer(
    user_api_client, checkout
):
    query = QUERY_CHECKOUT_CHANNEL_SLUG
    checkout_token = str(checkout.token)
    channel_slug = checkout.channel.slug
    variables = {
        "token": checkout_token,
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    assert content["data"]["checkout"]["token"] == checkout_token
    assert content["data"]["checkout"]["channel"]["slug"] == channel_slug


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


def test_fetch_checkout_invalid_token(user_api_client, channel_USD):
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
    lines = fetch_checkout_lines(checkout_with_item)
    manager = get_plugins_manager()
    total = calculations.checkout_total(
        manager=manager,
        checkout=checkout_with_item,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    assert data["totalPrice"]["gross"]["amount"] == (total.gross.amount)
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout=checkout_with_item,
        lines=lines,
        address=checkout_with_item.shipping_address,
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

    lines = fetch_checkout_lines(checkout)
    mock_clean_shipping.assert_called_once_with(
        checkout=checkout, lines=lines, method=shipping_method, discounts=ANY
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


@patch("saleor.shipping.models.check_shipping_method_for_zip_code")
def test_checkout_shipping_method_update_excluded_zip_code(
    mock_check_zip_code, staff_api_client, shipping_method, checkout_with_item, address
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD
    mock_check_zip_code.return_value = True

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"checkoutId": checkout_id, "shippingMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    assert data["errors"] == [
        {
            "field": "shippingMethod",
            "message": "This shipping method is not applicable.",
        }
    ]
    assert checkout.shipping_method is None
    assert (
        mock_check_zip_code.call_count == shipping_models.ShippingMethod.objects.count()
    )


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


def test_query_with_channel(
    checkouts_list, staff_api_client, permission_manage_checkouts, channel_USD
):
    query = """
    query CheckoutsQuery($channel: String) {
        checkouts(first: 20, channel: $channel) {
            edges {
                node {
                    token
                }
            }
        }
    }
    """
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_checkouts]
    )
    content = get_graphql_content(response)
    assert len(content["data"]["checkouts"]["edges"]) == 3


def test_query_without_channel(
    checkouts_list, staff_api_client, permission_manage_checkouts
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
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_checkouts]
    )
    content = get_graphql_content(response)
    assert len(content["data"]["checkouts"]["edges"]) == 5


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

    lines = fetch_checkout_lines(checkout_with_item)
    manager = get_plugins_manager()
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    # Shouldn't raise any errors

    clean_checkout_shipping(checkout, lines, None, CheckoutErrorCode)
    clean_checkout_payment(
        manager, checkout, lines, None, CheckoutErrorCode, last_payment=payment
    )


def test_clean_checkout_no_shipping_method(checkout_with_item, address):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save()

    lines = fetch_checkout_lines(checkout)
    with pytest.raises(ValidationError) as e:
        clean_checkout_shipping(checkout, lines, None, CheckoutErrorCode)

    msg = "Shipping method is not set"
    assert e.value.error_dict["shipping_method"][0].message == msg


def test_clean_checkout_no_shipping_address(checkout_with_item, shipping_method):
    checkout = checkout_with_item
    checkout.shipping_method = shipping_method
    checkout.save()

    lines = fetch_checkout_lines(checkout)
    with pytest.raises(ValidationError) as e:
        clean_checkout_shipping(checkout, lines, None, CheckoutErrorCode)
    msg = "Shipping address is not set"
    assert e.value.error_dict["shipping_address"][0].message == msg


def test_clean_checkout_invalid_shipping_method(
    checkout_with_item, address, shipping_zone_without_countries
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    shipping_method = shipping_zone_without_countries.shipping_methods.first()
    checkout.shipping_method = shipping_method
    checkout.save()

    lines = fetch_checkout_lines(checkout)
    with pytest.raises(ValidationError) as e:
        clean_checkout_shipping(checkout, lines, None, CheckoutErrorCode)

    msg = "Shipping method is not valid for your shipping address"

    assert e.value.error_dict["shipping_method"][0].message == msg


def test_clean_checkout_no_billing_address(
    checkout_with_item, address, shipping_method
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()
    payment = checkout.get_last_active_payment()
    lines = fetch_checkout_lines(checkout)
    manager = get_plugins_manager()

    with pytest.raises(ValidationError) as e:
        clean_checkout_payment(
            manager, checkout, lines, None, CheckoutErrorCode, last_payment=payment
        )
    msg = "Billing address is not set"
    assert e.value.error_dict["billing_address"][0].message == msg


def test_clean_checkout_no_payment(checkout_with_item, shipping_method, address):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()
    payment = checkout.get_last_active_payment()
    lines = fetch_checkout_lines(checkout)
    manager = get_plugins_manager()

    with pytest.raises(ValidationError) as e:
        clean_checkout_payment(
            manager, checkout, lines, None, CheckoutErrorCode, last_payment=payment
        )

    msg = "Provided payment methods can not cover the checkout's total amount"
    assert e.value.error_list[0].message == msg


def test_get_variant_data_from_checkout_line_variant_hidden_in_listings(
    checkout_with_item, api_client
):
    # given
    query = """
        query getCheckout($token: UUID!){
            checkout(token: $token){
                id
                lines{
                    id
                    variant{
                        id
                    }
                }
            }
        }
    """
    checkout = checkout_with_item
    variant = checkout.lines.get().variant
    variant.product.channel_listings.update(visible_in_listings=False)
    variables = {"token": checkout.token}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["lines"][0]["variant"]["id"]
