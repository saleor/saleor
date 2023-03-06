import datetime
import warnings
from unittest import mock

import graphene
import pytest
import pytz
from django.test import override_settings
from django.utils import timezone

from .....account.models import Address
from .....channel.utils import DEPRECATION_WARNING_MESSAGE
from .....checkout import AddressType
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_lines
from .....checkout.models import Checkout
from .....checkout.utils import calculate_checkout_quantity
from .....product.models import ProductChannelListing
from .....warehouse.models import Reservation, Stock
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_CHECKOUT_CREATE = """
    mutation createCheckout($checkoutInput: CheckoutCreateInput!) {
      checkoutCreate(input: $checkoutInput) {
        checkout {
          id
          token
          email
          quantity
          lines {
            quantity
          }
        }
        errors {
          field
          message
          code
          variants
          addressType
        }
      }
    }
"""


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_checkout_create_triggers_webhooks(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    user_api_client,
    stock,
    graphql_address_data,
    settings,
    channel_USD,
):
    """Create checkout object using GraphQL API."""
    mocked_get_webhooks_for_event.return_value = [any_webhook]
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
    quantity = 1
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": quantity, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
        get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    lines, _ = fetch_checkout_lines(new_checkout)
    assert new_checkout.channel == channel_USD
    assert calculate_checkout_quantity(lines) == quantity

    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_checkout_create_with_variant_without_sku(
    api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant.sku = None
    variant.save()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    quantity = 1
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": quantity, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    lines, _ = fetch_checkout_lines(new_checkout)
    assert new_checkout.channel == channel_USD
    assert calculate_checkout_quantity(lines) == quantity
    assert lines[0].variant.sku is None


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

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.CHANNEL_INACTIVE.name


def test_checkout_create_with_zero_quantity(
    api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 0, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "quantity"
    assert error["code"] == CheckoutErrorCode.ZERO_QUANTITY.name


def test_checkout_create_with_unavailable_variant(
    api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant.channel_listings.filter(channel=channel_USD).update(price_amount=None)
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

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "lines"
    assert error["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert error["variants"] == [variant_id]


def test_checkout_create_with_malicious_variant_id(
    api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant.channel_listings.filter(channel=channel_USD).update(price_amount=None)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variant_id = (
        "UHJvZHVjdFZhcmlhbnQ6NDkxMyd8fERCTVNfUElQRS5SRUNFSVZFX01FU1N"
        "BR0UoQ0hSKDk4KXx8Q0hSKDk4KXx8Q0hSKDk4KSwxNSl8fCc="
    )
    # This string translates to
    # ProductVariant:4913'||DBMS_PIPE.RECEIVE_MESSAGE(CHR(98)||CHR(98)||CHR(98),15)||'

    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "variantId"
    assert error["code"] == "GRAPHQL_ERROR"


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
        get_graphql_content(response)["data"]["checkoutCreate"]

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
        get_graphql_content(response)["data"]["checkoutCreate"]

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

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

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

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

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

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

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

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

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

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

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
    assert not Reservation.objects.exists()


def test_checkout_create_with_custom_price(
    app_api_client,
    stock,
    graphql_address_data,
    channel_USD,
    permission_handle_checkouts,
):
    """Ensure that app with handle checkouts permission can set custom price."""
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    price = 12.25
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id, "price": price}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE, variables, permissions=[permission_handle_checkouts]
    )
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 1
    assert checkout_line.price_override == price


def test_checkout_create_with_metadata_in_line(
    api_client, stock, graphql_address_data, channel_USD
):
    """Ensure that app with handle checkouts permission can set custom price."""
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    metadata_key = "md key"
    metadata_value = "md value"
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [
                {
                    "quantity": 1,
                    "variantId": variant_id,
                    "metadata": [{"key": metadata_key, "value": metadata_value}],
                }
            ],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 1
    assert checkout_line.metadata == {metadata_key: metadata_value}


def test_checkout_create_with_custom_price_duplicated_items(
    app_api_client,
    stock,
    graphql_address_data,
    channel_USD,
    permission_handle_checkouts,
):
    """Ensure that when the same item with a custom price is provided multiple times,
    the price from the last occurrence will be set."""
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    price_1 = 12.25
    price_2 = 20.25
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [
                {"quantity": 1, "variantId": variant_id, "price": price_1},
                {"quantity": 1, "variantId": variant_id, "price": price_2},
            ],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE, variables, permissions=[permission_handle_checkouts]
    )
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 2
    assert checkout_line.price_override == price_2


def test_checkout_create_with_force_new_line(
    app_api_client,
    stock,
    graphql_address_data,
    channel_USD,
    permission_handle_checkouts,
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data

    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [
                {"quantity": 1, "variantId": variant_id},
                {"quantity": 1, "variantId": variant_id, "forceNewLine": True},
            ],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE,
        variables,
        permissions=[permission_handle_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    new_checkout_lines = new_checkout.lines.all()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert len(new_checkout_lines) == 2

    for line in new_checkout_lines:
        assert line.variant == variant
        assert line.quantity == 1


def test_checkout_create_with_custom_price_by_app_no_perm(
    app_api_client, stock, graphql_address_data, channel_USD
):
    """Ensure that app without handle checkouts permission cannot set custom price."""
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    price = 12.25
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id, "price": price}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = app_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    assert_no_permission(response)


def test_checkout_create_with_custom_price_by_staff_with_handle_checkouts(
    staff_api_client,
    stock,
    graphql_address_data,
    channel_USD,
    permission_handle_checkouts,
):
    """Ensure that staff with handle checkouts permission cannot set custom price."""
    staff_api_client.user.user_permissions.add(permission_handle_checkouts)
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    price = 12.25
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id, "price": price}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = staff_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    assert_no_permission(response)


def test_checkout_create_no_email(api_client, stock, graphql_address_data, channel_USD):
    """Create checkout object using GraphQL API."""
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 1
    assert new_checkout.shipping_address is not None
    assert new_checkout.email is None
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


def test_checkout_create_stock_only_in_cc_warehouse(
    api_client, stock, graphql_address_data, channel_USD, warehouse_for_cc
):
    """Create checkout object using GraphQL API."""
    # given
    variant = stock.product_variant
    variant.stocks.all().delete()

    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=10
    )

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

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    content = get_graphql_content(response)["data"]["checkoutCreate"]

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
    assert not Reservation.objects.exists()


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
    error = content["errors"][0]

    assert error["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert error["field"] == "channel"


def test_checkout_create_no_channel_shipping_zones(
    api_client, stock, graphql_address_data, channel_USD
):
    """Create checkout object using GraphQL API."""
    channel_USD.shipping_zones.clear()
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

    new_checkout = Checkout.objects.first()
    assert new_checkout is None
    errors = content["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


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

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 4


def test_checkout_create_with_reservation(
    site_settings_with_reservations,
    api_client,
    variant_with_many_stocks,
    graphql_address_data,
    channel_USD,
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
    get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line
    reservation = checkout_line.reservations.first()
    assert reservation
    assert reservation.checkout_line == checkout_line
    assert reservation.quantity_reserved == checkout_line.quantity
    assert reservation.reserved_until > timezone.now()


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
            "Cannot add more than 50 times this item: SKU_A.",
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
    assert content["errors"]
    assert content["errors"] == [
        {
            "field": "quantity",
            "message": expected_error_message,
            "code": error_code.name,
            "variants": None,
            "addressType": None,
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

    checkout_data = content["checkout"]
    assert checkout_data["token"] != str(checkout.token)

    assert len(checkout_data["lines"]) == 1


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

    checkout_errors = content["data"]["checkoutCreate"]["errors"]
    assert checkout_errors[0]["field"] == "country"
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert checkout_errors[0]["addressType"] == AddressType.SHIPPING.upper()


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

    checkout_errors = content["data"]["checkoutCreate"]["errors"]
    assert checkout_errors[0]["field"] == "country"
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert checkout_errors[0]["addressType"] == AddressType.BILLING.upper()


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
    assert new_checkout.shipping_address is None
    assert new_checkout.billing_address is None
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
    assert data["errors"][0]["message"] == (
        "Could not add items SKU_A. Only 7 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


def test_checkout_create_when_all_stocks_exceeded(
    user_api_client, variant_with_many_stocks, graphql_address_data, channel_USD
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 16, "variantId": variant_id}],
            "email": "test@example.com",
            "shippingAddress": graphql_address_data,
            "channel": channel_USD.slug,
        }
    }

    # make stocks exceeded and assert
    variant.stocks.update(quantity=-99)
    for stock in variant.stocks.all():
        assert stock.quantity == -99

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["errors"][0]["message"] == (
        "Could not add items SKU_A. Only 0 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


def test_checkout_create_when_one_stock_exceeded(
    user_api_client, variant_with_many_stocks, graphql_address_data, channel_USD
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 16, "variantId": variant_id}],
            "email": "test@example.com",
            "shippingAddress": graphql_address_data,
            "channel": channel_USD.slug,
        }
    }

    # make first stock exceeded
    stock = variant.stocks.first()
    stock.quantity = -1
    stock.save()

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["errors"][0]["message"] == (
        "Could not add items SKU_A. Only 2 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


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
    content["data"]["checkoutCreate"]
    checkout = Checkout.objects.first()
    assert checkout.country == "US"


def test_checkout_create_sets_country_when_no_shipping_address_is_given(
    api_client, variant_with_many_stocks_different_shipping_zones, channel_USD
):
    variant = variant_with_many_stocks_different_shipping_zones
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
        }
    }
    assert not Checkout.objects.exists()

    # should set channel's default_country
    api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    checkout = Checkout.objects.first()
    assert checkout.country == channel_USD.default_country


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
    errors = data["errors"]
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
    assert data["errors"][0]["message"] == (
        "Could not add items SKU_A. Only 15 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


@pytest.mark.parametrize("is_preorder", [True, False])
def test_checkout_create_check_lines_quantity_when_limit_per_variant_is_set_raise_err(
    user_api_client, stock, graphql_address_data, channel_USD, is_preorder
):
    limit_per_customer = 5
    variant = stock.product_variant
    variant.quantity_limit_per_customer = limit_per_customer
    variant.is_preorder = is_preorder
    variant.preorder_end_date = timezone.now() + datetime.timedelta(days=1)
    variant.save(
        update_fields=[
            "quantity_limit_per_customer",
            "is_preorder",
            "preorder_end_date",
        ]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 6, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]

    assert data["errors"][0]["message"] == (
        f"Cannot add more than {limit_per_customer} times this item: {variant}."
    )
    assert data["errors"][0]["field"] == "quantity"


@pytest.mark.parametrize("is_preorder", [True, False])
def test_checkout_create_check_lines_quantity_limit_when_variant_in_multiple_lines(
    user_api_client, stock, graphql_address_data, channel_USD, is_preorder
):
    limit_per_customer = 5
    variant = stock.product_variant
    variant.quantity_limit_per_customer = limit_per_customer
    variant.is_preorder = is_preorder
    variant.preorder_end_date = timezone.now() + datetime.timedelta(days=1)
    variant.save(
        update_fields=[
            "quantity_limit_per_customer",
            "is_preorder",
            "preorder_end_date",
        ]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "lines": [
                {"quantity": 4, "variantId": variant_id},
                {"quantity": 3, "variantId": variant_id, "forceNewLine": True},
            ],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]

    assert data["errors"][0]["message"] == (
        f"Cannot add more than {limit_per_customer} times this item: {variant}."
    )
    assert data["errors"][0]["field"] == "quantity"


@pytest.mark.parametrize("is_preorder", [True, False])
def test_checkout_create_check_lines_quantity_respects_site_settings(
    user_api_client,
    stock,
    graphql_address_data,
    channel_USD,
    site_settings,
    is_preorder,
):
    global_limit = 5
    variant = stock.product_variant
    variant.is_preorder = is_preorder
    variant.preorder_end_date = timezone.now() + datetime.timedelta(days=1)
    variant.save(
        update_fields=[
            "is_preorder",
            "preorder_end_date",
        ]
    )
    site_settings.limit_quantity_per_checkout = global_limit
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 6, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]

    assert data["errors"][0]["message"] == (
        f"Cannot add more than {global_limit} times this item: {variant}."
    )
    assert data["errors"][0]["field"] == "quantity"


@pytest.mark.parametrize("is_preorder", [True, False])
def test_checkout_create_check_lines_quantity_site_settings_no_limit(
    user_api_client,
    stock,
    graphql_address_data,
    channel_USD,
    site_settings,
    is_preorder,
):
    variant = stock.product_variant
    variant.is_preorder = is_preorder
    variant.preorder_end_date = timezone.now() + datetime.timedelta(days=1)
    variant.save(
        update_fields=[
            "is_preorder",
            "preorder_end_date",
        ]
    )
    site_settings.limit_quantity_per_checkout = None
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 15, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]

    assert not data["errors"]
    assert Checkout.objects.first()


def test_checkout_create_check_lines_quantity_against_reservations(
    site_settings_with_reservations,
    user_api_client,
    stock,
    graphql_address_data,
    channel_USD,
    checkout,
):
    variant = stock.product_variant
    checkout_line = checkout.lines.create(
        variant=variant,
        quantity=3,
    )
    Reservation.objects.create(
        checkout_line=checkout_line,
        stock=stock,
        quantity_reserved=3,
        reserved_until=timezone.now() + datetime.timedelta(minutes=5),
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 15, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert Checkout.objects.count() == 1
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["errors"][0]["message"] == (
        "Could not add items SKU_A. Only 12 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


def test_checkout_create_unavailable_for_purchase_product(
    user_api_client, stock, graphql_address_data, channel_USD
):
    # given
    variant = stock.product_variant
    product = variant.product

    product.channel_listings.update(available_for_purchase_at=None)

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

    errors = data["errors"]
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
        available_for_purchase_at=datetime.datetime.now(pytz.UTC)
        + datetime.timedelta(days=1)
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

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name
    assert errors[0]["variants"] == [variant_id]


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
                errors {
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
    error = response["data"]["checkoutCreate"]["errors"][0]
    assert error["code"] == CheckoutErrorCode.PRODUCT_NOT_PUBLISHED.name


@pytest.mark.parametrize(
    "address_data, address_input_name, address_db_field_name",
    [
        (
            {"country": "PL"},  # missing postalCode, streetAddress
            "shippingAddress",
            "shipping_address",
        ),
        (
            {"country": "PL", "postalCode": "53-601"},  # missing streetAddress
            "shippingAddress",
            "shipping_address",
        ),
        ({"country": "US"}, "shippingAddress", "shipping_address"),
        (
            {
                "country": "US",
                "city": "New York",
            },  # missing postalCode, streetAddress, countryArea
            "shippingAddress",
            "shipping_address",
        ),
        (
            {"country": "PL"},  # missing postalCode, streetAddress
            "billingAddress",
            "billing_address",
        ),
        (
            {"country": "PL", "postalCode": "53-601"},  # missing streetAddress
            "billingAddress",
            "billing_address",
        ),
        ({"country": "US"}, "shippingAddress", "shipping_address"),
        (
            {
                "country": "US",
                "city": "New York",
            },  # missing postalCode, streetAddress, countryArea
            "billingAddress",
            "billing_address",
        ),
    ],
)
def test_checkout_create_with_skip_required_doesnt_raise_error(
    address_data,
    address_input_name,
    address_db_field_name,
    api_client,
    stock,
    channel_USD,
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            address_input_name: address_data,
            "validationRules": {address_input_name: {"checkRequiredFields": False}},
            "channel": channel_USD.slug,
        }
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    data = get_graphql_content(response)["data"]["checkoutCreate"]
    created_checkout = Checkout.objects.first()

    assert not data["errors"]
    assert created_checkout
    assert getattr(created_checkout, address_db_field_name)


@pytest.mark.parametrize(
    "address_input_name",
    ["shippingAddress", "billingAddress"],
)
def test_checkout_create_with_skip_required_raises_validation_error(
    address_input_name, api_client, stock, channel_USD
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            address_input_name: {"country": "US", "postalCode": "XX-123"},
            "validationRules": {address_input_name: {"checkRequiredFields": False}},
            "channel": channel_USD.slug,
        }
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    created_checkout = Checkout.objects.first()
    data = get_graphql_content(response)["data"]["checkoutCreate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["field"] == "postalCode"
    assert created_checkout is None


@pytest.mark.parametrize(
    "address_input_name, address_db_field_name",
    [("shippingAddress", "shipping_address"), ("billingAddress", "billing_address")],
)
def test_checkout_create_with_skip_required_saves_address(
    address_input_name, address_db_field_name, api_client, stock, channel_USD
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            address_input_name: {"country": "PL", "postalCode": "53-601"},
            "validationRules": {address_input_name: {"checkRequiredFields": False}},
            "channel": channel_USD.slug,
        }
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    data = get_graphql_content(response)["data"]["checkoutCreate"]
    created_checkout = Checkout.objects.first()

    assert not data["errors"]
    assert created_checkout is not None
    assert getattr(created_checkout, address_db_field_name)
    assert getattr(created_checkout, address_db_field_name).country.code == "PL"
    assert getattr(created_checkout, address_db_field_name).postal_code == "53-601"


@pytest.mark.parametrize(
    "address_data, address_input_name, address_db_field_name",
    [
        (
            {
                "country": "PL",
                "city": "Wroclaw",
                "postalCode": "XYZ",
                "streetAddress1": "Teczowa 7",
            },  # incorrect postalCode
            "shippingAddress",
            "shipping_address",
        ),
        (
            {
                "country": "US",
                "city": "New York",
                "countryArea": "ABC",
                "streetAddress1": "New street",
                "postalCode": "53-601",
            },  # incorrect postalCode
            "shippingAddress",
            "shipping_address",
        ),
        (
            {
                "country": "PL",
                "city": "Wroclaw",
                "postalCode": "XYZ",
                "streetAddress1": "Teczowa 7",
            },  # incorrect postalCode
            "billingAddress",
            "billing_address",
        ),
        (
            {
                "country": "US",
                "city": "New York",
                "countryArea": "ABC",
                "streetAddress1": "New street",
                "postalCode": "53-601",
            },  # incorrect postalCode
            "billingAddress",
            "billing_address",
        ),
    ],
)
def test_checkout_create_with_skip_value_check_doesnt_raise_error(
    address_data,
    address_input_name,
    address_db_field_name,
    api_client,
    stock,
    channel_USD,
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            address_input_name: address_data,
            "validationRules": {address_input_name: {"checkFieldsFormat": False}},
            "channel": channel_USD.slug,
        }
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    data = get_graphql_content(response)["data"]["checkoutCreate"]
    created_checkout = Checkout.objects.first()

    assert not data["errors"]
    assert created_checkout
    assert getattr(created_checkout, address_db_field_name)


@pytest.mark.parametrize(
    "address_data, address_input_name",
    [
        (
            {
                "country": "PL",
                "city": "Wroclaw",
                "postalCode": "XYZ",
            },  # incorrect postalCode
            "shippingAddress",
        ),
        (
            {
                "country": "US",
                "city": "New York",
                "countryArea": "XYZ",
                "postalCode": "XYZ",
            },  # incorrect postalCode
            "shippingAddress",
        ),
        (
            {
                "country": "PL",
                "city": "Wroclaw",
                "postalCode": "XYZ",
            },  # incorrect postalCode
            "billingAddress",
        ),
        (
            {
                "country": "US",
                "city": "New York",
                "countryArea": "XYZ",
                "postalCode": "XYZ",
            },  # incorrect postalCode
            "billingAddress",
        ),
    ],
)
def test_checkout_create_with_skip_value_raises_required_fields_error(
    address_data, address_input_name, api_client, stock, channel_USD
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            address_input_name: address_data,
            "validationRules": {address_input_name: {"checkFieldsFormat": False}},
            "channel": channel_USD.slug,
        }
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    created_checkout = Checkout.objects.first()
    data = get_graphql_content(response)["data"]["checkoutCreate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "REQUIRED"
    assert data["errors"][0]["field"] == "streetAddress1"
    assert created_checkout is None


@pytest.mark.parametrize(
    "address_input_name, address_db_field_name",
    [("shippingAddress", "shipping_address"), ("billingAddress", "billing_address")],
)
def test_checkout_create_with_skip_value_check_saves_address(
    address_input_name, address_db_field_name, api_client, stock, channel_USD
):
    # given
    city = "Wroclaw"
    street_address = "Teczowa 7"
    postal_code = "XX-601"  # incorrect format for PL
    country_code = "PL"

    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            address_input_name: {
                "country": country_code,
                "city": city,
                "streetAddress1": street_address,
                "postalCode": postal_code,
            },
            "validationRules": {address_input_name: {"checkFieldsFormat": False}},
            "channel": channel_USD.slug,
        }
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    created_checkout = Checkout.objects.first()
    data = get_graphql_content(response)["data"]["checkoutCreate"]
    assert not data["errors"]

    assert created_checkout
    assert getattr(created_checkout, address_db_field_name)
    assert (
        getattr(created_checkout, address_db_field_name).street_address_1
        == street_address
    )
    assert getattr(created_checkout, address_db_field_name).city == city
    assert getattr(created_checkout, address_db_field_name).postal_code == postal_code
    assert getattr(created_checkout, address_db_field_name).country.code == country_code


[("shippingAddress", "shipping_address"), ("billingAddress", "billing_address")],


@pytest.mark.parametrize(
    "address_data, address_input_name, address_db_field_name",
    [
        (
            {
                "country": "PL",
                "postalCode": "XYZ",
            },  # incorrect postalCode, missing city, streetAddress
            "shippingAddress",
            "shipping_address",
        ),
        (
            {
                "country": "US",
                "countryArea": "DC",
                "postalCode": "XYZ",
            },  # incorrect postalCode, missing city
            "shippingAddress",
            "shipping_address",
        ),
        (
            {
                "country": "PL",
                "postalCode": "XYZ",
            },  # incorrect postalCode, missing city, streetAddress
            "billingAddress",
            "billing_address",
        ),
        (
            {
                "country": "US",
                "countryArea": "DC",
                "postalCode": "XYZ",
            },  # incorrect postalCode, missing city
            "billingAddress",
            "billing_address",
        ),
    ],
)
def test_checkout_create_with_skip_value_and_skip_required_fields(
    address_data,
    address_input_name,
    address_db_field_name,
    api_client,
    stock,
    channel_USD,
):
    # given
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            address_input_name: address_data,
            "validationRules": {
                address_input_name: {
                    "checkFieldsFormat": False,
                    "checkRequiredFields": False,
                }
            },
            "channel": channel_USD.slug,
        }
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    created_checkout = Checkout.objects.first()
    data = get_graphql_content(response)["data"]["checkoutCreate"]
    assert not data["errors"]
    assert getattr(created_checkout, address_db_field_name)


@pytest.mark.parametrize(
    "address_input_name, address_db_field_name",
    [("shippingAddress", "shipping_address"), ("billingAddress", "billing_address")],
)
def test_checkout_create_with_skip_value_and_skip_required_saves_address(
    address_input_name, address_db_field_name, api_client, stock, channel_USD
):
    # given
    city = "Wroclaw"
    postal_code = "XX-601"  # incorrect format for PL
    country_code = "PL"

    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            address_input_name: {
                "country": country_code,
                "city": city,
                "postalCode": postal_code,
            },
            "validationRules": {
                address_input_name: {
                    "checkFieldsFormat": False,
                    "checkRequiredFields": False,
                }
            },
            "channel": channel_USD.slug,
        }
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    created_checkout = Checkout.objects.first()
    data = get_graphql_content(response)["data"]["checkoutCreate"]
    assert not data["errors"]

    assert created_checkout
    assert getattr(created_checkout, address_db_field_name)
    assert getattr(created_checkout, address_db_field_name).country.code == country_code
    assert getattr(created_checkout, address_db_field_name).postal_code == postal_code
    assert getattr(created_checkout, address_db_field_name).city == city
    assert getattr(created_checkout, address_db_field_name).street_address_1 == ""


def test_checkout_create_with_shipping_address_disabled_fields_normalization(
    api_client, stock, channel_USD
):
    # given
    address_data = {
        "country": "US",
        "city": "Washington",
        "countryArea": "District of Columbia",
        "streetAddress1": "1600 Pennsylvania Avenue NW",
        "postalCode": "20500",
    }
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            "shippingAddress": address_data,
            "validationRules": {
                "shippingAddress": {"enableFieldsNormalization": False}
            },
            "channel": channel_USD.slug,
        }
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    data = get_graphql_content(response)["data"]["checkoutCreate"]
    assert not data["errors"]
    created_checkout = Checkout.objects.first()
    assert created_checkout
    shipping_address = created_checkout.shipping_address
    assert shipping_address
    assert shipping_address.city == address_data["city"]
    assert shipping_address.country_area == address_data["countryArea"]
    assert shipping_address.postal_code == address_data["postalCode"]
    assert shipping_address.street_address_1 == address_data["streetAddress1"]


def test_checkout_create_with_billing_address_disabled_fields_normalization(
    api_client, stock, channel_USD
):
    # given
    address_data = {
        "country": "US",
        "city": "Washington",
        "countryArea": "District of Columbia",
        "streetAddress1": "1600 Pennsylvania Avenue NW",
        "postalCode": "20500",
    }
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            "billingAddress": address_data,
            "validationRules": {"billingAddress": {"enableFieldsNormalization": False}},
            "channel": channel_USD.slug,
        }
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    data = get_graphql_content(response)["data"]["checkoutCreate"]
    assert not data["errors"]
    created_checkout = Checkout.objects.first()
    assert created_checkout
    billing_address = created_checkout.billing_address
    assert billing_address
    assert billing_address.city == address_data["city"]
    assert billing_address.country_area == address_data["countryArea"]
    assert billing_address.postal_code == address_data["postalCode"]
    assert billing_address.street_address_1 == address_data["streetAddress1"]


def test_checkout_create_with_disabled_fields_normalization_raises_required_error(
    api_client, stock, channel_USD
):
    # given
    address_data = {
        "city": "Wroclaw",
        "country": "PL",
        "firstName": "John",
        "lastName": "Doe",
        "phone": "+12125094995",
        "streetAddress1": "Teczowa 7",
    }
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            "shippingAddress": address_data,
            "validationRules": {
                "shippingAddress": {"enableFieldsNormalization": False}
            },
            "channel": channel_USD.slug,
        }
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    data = get_graphql_content(response)["data"]["checkoutCreate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "postalCode"
    assert data["errors"][0]["code"] == "REQUIRED"


@pytest.mark.parametrize("with_shipping_address", (True, False))
def test_create_checkout_with_digital(
    api_client,
    digital_content,
    graphql_address_data,
    with_shipping_address,
    channel_USD,
):
    """Test creating a checkout with a shipping address gets the address ignored."""

    address_count = Address.objects.count()

    variant = digital_content.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    checkout_input = {
        "channel": channel_USD.slug,
        "lines": [{"quantity": 1, "variantId": variant_id}],
        "email": "customer@example.com",
    }

    if with_shipping_address:
        checkout_input["shippingAddress"] = graphql_address_data

    get_graphql_content(
        api_client.post_graphql(
            MUTATION_CHECKOUT_CREATE, {"checkoutInput": checkout_input}
        )
    )["data"]["checkoutCreate"]

    # Retrieve the created checkout
    checkout = Checkout.objects.get()

    # Check that the shipping address was ignored, thus not created
    assert (
        checkout.shipping_address is None
    ), "The address shouldn't have been associated"
    assert (
        Address.objects.count() == address_count
    ), "No address should have been created"
