import datetime
import warnings
from decimal import Decimal
from unittest import mock
from unittest.mock import patch

import graphene
import pytest
import pytz
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.test import override_settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django_countries.fields import Country
from measurement.measures import Weight
from prices import Money

from ....account.models import User
from ....channel.utils import DEPRECATION_WARNING_MESSAGE
from ....checkout import AddressType, base_calculations, calculations
from ....checkout.checkout_cleaner import (
    clean_checkout_payment,
    clean_checkout_shipping,
)
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    fetch_checkout_info,
    fetch_checkout_lines,
    get_delivery_method_info,
)
from ....checkout.models import Checkout
from ....checkout.utils import (
    PRIVATE_META_APP_SHIPPING_ID,
    add_variant_to_checkout,
    calculate_checkout_quantity,
)
from ....core.payments import PaymentInterface
from ....core.prices import quantize_price
from ....payment import TransactionAction, TransactionKind
from ....payment.interface import GatewayResponse
from ....plugins.base_plugin import ExcludedShippingMethod
from ....plugins.manager import get_plugins_manager
from ....plugins.tests.sample_plugins import ActiveDummyPaymentGateway
from ....product.models import ProductChannelListing, ProductVariant
from ....shipping import models as shipping_models
from ....shipping.models import ShippingMethodTranslation
from ....shipping.utils import convert_to_shipping_method_data
from ....tests.utils import dummy_editorjs
from ....warehouse import WarehouseClickAndCollectOption
from ....warehouse.models import PreorderReservation, Reservation, Stock, Warehouse
from ...core.utils import to_global_id_or_none
from ...tests.utils import assert_no_permission, get_graphql_content
from ..mutations.utils import (
    clean_delivery_method,
    update_checkout_shipping_method_if_invalid,
)


def test_clean_delivery_method_after_shipping_address_changes_stay_the_same(
    checkout_with_single_item, address, shipping_method, other_shipping_method
):
    """Ensure the current shipping method applies to new address.

    If it does, then it doesn't need to be changed.
    """

    checkout = checkout_with_single_item
    checkout.shipping_address = address

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    delivery_method = convert_to_shipping_method_data(
        shipping_method, shipping_method.channel_listings.first()
    )
    is_valid_method = clean_delivery_method(checkout_info, lines, delivery_method)
    assert is_valid_method is True


def test_clean_delivery_method_with_preorder_is_valid_for_enabled_warehouse(
    checkout_with_preorders_only, address, warehouses_for_cc
):
    checkout = checkout_with_preorders_only
    checkout.shipping_address = address

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    is_valid_method = clean_delivery_method(checkout_info, lines, warehouses_for_cc[1])

    assert is_valid_method is True


def test_clean_delivery_method_does_nothing_if_no_shipping_method(
    checkout_with_single_item, address, other_shipping_method
):
    """If no shipping method was selected, it shouldn't return an error."""

    checkout = checkout_with_single_item
    checkout.shipping_address = address
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    is_valid_method = clean_delivery_method(checkout_info, lines, None)
    assert is_valid_method is True


def test_update_checkout_shipping_method_if_invalid(
    checkout_with_single_item,
    address,
    shipping_method,
    other_shipping_method,
    shipping_zone_without_countries,
):
    # If the shipping method is invalid, it should be removed.

    checkout = checkout_with_single_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method

    shipping_method.shipping_zone = shipping_zone_without_countries
    shipping_method.save(update_fields=["shipping_zone"])

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    update_checkout_shipping_method_if_invalid(checkout_info, lines)

    assert checkout.shipping_method is None
    assert checkout_info.delivery_method_info.delivery_method is None

    # Ensure the checkout's shipping method was saved
    checkout.refresh_from_db(fields=["shipping_method"])
    assert checkout.shipping_method is None


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


@pytest.fixture
def expected_dummy_gateway():
    return {
        "id": "mirumee.payments.dummy",
        "name": "Dummy",
        "config": [{"field": "store_customer_card", "value": "false"}],
        "currencies": ["USD", "PLN"],
    }


GET_CHECKOUT_PAYMENTS_QUERY = """
query getCheckoutPayments($id: ID) {
    checkout(id: $id) {
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
    variables = {"id": to_global_id_or_none(checkout_with_item)}
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

    variables = {"id": to_global_id_or_none(checkout_with_item)}
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

    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert (
        data["availablePaymentGateways"][0]["id"] == ActiveDummyPaymentGateway.PLUGIN_ID
    )


GET_CHECKOUT_SELECTED_SHIPPING_METHOD = """
query getCheckout($id: ID) {
    checkout(id: $id) {
        shippingMethod {
            id
            name
            description
            price {
                amount
            }
            translation(languageCode: PL) {
                name
                description
            }
            minimumOrderPrice {
                amount
            }
            maximumOrderPrice {
                amount
            }
            minimumOrderWeight {
               unit
               value
            }
            maximumOrderWeight {
               unit
               value
            }
            message
            active
            minimumDeliveryDays
            maximumDeliveryDays
            metadata {
                key
                value
            }
            metadata {
                key
                value
            }
        }
    }
}
"""


def test_checkout_selected_shipping_method(
    api_client, checkout_with_item, address, shipping_zone
):
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    shipping_method = shipping_zone.shipping_methods.first()
    min_weight = 0
    shipping_method.minimum_order_weight = Weight(oz=min_weight)
    max_weight = 10
    shipping_method.maximum_order_weight = Weight(kg=max_weight)
    metadata_key = "md key"
    metadata_value = "md value"
    raw_description = "this is descr"
    description = dummy_editorjs(raw_description)
    shipping_method.description = description
    shipping_method.store_value_in_metadata({metadata_key: metadata_value})
    shipping_method.save()
    translated_name = "Dostawa ekspresowa"
    ShippingMethodTranslation.objects.create(
        language_code="pl", shipping_method=shipping_method, name=translated_name
    )
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.save()

    # when
    query = GET_CHECKOUT_SELECTED_SHIPPING_METHOD
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    shipping_method = shipping_zone.shipping_methods.first()
    # then
    assert data["shippingMethod"]["id"] == (
        graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    )
    assert data["shippingMethod"]["name"] == shipping_method.name
    assert raw_description in data["shippingMethod"]["description"]
    assert data["shippingMethod"]["active"]
    assert data["shippingMethod"]["message"] == ""
    assert (
        data["shippingMethod"]["minimumDeliveryDays"]
        == shipping_method.minimum_delivery_days
    )
    assert (
        data["shippingMethod"]["maximumDeliveryDays"]
        == shipping_method.maximum_delivery_days
    )
    assert data["shippingMethod"]["minimumOrderWeight"]["unit"] == "KG"
    assert data["shippingMethod"]["minimumOrderWeight"]["value"] == min_weight
    assert data["shippingMethod"]["maximumOrderWeight"]["unit"] == "KG"
    assert data["shippingMethod"]["maximumOrderWeight"]["value"] == max_weight
    assert data["shippingMethod"]["metadata"][0]["key"] == metadata_key
    assert data["shippingMethod"]["metadata"][0]["value"] == metadata_value
    assert data["shippingMethod"]["translation"]["name"] == translated_name


GET_CHECKOUT_SELECTED_SHIPPING_METHOD_PRIVATE_FIELDS = """
query getCheckout($id: ID) {
    checkout(id: $id) {
        shippingMethod {
            id
            privateMetadata {
                key
                value
            }
        }
    }
}
"""


def test_checkout_selected_shipping_method_as_staff(
    staff_api_client, checkout_with_item, shipping_zone, permission_manage_shipping
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_shipping)
    shipping_method = shipping_zone.shipping_methods.first()
    metadata_key = "md key"
    metadata_value = "md value"
    shipping_method.store_value_in_private_metadata({metadata_key: metadata_value})
    shipping_method.save()
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.save()

    # when
    query = GET_CHECKOUT_SELECTED_SHIPPING_METHOD_PRIVATE_FIELDS
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    response_metadata = data["shippingMethod"]["privateMetadata"][0]
    assert response_metadata["key"] == metadata_key
    assert response_metadata["value"] == metadata_value


GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS_TEMPLATE = """
query getCheckout($id: ID) {
    checkout(id: $id) {
        %s {
            id
            type
            name
            description
            price {
                amount
            }
            translation(languageCode: PL) {
                name
                description
            }
            minimumOrderPrice {
                amount
            }
            maximumOrderPrice {
                amount
            }
            minimumOrderWeight {
               unit
               value
            }
            maximumOrderWeight {
               unit
               value
            }
            message
            active
            minimumDeliveryDays
            maximumDeliveryDays
            metadata {
                key
                value
            }
        }
    }
}
"""

GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS = (
    GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS_TEMPLATE % "availableShippingMethods"
)


@pytest.mark.parametrize("field", ["availableShippingMethods", "shippingMethods"])
def test_checkout_available_shipping_methods(
    api_client, checkout_with_item, address, shipping_zone, field
):
    # given
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    shipping_method = shipping_zone.shipping_methods.first()
    min_weight = 0
    shipping_method.minimum_order_weight = Weight(oz=min_weight)
    max_weight = 10
    shipping_method.maximum_order_weight = Weight(kg=max_weight)
    metadata_key = "md key"
    metadata_value = "md value"
    raw_description = "this is descr"
    description = dummy_editorjs(raw_description)
    shipping_method.description = description
    shipping_method.store_value_in_metadata({metadata_key: metadata_value})
    shipping_method.save()
    translated_name = "Dostawa ekspresowa"
    ShippingMethodTranslation.objects.create(
        language_code="pl", shipping_method=shipping_method, name=translated_name
    )

    # when
    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS_TEMPLATE % field
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data[field][0]["id"] == (
        graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    )
    assert data[field][0]["name"] == shipping_method.name
    assert data[field][0]["type"] == shipping_method.type.upper()
    assert raw_description in data[field][0]["description"]
    assert data[field][0]["active"]
    assert data[field][0]["message"] == ""
    assert (
        data[field][0]["minimumDeliveryDays"] == shipping_method.minimum_delivery_days
    )
    assert (
        data[field][0]["maximumDeliveryDays"] == shipping_method.maximum_delivery_days
    )
    assert data[field][0]["minimumOrderWeight"]["unit"] == "KG"
    assert data[field][0]["minimumOrderWeight"]["value"] == min_weight
    assert data[field][0]["maximumOrderWeight"]["unit"] == "KG"
    assert data[field][0]["maximumOrderWeight"]["value"] == max_weight
    assert data[field][0]["metadata"][0]["key"] == metadata_key
    assert data[field][0]["metadata"][0]["value"] == metadata_value
    assert data[field][0]["translation"]["name"] == translated_name


@pytest.mark.parametrize("minimum_order_weight_value", [0, 2, None])
def test_checkout_available_shipping_methods_with_weight_based_shipping_method(
    api_client,
    checkout_with_item,
    address,
    shipping_method_weight_based,
    minimum_order_weight_value,
):
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    shipping_method = shipping_method_weight_based
    if minimum_order_weight_value is not None:
        weight = Weight(kg=minimum_order_weight_value)
        shipping_method.minimum_order_weight = weight
        variant = checkout_with_item.lines.first().variant
        variant.weight = weight
        variant.save(update_fields=["weight"])
    else:
        shipping_method.minimum_order_weight = minimum_order_weight_value

    shipping_method.save(update_fields=["minimum_order_weight"])

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    shipping_methods = [method["name"] for method in data["availableShippingMethods"]]
    assert shipping_method.name in shipping_methods


def test_checkout_available_shipping_methods_weight_method_with_higher_minimal_weigh(
    api_client, checkout_with_item, address, shipping_method_weight_based
):
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    shipping_method = shipping_method_weight_based
    weight_value = 5
    shipping_method.minimum_order_weight = Weight(kg=weight_value)
    shipping_method.save(update_fields=["minimum_order_weight"])

    variants = []
    for line in checkout_with_item.lines.all():
        variant = line.variant
        variant.weight = Weight(kg=1)
        variants.append(variant)
    ProductVariant.objects.bulk_update(variants, ["weight"])

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    shipping_methods = [method["name"] for method in data["availableShippingMethods"]]
    assert shipping_method.name not in shipping_methods


def test_checkout_shipping_methods_with_price_based_shipping_method_and_discount(
    api_client,
    checkout_with_item,
    address,
    shipping_method,
):
    """Ensure that price based shipping method is not returned when
    checkout with discounts subtotal is lower than minimal order price."""
    checkout_with_item.shipping_address = address
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )

    checkout_with_item.discount_amount = Decimal(5.0)
    checkout_with_item.save(update_fields=["shipping_address", "discount_amount"])

    shipping_method.name = "Price based"
    shipping_method.save(update_fields=["name"])

    shipping_channel_listing = shipping_method.channel_listings.get(
        channel=checkout_with_item.channel
    )
    shipping_channel_listing.minimum_order_price_amount = subtotal.gross.amount - 1
    shipping_channel_listing.save(update_fields=["minimum_order_price_amount"])

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    shipping_methods = [method["name"] for method in data["availableShippingMethods"]]
    assert shipping_method.name not in shipping_methods


def test_checkout_shipping_methods_with_price_based_shipping_and_shipping_discount(
    api_client,
    checkout_with_item,
    address,
    shipping_method,
    voucher_shipping_type,
):
    """Ensure that price based shipping method is returned when checkout
    has discount on shipping."""
    checkout_with_item.shipping_address = address
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )

    checkout_with_item.discount_amount = Decimal(5.0)
    checkout_with_item.voucher_code = voucher_shipping_type.code
    checkout_with_item.save(
        update_fields=["shipping_address", "discount_amount", "voucher_code"]
    )

    shipping_method.name = "Price based"
    shipping_method.save(update_fields=["name"])

    shipping_channel_listing = shipping_method.channel_listings.get(
        channel=checkout_with_item.channel
    )
    shipping_channel_listing.minimum_order_price_amount = subtotal.gross.amount - 1
    shipping_channel_listing.save(update_fields=["minimum_order_price_amount"])

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    shipping_methods = [method["name"] for method in data["availableShippingMethods"]]
    assert shipping_method.name in shipping_methods


def test_checkout_available_shipping_methods_shipping_zone_without_channels(
    api_client, checkout_with_item, address, shipping_zone
):
    shipping_zone.channels.clear()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert len(data["availableShippingMethods"]) == 0


def test_checkout_available_shipping_methods_excluded_postal_codes(
    api_client, checkout_with_item, address, shipping_zone
):
    address.country = Country("GB")
    address.postal_code = "BH16 7HF"
    address.save()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_method.postal_code_rules.create(start="BH16 7HA", end="BH16 7HG")

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["availableShippingMethods"] == []


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_checkout_available_shipping_methods_with_price_displayed(
    send_webhook_request_sync,
    monkeypatch,
    api_client,
    checkout_with_item,
    address,
    shipping_zone,
    site_settings,
    shipping_app,
):
    shipping_method = shipping_zone.shipping_methods.first()
    listing = shipping_zone.shipping_methods.first().channel_listings.first()
    expected_shipping_price = Money(10, "USD")
    expected_min_order_price = Money(10, "USD")
    expected_max_order_price = Money(999, "USD")
    listing.price = expected_shipping_price
    listing.minimum_order_price = expected_min_order_price
    listing.maximum_order_price = expected_max_order_price
    listing.save()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    translated_name = "Dostawa ekspresowa"
    ShippingMethodTranslation.objects.create(
        language_code="pl", shipping_method=shipping_method, name=translated_name
    )

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS

    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert len(data["availableShippingMethods"]) == 1
    assert data["availableShippingMethods"][0]["name"] == "DHL"
    assert (
        data["availableShippingMethods"][0]["price"]["amount"]
        == expected_shipping_price.amount
    )
    assert (
        data["availableShippingMethods"][0]["minimumOrderPrice"]["amount"]
        == expected_min_order_price.amount
    )
    assert (
        data["availableShippingMethods"][0]["maximumOrderPrice"]["amount"]
        == expected_max_order_price.amount
    )
    assert data["availableShippingMethods"][0]["translation"]["name"] == translated_name


def test_checkout_no_available_shipping_methods_without_address(
    api_client, checkout_with_item
):
    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableShippingMethods"] == []


def test_checkout_no_available_shipping_methods_without_lines(api_client, checkout):
    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS

    variables = {"id": to_global_id_or_none(checkout)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableShippingMethods"] == []


GET_CHECKOUT_AVAILABLE_COLLECTION_POINTS = """
query getCheckout($id: ID) {
    checkout(id: $id) {
        availableCollectionPoints {
            name
            address {
                streetAddress1
            }
        }
    }
}
"""

QUERY_GET_ALL_COLLECTION_POINTS_FROM_CHECKOUT = """
query AvailableCollectionPoints($id: ID) {
  checkout(id: $id) {
    availableCollectionPoints {
      name
    }
  }
}
"""


def test_available_collection_points_for_preorders_variants_in_checkout(
    api_client, staff_api_client, checkout_with_preorders_only
):
    expected_collection_points = list(
        Warehouse.objects.for_country("US")
        .exclude(
            click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
        )
        .values("name")
    )
    response = staff_api_client.post_graphql(
        QUERY_GET_ALL_COLLECTION_POINTS_FROM_CHECKOUT,
        variables={"id": to_global_id_or_none(checkout_with_preorders_only)},
    )
    response_content = get_graphql_content(response)
    assert (
        expected_collection_points
        == response_content["data"]["checkout"]["availableCollectionPoints"]
    )


def test_available_collection_points_for_preorders_and_regular_variants_in_checkout(
    api_client,
    staff_api_client,
    checkout_with_preorders_and_regular_variant,
    warehouses_for_cc,
):
    expected_collection_points = [{"name": warehouses_for_cc[1].name}]
    response = staff_api_client.post_graphql(
        QUERY_GET_ALL_COLLECTION_POINTS_FROM_CHECKOUT,
        variables={
            "id": to_global_id_or_none(checkout_with_preorders_and_regular_variant)
        },
    )
    response_content = get_graphql_content(response)
    assert (
        expected_collection_points
        == response_content["data"]["checkout"]["availableCollectionPoints"]
    )


def test_checkout_available_collection_points_with_lines_avail_in_1_local_and_1_all(
    api_client, checkout_with_items_for_cc, stocks_for_cc
):
    expected_collection_points = [
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": "Warehouse4"},
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": "Warehouse2"},
    ]

    query = GET_CHECKOUT_AVAILABLE_COLLECTION_POINTS
    variables = {"id": to_global_id_or_none(checkout_with_items_for_cc)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    received_collection_points = content["data"]["checkout"][
        "availableCollectionPoints"
    ]

    assert len(received_collection_points) == len(expected_collection_points)
    assert all(c in expected_collection_points for c in received_collection_points)


def test_checkout_available_collection_points_with_line_avail_in_2_local_and_1_all(
    api_client, checkout_with_item_for_cc, stocks_for_cc
):
    expected_collection_points = [
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": "Warehouse4"},
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": "Warehouse3"},
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": "Warehouse2"},
    ]

    query = GET_CHECKOUT_AVAILABLE_COLLECTION_POINTS
    variables = {"id": to_global_id_or_none(checkout_with_item_for_cc)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    received_collection_points = content["data"]["checkout"][
        "availableCollectionPoints"
    ]

    assert len(received_collection_points) == len(expected_collection_points)
    assert all(c in expected_collection_points for c in received_collection_points)


def test_checkout_avail_collect_points_exceeded_quantity_shows_only_all_warehouse(
    api_client, checkout_with_items_for_cc, stocks_for_cc
):
    query = GET_CHECKOUT_AVAILABLE_COLLECTION_POINTS
    line = checkout_with_items_for_cc.lines.last()
    line.quantity = (
        Stock.objects.filter(product_variant=line.variant)
        .aggregate(total_quantity=Sum("quantity"))
        .get("total_quantity")
        + 1
    )
    line.save(update_fields=["quantity"])
    checkout_with_items_for_cc.refresh_from_db()

    variables = {"id": to_global_id_or_none(checkout_with_items_for_cc)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableCollectionPoints"] == [
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": "Warehouse2"}
    ]


def test_checkout_avail_collect_points_returns_empty_list_when_not_in_shipping_zone(
    api_client, warehouse_for_cc, checkout_with_items_for_cc
):
    query = GET_CHECKOUT_AVAILABLE_COLLECTION_POINTS
    warehouse_for_cc.shipping_zones.filter(name="Poland").delete()

    variables = {"id": to_global_id_or_none(checkout_with_items_for_cc)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert not data["availableCollectionPoints"]


def test_checkout_avail_collect_fallbacks_to_channel_country_when_no_shipping_address(
    api_client, warehouse_for_cc, checkout_with_items_for_cc
):
    query = GET_CHECKOUT_AVAILABLE_COLLECTION_POINTS
    checkout_with_items_for_cc.shipping_address = None
    checkout_with_items_for_cc.save()

    variables = {"id": to_global_id_or_none(checkout_with_items_for_cc)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableCollectionPoints"] == [
        {
            "address": {"streetAddress1": warehouse_for_cc.address.street_address_1},
            "name": warehouse_for_cc.name,
        }
    ]


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


MUTATION_CHECKOUT_CUSTOMER_ATTACH = """
    mutation checkoutCustomerAttach($id: ID, $customerId: ID) {
        checkoutCustomerAttach(id: $id, customerId: $customerId) {
            checkout {
                token
            }
            errors {
                code
                field
                message
            }
        }
    }
"""


def test_checkout_customer_attach(
    user_api_client, checkout_with_item, customer_user, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_impersonate_user]
    )
    content = get_graphql_content(response)

    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user
    assert checkout.email == customer_user.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_no_customer_id(
    api_client, user_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    variables = {"id": to_global_id_or_none(checkout)}

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
    assert checkout.email == customer_user.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_by_app(
    app_api_client, checkout_with_item, customer_user, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    # Mutation should succeed for authenticated customer
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_impersonate_user]
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user
    assert checkout.email == customer_user.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_by_app_no_customer_id(
    app_api_client, checkout_with_item, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    variables = {"id": to_global_id_or_none(checkout)}

    # Mutation should succeed for authenticated customer
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_impersonate_user],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert data["errors"][0]["field"] == "customerId"


def test_checkout_customer_attach_by_app_without_permission(
    app_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    # Mutation should succeed for authenticated customer
    response = app_api_client.post_graphql(
        query,
        variables,
    )

    assert_no_permission(response)


def test_checkout_customer_attach_user_to_checkout_with_user(
    user_api_client, customer_user, user_checkout, address
):
    checkout = user_checkout

    query = """
    mutation checkoutCustomerAttach($id: ID) {
        checkoutCustomerAttach(id: $id) {
            checkout {
                token
            }
            errors {
                field
                message
                code
            }
        }
    }
"""

    default_address = address.get_copy()
    second_user = User.objects.create_user(
        "test2@example.com",
        "password",
        default_billing_address=default_address,
        default_shipping_address=default_address,
        first_name="Test2",
        last_name="Tested",
    )

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    customer_id = graphene.Node.to_global_id("User", second_user.pk)
    variables = {"id": checkout_id, "customerId": customer_id}
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


GET_CHECKOUT_STOCK_RESERVATION_EXPIRES_QUERY = """
query getCheckoutStockReservationExpiration($id: ID) {
    checkout(id: $id) {
        stockReservationExpires
    }
}
"""


def test_checkout_reservation_date_for_stock_reservation(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_one_reservation,
    address,
):
    reservation = Reservation.objects.order_by("reserved_until").first()
    query = GET_CHECKOUT_STOCK_RESERVATION_EXPIRES_QUERY
    variables = {
        "id": to_global_id_or_none(checkout_line_with_one_reservation.checkout)
    }
    response = api_client.post_graphql(query, variables)
    data = get_graphql_content(response)["data"]["checkout"]["stockReservationExpires"]
    assert parse_datetime(data) == reservation.reserved_until


def test_checkout_reservation_date_for_preorder_reservation(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_reserved_preorder_item,
    address,
):
    reservation = PreorderReservation.objects.order_by("reserved_until").first()
    query = GET_CHECKOUT_STOCK_RESERVATION_EXPIRES_QUERY
    variables = {
        "id": to_global_id_or_none(checkout_line_with_reserved_preorder_item.checkout)
    }
    response = api_client.post_graphql(query, variables)
    data = get_graphql_content(response)["data"]["checkout"]["stockReservationExpires"]
    assert parse_datetime(data) == reservation.reserved_until


def test_checkout_reservation_date_for_multiple_reservations(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_one_reservation,
    checkout_line_with_reservation_in_many_stocks,
    address,
):
    reservation = Reservation.objects.order_by("reserved_until").first()
    query = GET_CHECKOUT_STOCK_RESERVATION_EXPIRES_QUERY
    variables = {
        "id": to_global_id_or_none(checkout_line_with_one_reservation.checkout)
    }
    response = api_client.post_graphql(query, variables)
    data = get_graphql_content(response)["data"]["checkout"]["stockReservationExpires"]
    assert parse_datetime(data) == reservation.reserved_until


def test_checkout_reservation_date_for_multiple_reservations_types(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_one_reservation,
    checkout_line_with_reserved_preorder_item,
    address,
):
    Reservation.objects.update(
        reserved_until=timezone.now() + datetime.timedelta(minutes=3)
    )
    PreorderReservation.objects.update(
        reserved_until=timezone.now() + datetime.timedelta(minutes=1)
    )

    reservation = PreorderReservation.objects.order_by("reserved_until").first()
    query = GET_CHECKOUT_STOCK_RESERVATION_EXPIRES_QUERY
    variables = {
        "id": to_global_id_or_none(checkout_line_with_one_reservation.checkout)
    }
    response = api_client.post_graphql(query, variables)
    data = get_graphql_content(response)["data"]["checkout"]["stockReservationExpires"]
    assert parse_datetime(data) == reservation.reserved_until


def test_checkout_reservation_date_for_expired_reservations(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_one_reservation,
    checkout_line_with_reserved_preorder_item,
    address,
):
    Reservation.objects.update(
        reserved_until=timezone.now() - datetime.timedelta(minutes=1)
    )
    PreorderReservation.objects.update(
        reserved_until=timezone.now() - datetime.timedelta(minutes=1)
    )

    query = GET_CHECKOUT_STOCK_RESERVATION_EXPIRES_QUERY
    variables = {
        "id": to_global_id_or_none(checkout_line_with_one_reservation.checkout)
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["stockReservationExpires"] is None


def test_checkout_reservation_date_for_no_reservations(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_one_reservation,
    checkout_line_with_reserved_preorder_item,
    address,
):
    Reservation.objects.all().delete()
    PreorderReservation.objects.all().delete()

    query = GET_CHECKOUT_STOCK_RESERVATION_EXPIRES_QUERY
    variables = {
        "id": to_global_id_or_none(checkout_line_with_one_reservation.checkout)
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["stockReservationExpires"] is None


def test_checkout_reservation_date_for_disabled_reservations(
    api_client,
    checkout_line_with_one_reservation,
    checkout_line_with_reserved_preorder_item,
    address,
):
    query = GET_CHECKOUT_STOCK_RESERVATION_EXPIRES_QUERY
    variables = {
        "id": to_global_id_or_none(checkout_line_with_one_reservation.checkout)
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["stockReservationExpires"] is None


MUTATION_CHECKOUT_CUSTOMER_DETACH = """
    mutation checkoutCustomerDetach($id: ID) {
        checkoutCustomerDetach(id: $id) {
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
    previous_last_change = checkout.last_change

    variables = {"id": to_global_id_or_none(checkout)}

    # Mutation should succeed if the user owns this checkout.
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerDetach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user is None
    assert checkout.last_change != previous_last_change

    # Mutation should fail when user calling it doesn't own the checkout.
    other_user = User.objects.create_user("othercustomer@example.com", "password")
    checkout.user = other_user
    checkout.save()
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH, variables
    )
    assert_no_permission(response)


def test_checkout_customer_detach_by_app(
    app_api_client, checkout_with_item, customer_user, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    previous_last_change = checkout.last_change

    variables = {"id": to_global_id_or_none(checkout)}

    # Mutation should succeed if the user owns this checkout.
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH,
        variables,
        permissions=[permission_impersonate_user],
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerDetach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user is None
    assert checkout.last_change != previous_last_change


def test_checkout_customer_detach_by_app_without_permissions(
    app_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    previous_last_change = checkout.last_change

    variables = {"id": to_global_id_or_none(checkout)}

    # Mutation should succeed if the user owns this checkout.
    response = app_api_client.post_graphql(MUTATION_CHECKOUT_CUSTOMER_DETACH, variables)

    assert_no_permission(response)
    checkout.refresh_from_db()
    assert checkout.last_change == previous_last_change


MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE = """
    mutation checkoutShippingAddressUpdate(
            $id: ID, $shippingAddress: AddressInput!) {
        checkoutShippingAddressUpdate(
                id: $id, shippingAddress: $shippingAddress) {
            checkout {
                token,
                id
            },
            errors {
                field
                message
                code
            }
        }
    }"""


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "update_checkout_shipping_method_if_invalid",
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
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "shippingAddress": shipping_address,
    }

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
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "update_checkout_shipping_method_if_invalid",
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
    checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    checkout.set_country("PL", commit=True)
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

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
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.country == shipping_address["country"]
    assert checkout.last_change != previous_last_change


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "update_checkout_shipping_method_if_invalid",
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
    checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    checkout.set_country("PL", commit=True)
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    Stock.objects.filter(
        warehouse__shipping_zones__countries__contains="US", product_variant=variant
    ).update(quantity=0)
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    errors = data["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"
    checkout.refresh_from_db()
    assert checkout.last_change == previous_last_change


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_with_reserved_stocks(
    mocked_update_shipping_method,
    site_settings_with_reservations,
    channel_USD,
    user_api_client,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
):
    variant = variant_with_many_stocks_different_shipping_zones
    checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    checkout.set_country("PL", commit=True)
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 2)
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }
    other_checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    other_checkout_line = other_checkout.lines.create(
        variant=variant,
        quantity=1,
    )
    Reservation.objects.create(
        checkout_line=other_checkout_line,
        stock=variant.stocks.filter(
            warehouse__shipping_zones__countries__contains="US"
        ).first(),
        quantity_reserved=1,
        reserved_until=timezone.now() + datetime.timedelta(minutes=5),
    )

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_against_reserved_stocks(
    mocked_update_shipping_method,
    site_settings_with_reservations,
    channel_USD,
    user_api_client,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
):
    variant = variant_with_many_stocks_different_shipping_zones
    checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    checkout.set_country("PL", commit=True)
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 2)
    Stock.objects.filter(
        warehouse__shipping_zones__countries__contains="US", product_variant=variant
    ).update(quantity=2)
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    other_checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    other_checkout_line = other_checkout.lines.create(
        variant=variant,
        quantity=3,
    )
    Reservation.objects.create(
        checkout_line=other_checkout_line,
        stock=variant.stocks.filter(
            warehouse__shipping_zones__countries__contains="US"
        ).first(),
        quantity_reserved=3,
        reserved_until=timezone.now() + datetime.timedelta(minutes=5),
    )

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    errors = data["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


def test_checkout_shipping_address_update_channel_without_shipping_zones(
    user_api_client,
    checkout_with_item,
    graphql_address_data,
):
    checkout = checkout_with_item
    checkout.channel.shipping_zones.clear()
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    errors = data["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"
    checkout.refresh_from_db()
    assert checkout.last_change == previous_last_change


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
                "id": to_global_id_or_none(checkout),
                "shippingAddress": shipping_address,
            },
        )
    )["data"]["checkoutShippingAddressUpdate"]

    assert response["errors"] == [
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

    shipping_address = graphql_address_data
    shipping_address["phone"] = number
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

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

    shipping_address = graphql_address_data
    shipping_address["phone"] = "+1-202-555-0132"
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]


@mock.patch(
    "saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_checkout"
)
def test_checkout_shipping_address_update_exclude_shipping_method(
    mocked_webhook,
    user_api_client,
    checkout_with_items_and_shipping,
    graphql_address_data,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    checkout = checkout_with_items_and_shipping
    shipping_method = checkout.shipping_method
    assert shipping_method is not None
    webhook_reason = "hello-there"
    mocked_webhook.return_value = [
        ExcludedShippingMethod(shipping_method.id, webhook_reason)
    ]
    shipping_address = graphql_address_data
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    user_api_client.post_graphql(MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables)
    checkout.refresh_from_db()
    assert checkout.shipping_method is None


def test_checkout_billing_address_update(
    user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    query = """
    mutation checkoutBillingAddressUpdate(
            $id: ID, $billingAddress: AddressInput!) {
        checkoutBillingAddressUpdate(
                id: $id, billingAddress: $billingAddress) {
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

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "billingAddress": billing_address,
    }

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
    assert checkout.last_change != previous_last_change


CHECKOUT_EMAIL_UPDATE_MUTATION = """
    mutation checkoutEmailUpdate($id: ID, $email: String!) {
        checkoutEmailUpdate(id: $id, email: $email) {
            checkout {
                id,
                email
            },
            errors {
                field,
                message
            }
            errors {
                field,
                message
                code
            }
        }
    }
"""


def test_checkout_email_update(user_api_client, checkout_with_item):
    checkout = checkout_with_item
    checkout.email = None
    checkout.save(update_fields=["email"])
    previous_last_change = checkout.last_change

    email = "test@example.com"
    variables = {"id": to_global_id_or_none(checkout), "email": email}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutEmailUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.email == email
    assert checkout.last_change != previous_last_change


def test_checkout_email_update_validation(user_api_client, checkout_with_item):
    variables = {"id": to_global_id_or_none(checkout_with_item), "email": ""}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    previous_last_change = checkout_with_item.last_change

    errors = content["data"]["checkoutEmailUpdate"]["errors"]
    assert errors
    assert errors[0]["field"] == "email"
    assert errors[0]["message"] == "This field cannot be blank."

    checkout_errors = content["data"]["checkoutEmailUpdate"]["errors"]
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert checkout_with_item.last_change == previous_last_change


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

QUERY_CHECKOUT_USER_ID = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
           user {
               id
           }
        }
    }
    """


def test_anonymous_client_can_fetch_anonymoues_checkout_user(api_client, checkout):
    # given
    query = QUERY_CHECKOUT_USER_ID
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(query, variables)

    # then

    content = get_graphql_content(response)
    assert not content["data"]["checkout"]["user"]


def test_anonymous_client_cant_fetch_checkout_with_attached_user(
    api_client, checkout, customer_user
):
    # given
    checkout.user = customer_user
    checkout.save()

    query = QUERY_CHECKOUT_USER_ID
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkout"]


def test_authorized_access_to_checkout_user_as_customer(
    user_api_client,
    checkout,
    customer_user,
):
    query = QUERY_CHECKOUT_USER_ID
    checkout.user = customer_user
    checkout.save()

    variables = {"id": to_global_id_or_none(checkout)}
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

    variables = {"id": to_global_id_or_none(checkout)}
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

    variables = {"id": to_global_id_or_none(checkout)}

    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    assert_no_permission(response)


QUERY_CHECKOUT = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            token
        }
    }
"""


def test_query_anonymous_customer_checkout_as_anonymous_customer(api_client, checkout):
    variables = {"id": to_global_id_or_none(checkout), "channel": checkout.channel.slug}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


QUERY_CHECKOUT_CHANNEL_SLUG = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
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
    variables = {"id": to_global_id_or_none(checkout)}

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
        "id": to_global_id_or_none(checkout),
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    assert content["data"]["checkout"]["token"] == checkout_token
    assert content["data"]["checkout"]["channel"]["slug"] == channel_slug


def test_query_anonymous_customer_checkout_as_customer(user_api_client, checkout):
    variables = {"id": to_global_id_or_none(checkout)}
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_anonymous_customer_checkout_as_staff_user(
    staff_api_client, checkout, permission_manage_checkouts
):
    variables = {"id": to_global_id_or_none(checkout)}
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
    variables = {"id": to_global_id_or_none(checkout)}
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
    variables = {"id": to_global_id_or_none(checkout)}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert not content["data"]["checkout"]


def test_query_customer_checkout_as_customer(user_api_client, checkout, customer_user):
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"id": to_global_id_or_none(checkout)}
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_other_customer_checkout_as_customer(
    user_api_client, checkout, staff_user
):
    checkout.user = staff_user
    checkout.save(update_fields=["user"])
    variables = {"id": to_global_id_or_none(checkout)}
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert not content["data"]["checkout"]


def test_query_customer_checkout_as_staff_user(
    app_api_client, checkout, customer_user, permission_manage_checkouts
):
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"id": to_global_id_or_none(checkout)}
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
    variables = {"id": to_global_id_or_none(checkout)}
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_fetch_checkout_invalid_token(user_api_client, channel_USD, checkout):
    variables = {"id": to_global_id_or_none(checkout)}
    checkout.delete()
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data is None


QUERY_CHECKOUT_PRICES = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
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
                unitPrice {
                    gross {
                        amount
                    }
                }
                undiscountedUnitPrice {
                    amount
                    currency
                }
                totalPrice {
                    currency
                    gross {
                        amount
                    }
                }
                undiscountedTotalPrice {
                    amount
                    currency
                }
           }
        }
    }
"""


def test_checkout_prices(user_api_client, checkout_with_item):
    # given
    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout_with_item)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout_with_item.token)
    assert len(data["lines"]) == checkout_with_item.lines.count()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    assert data["totalPrice"]["gross"]["amount"] == (total.gross.amount)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    assert data["subtotalPrice"]["gross"]["amount"] == (subtotal.gross.amount)

    line_info = lines[0]
    assert line_info.line.quantity > 0
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
        discounts=[],
    ).price_with_discounts
    assert (
        data["lines"][0]["unitPrice"]["gross"]["amount"]
        == line_total_price.gross.amount / line_info.line.quantity
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.variant.get_price(
        line_info.product,
        line_info.collections,
        checkout_info.channel,
        line_info.channel_listing,
        [],
        line_info.line.price_override,
    )
    assert (
        data["lines"][0]["undiscountedUnitPrice"]["amount"]
        == undiscounted_unit_price.amount
    )
    assert (
        data["lines"][0]["undiscountedTotalPrice"]["amount"]
        == undiscounted_unit_price.amount * line_info.line.quantity
    )


def test_checkout_prices_checkout_with_custom_prices(
    user_api_client, checkout_with_item
):
    # given
    query = QUERY_CHECKOUT_PRICES
    checkout_line = checkout_with_item.lines.first()
    price_override = Decimal("20.00")
    checkout_line.price_override = price_override
    checkout_line.save(update_fields=["price_override"])

    variables = {"id": to_global_id_or_none(checkout_with_item)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout_with_item.token)
    assert len(data["lines"]) == checkout_with_item.lines.count()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    shipping_price = base_calculations.base_checkout_delivery_price(
        checkout_info, lines
    )
    assert (
        data["totalPrice"]["gross"]["amount"]
        == checkout_line.quantity * price_override + shipping_price.gross.amount
    )
    assert (
        data["subtotalPrice"]["gross"]["amount"]
        == checkout_line.quantity * price_override
    )
    line_info = lines[0]
    assert line_info.line.quantity > 0
    assert data["lines"][0]["unitPrice"]["gross"]["amount"] == price_override
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == checkout_line.quantity * price_override
    )
    assert data["lines"][0]["undiscountedUnitPrice"]["amount"] == price_override
    assert (
        data["lines"][0]["undiscountedTotalPrice"]["amount"]
        == price_override * line_info.line.quantity
    )


def test_checkout_prices_with_sales(user_api_client, checkout_with_item, discount_info):
    # given
    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout_with_item)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout_with_item.token)
    assert len(data["lines"]) == checkout_with_item.lines.count()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
        discounts=[discount_info],
    )
    assert data["totalPrice"]["gross"]["amount"] == (total.gross.amount)
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
        discounts=[discount_info],
    )
    assert data["subtotalPrice"]["gross"]["amount"] == (subtotal.gross.amount)
    line_info = lines[0]
    assert line_info.line.quantity > 0
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
        discounts=[discount_info],
    ).price_with_discounts
    assert (
        data["lines"][0]["unitPrice"]["gross"]["amount"]
        == line_total_price.gross.amount / line_info.line.quantity
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.variant.get_price(
        line_info.product,
        line_info.collections,
        checkout_info.channel,
        line_info.channel_listing,
        [],
        line_info.line.price_override,
    )
    assert (
        data["lines"][0]["undiscountedUnitPrice"]["amount"]
        == undiscounted_unit_price.amount
    )
    assert (
        data["lines"][0]["undiscountedTotalPrice"]["amount"]
        == undiscounted_unit_price.amount * line_info.line.quantity
    )


def test_checkout_prices_with_specific_voucher(
    user_api_client, checkout_with_item_and_voucher_specific_products
):
    # given
    checkout = checkout_with_item_and_voucher_specific_products
    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == checkout.lines.count()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_info.shipping_address,
    )
    assert data["totalPrice"]["gross"]["amount"] == (total.gross.amount)
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_info.shipping_address,
    )
    assert data["subtotalPrice"]["gross"]["amount"] == (subtotal.gross.amount)
    line_info = lines[0]
    assert line_info.line.quantity > 0
    line_total_prices = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    assert (
        line_total_prices.price_with_discounts != line_total_prices.undiscounted_price
    )
    assert line_total_prices.price_with_discounts != line_total_prices.price_with_sale
    line_total_price = line_total_prices.price_with_discounts
    assert (
        data["lines"][0]["unitPrice"]["gross"]["amount"]
        == line_total_price.gross.amount / line_info.line.quantity
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.variant.get_price(
        line_info.product,
        line_info.collections,
        checkout_info.channel,
        line_info.channel_listing,
        [],
        line_info.line.price_override,
    )
    assert (
        data["lines"][0]["undiscountedUnitPrice"]["amount"]
        == undiscounted_unit_price.amount
    )
    assert (
        data["lines"][0]["undiscountedTotalPrice"]["amount"]
        == undiscounted_unit_price.amount * line_info.line.quantity
    )


def test_checkout_prices_with_voucher_once_per_order(
    user_api_client, checkout_with_item_and_voucher_once_per_order
):
    # given
    checkout = checkout_with_item_and_voucher_once_per_order
    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == checkout.lines.count()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_info.shipping_address,
    )
    assert data["totalPrice"]["gross"]["amount"] == (total.gross.amount)
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_info.shipping_address,
    )
    assert data["subtotalPrice"]["gross"]["amount"] == (subtotal.gross.amount)
    line_info = lines[0]
    assert line_info.line.quantity > 0
    line_total_prices = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    assert (
        line_total_prices.price_with_discounts != line_total_prices.undiscounted_price
    )
    assert line_total_prices.price_with_discounts != line_total_prices.price_with_sale
    line_total_price = line_total_prices.price_with_discounts
    assert data["lines"][0]["unitPrice"]["gross"]["amount"] == float(
        quantize_price(
            line_total_price.gross.amount / line_info.line.quantity, checkout.currency
        )
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.variant.get_price(
        line_info.product,
        line_info.collections,
        checkout_info.channel,
        line_info.channel_listing,
        [],
        line_info.line.price_override,
    )
    assert (
        data["lines"][0]["undiscountedUnitPrice"]["amount"]
        == undiscounted_unit_price.amount
    )
    assert (
        data["lines"][0]["undiscountedTotalPrice"]["amount"]
        == undiscounted_unit_price.amount * line_info.line.quantity
    )


MUTATION_UPDATE_SHIPPING_METHOD = """
    mutation checkoutShippingMethodUpdate(
            $id: ID, $shippingMethodId: ID!){
        checkoutShippingMethodUpdate(
            id: $id, shippingMethodId: $shippingMethodId) {
            errors {
                field
                message
                code
            }
            checkout {
                token
            }
        }
    }
"""

MUTATION_UPDATE_DELIVERY_METHOD = """
    mutation checkoutDeliveryMethodUpdate(
            $id: ID, $deliveryMethodId: ID) {
        checkoutDeliveryMethodUpdate(
            id: $id,
            deliveryMethodId: $deliveryMethodId) {
            checkout {
            id
            deliveryMethod {
                __typename
                ... on ShippingMethod {
                    name
                    id
                    translation(languageCode: EN_US) {
                        name
                    }
                }
                ... on Warehouse {
                   name
                   id
                }
            }
        }
        errors {
            field
            message
            code
        }
    }
}
"""


# TODO: Deprecated
@pytest.mark.parametrize("is_valid_shipping_method", (True, False))
@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "clean_delivery_method"
)
def test_checkout_shipping_method_update(
    mock_clean_shipping,
    staff_api_client,
    shipping_method,
    checkout_with_item_and_shipping_method,
    is_valid_shipping_method,
):
    checkout = checkout_with_item_and_shipping_method
    old_shipping_method = checkout.shipping_method
    query = MUTATION_UPDATE_SHIPPING_METHOD
    mock_clean_shipping.return_value = is_valid_shipping_method
    previous_last_change = checkout.last_change

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "shippingMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    checkout.refresh_from_db()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    checkout_info.delivery_method_info = get_delivery_method_info(
        convert_to_shipping_method_data(
            old_shipping_method, old_shipping_method.channel_listings.first()
        ),
        None,
    )
    mock_clean_shipping.assert_called_once_with(
        checkout_info=checkout_info,
        lines=lines,
        method=convert_to_shipping_method_data(
            shipping_method, shipping_method.channel_listings.first()
        ),
    )
    errors = data["errors"]
    if is_valid_shipping_method:
        assert not errors
        assert data["checkout"]["token"] == str(checkout.token)
        assert checkout.shipping_method == shipping_method
        assert checkout.last_change != previous_last_change
    else:
        assert len(errors) == 1
        assert errors[0]["field"] == "shippingMethod"
        assert (
            errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
        )
        assert checkout.shipping_method == old_shipping_method
        assert checkout.last_change == previous_last_change


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_checkout_shipping_method_update_external_shipping_method(
    mock_send_request,
    staff_api_client,
    address,
    checkout_with_item,
    shipping_app,
    channel_USD,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "abcd"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mock_send_request.return_value = mock_json_response

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]
    assert not errors
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert PRIVATE_META_APP_SHIPPING_ID in checkout.private_metadata


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_checkout_shipping_method_update_external_shipping_method_with_tax_plugin(
    mock_send_request,
    staff_api_client,
    address,
    checkout_with_item,
    shipping_app,
    channel_USD,
    settings,
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.webhook.plugin.WebhookPlugin",
    ]
    response_method_id = "abcd"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mock_send_request.return_value = mock_json_response

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save()

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    # Set external shipping method for first time
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    assert not data["errors"]

    # Set external shipping for second time
    # Without a fix this request results in infinite recursion
    # between Avalara and Webhooks plugins
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    assert not data["errors"]


@pytest.mark.parametrize("is_valid_delivery_method", (True, False))
@pytest.mark.parametrize(
    "delivery_method, node_name, attribute_name",
    [
        ("warehouse", "Warehouse", "collection_point"),
        ("shipping_method", "ShippingMethod", "shipping_method"),
    ],
    indirect=("delivery_method",),
)
@patch(
    "saleor.graphql.checkout.mutations.checkout_delivery_method_update."
    "clean_delivery_method"
)
def test_checkout_delivery_method_update(
    mock_clean_delivery,
    api_client,
    delivery_method,
    node_name,
    attribute_name,
    checkout_with_item_for_cc,
    is_valid_delivery_method,
):
    # given
    mock_clean_delivery.return_value = is_valid_delivery_method

    checkout = checkout_with_item_for_cc
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    shipping_method_data = delivery_method
    if attribute_name == "shipping_method":
        shipping_method_data = convert_to_shipping_method_data(
            delivery_method,
            delivery_method.channel_listings.get(),
        )
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = is_valid_delivery_method

    method_id = graphene.Node.to_global_id(node_name, delivery_method.id)

    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    mock_clean_delivery.assert_called_once_with(
        checkout_info=checkout_info, lines=lines, method=shipping_method_data
    )
    errors = data["errors"]
    if is_valid_delivery_method:
        assert not errors
        assert getattr(checkout, attribute_name) == delivery_method
    else:
        assert len(errors) == 1
        assert errors[0]["field"] == "deliveryMethodId"
        assert (
            errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
        )
        assert checkout.shipping_method is None
        assert checkout.collection_point is None


@pytest.mark.parametrize("is_valid_delivery_method", (True, False))
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
@patch(
    "saleor.graphql.checkout.mutations.checkout_delivery_method_update."
    "clean_delivery_method"
)
def test_checkout_delivery_method_update_external_shipping(
    mock_clean_delivery,
    mock_send_request,
    api_client,
    checkout_with_item_for_cc,
    is_valid_delivery_method,
    settings,
    shipping_app,
    channel_USD,
):
    checkout = checkout_with_item_for_cc
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = is_valid_delivery_method

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "abcd"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mock_send_request.return_value = mock_json_response

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]
    if is_valid_delivery_method:
        assert not errors
        assert PRIVATE_META_APP_SHIPPING_ID in checkout.private_metadata
        assert data["checkout"]["deliveryMethod"]["id"] == method_id
    else:
        assert len(errors) == 1
        assert errors[0]["field"] == "deliveryMethodId"
        assert (
            errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
        )
        assert PRIVATE_META_APP_SHIPPING_ID not in checkout.private_metadata


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "clean_delivery_method"
)
def test_checkout_delivery_method_update_with_id_of_different_type_causes_and_error(
    mock_clean_delivery,
    api_client,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = True
    invalid_method_id = graphene.Node.to_global_id("Address", address.id)

    response = api_client.post_graphql(
        query,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": invalid_method_id,
        },
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.INVALID.name
    assert checkout.shipping_method is None
    assert checkout.collection_point is None


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "clean_delivery_method"
)
def test_checkout_delivery_method_with_nonexistant_id_results_not_found(
    mock_clean_delivery,
    api_client,
    warehouse_for_cc,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = True

    nonexistant_id = "YXBwOjEyMzQ6c29tZS1pZA=="
    response = api_client.post_graphql(
        query,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": nonexistant_id,
        },
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    assert not data["checkout"]
    assert data["errors"][0]["field"] == "deliveryMethodId"
    assert data["errors"][0]["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert checkout.shipping_method is None
    assert checkout.collection_point is None


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "clean_delivery_method"
)
def test_checkout_delivery_method_with_empty_fields_results_None(
    mock_clean_delivery,
    api_client,
    warehouse_for_cc,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = True

    response = api_client.post_graphql(
        query,
        {
            "id": to_global_id_or_none(checkout),
        },
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    assert not data["errors"]
    assert data["checkout"]["deliveryMethod"] is None
    assert checkout.shipping_method is None
    assert checkout.collection_point is None


@mock.patch(
    "saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_checkout"
)
def test_checkout_shipping_method_update_excluded_webhook(
    mocked_webhook,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    # given
    webhook_reason = "spanish-inquisition"
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    mocked_webhook.return_value = [
        ExcludedShippingMethod(shipping_method.id, webhook_reason)
    ]

    # when
    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    # then
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None


# Deprecated
@patch("saleor.shipping.postal_codes.is_shipping_method_applicable_for_postal_code")
def test_checkout_shipping_method_update_excluded_postal_code(
    mock_is_shipping_method_available,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD
    mock_is_shipping_method_available.return_value = False

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None
    assert (
        mock_is_shipping_method_available.call_count
        == shipping_models.ShippingMethod.objects.count()
    )


def test_checkout_delivery_method_update_unavailable_variant(
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    checkout_with_item.lines.first().variant.channel_listings.filter(
        channel=checkout_with_item.channel
    ).delete()
    query = MUTATION_UPDATE_SHIPPING_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name


@patch("saleor.shipping.postal_codes.is_shipping_method_applicable_for_postal_code")
def test_checkout_delivery_method_update_excluded_postal_code(
    mock_is_shipping_method_available,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_is_shipping_method_available.return_value = False

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None
    assert (
        mock_is_shipping_method_available.call_count
        == shipping_models.ShippingMethod.objects.count()
    )


# Deprecated
def test_checkout_shipping_method_update_shipping_zone_without_channel(
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    shipping_method.shipping_zone.channels.clear()
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None


def test_checkout_delivery_method_update_shipping_zone_without_channel(
    api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    shipping_method.shipping_zone.channels.clear()
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None


# Deprecated
def test_checkout_shipping_method_update_shipping_zone_with_channel(
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    checkout.refresh_from_db()
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["token"] == str(checkout_with_item.token)

    assert checkout.shipping_method == shipping_method


def test_checkout_delivery_method_update_shipping_zone_with_channel(
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]

    checkout.refresh_from_db()

    checkout.refresh_from_db()
    errors = data["errors"]
    assert not errors

    assert checkout.shipping_method == shipping_method


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

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    manager = get_plugins_manager()
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    # Shouldn't raise any errors

    clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)
    clean_checkout_payment(
        manager, checkout_info, lines, None, CheckoutErrorCode, last_payment=payment
    )


def test_clean_checkout_no_shipping_method(checkout_with_item, address):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    with pytest.raises(ValidationError) as e:
        clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)

    msg = "Shipping method is not set"
    assert e.value.error_dict["shipping_method"][0].message == msg


def test_clean_checkout_no_shipping_address(checkout_with_item, shipping_method):
    checkout = checkout_with_item
    checkout.shipping_method = shipping_method
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    with pytest.raises(ValidationError) as e:
        clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)
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

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    with pytest.raises(ValidationError) as e:
        clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)

    msg = "Delivery method is not valid for your shipping address"

    assert e.value.error_dict["shipping_method"][0].message == msg


def test_clean_checkout_no_billing_address(
    checkout_with_item, address, shipping_method
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()
    payment = checkout.get_last_active_payment()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    with pytest.raises(ValidationError) as e:
        clean_checkout_payment(
            manager, checkout_info, lines, None, CheckoutErrorCode, last_payment=payment
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
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    with pytest.raises(ValidationError) as e:
        clean_checkout_payment(
            manager, checkout_info, lines, None, CheckoutErrorCode, last_payment=payment
        )

    msg = "Provided payment methods can not cover the checkout's total amount"
    assert e.value.error_list[0].message == msg


QUERY_CHECKOUT = """
    query getCheckout($id: ID){
        checkout(id: $id){
            id
            token
            lines{
                id
                variant{
                    id
                }
            }
            shippingPrice{
                currency
                gross {
                    amount
                }
                net {
                    amount
                }
            }
        }
    }
"""


def test_get_variant_data_from_checkout_line_variant_hidden_in_listings(
    checkout_with_item, api_client
):
    # given
    query = QUERY_CHECKOUT
    checkout = checkout_with_item
    variant = checkout.lines.get().variant
    variant.product.channel_listings.update(visible_in_listings=False)
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["lines"][0]["variant"]["id"]


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_checkout_with_vatlayer_set(
    checkout_with_item, api_client, vatlayer, site_settings, shipping_zone
):
    # given
    site_settings.include_taxes_in_prices = True
    site_settings.save()

    query = QUERY_CHECKOUT
    checkout = checkout_with_item
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    variant = checkout.lines.get().variant
    variant.product.channel_listings.update(visible_in_listings=False)
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


QUERY_CHECKOUT_TRANSACTIONS = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
           transactions {
               id
           }
        }
    }
    """


def test_checkout_transactions_missing_permission(api_client, checkout):
    # given
    checkout.payment_transactions.create(
        status="Authorized",
        type="Credit card",
        reference="123",
        currency="USD",
        authorized_value=Decimal("15"),
        available_actions=[TransactionAction.CHARGE, TransactionAction.VOID],
    )
    query = QUERY_CHECKOUT_TRANSACTIONS
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_checkout_transactions_with_manage_checkouts(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    transaction = checkout.payment_transactions.create(
        status="Authorized",
        type="Credit card",
        reference="123",
        currency="USD",
        authorized_value=Decimal("15"),
        available_actions=[TransactionAction.CHARGE, TransactionAction.VOID],
    )
    query = QUERY_CHECKOUT_TRANSACTIONS
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["checkout"]["transactions"]) == 1
    transaction_id = content["data"]["checkout"]["transactions"][0]["id"]
    assert transaction_id == graphene.Node.to_global_id(
        "TransactionItem", transaction.id
    )


def test_checkout_transactions_with_handle_payments(
    staff_api_client, checkout, permission_manage_payments
):
    # given
    transaction = checkout.payment_transactions.create(
        status="Authorized",
        type="Credit card",
        reference="123",
        currency="USD",
        authorized_value=Decimal("15"),
        available_actions=[TransactionAction.CHARGE, TransactionAction.VOID],
    )
    query = QUERY_CHECKOUT_TRANSACTIONS
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["checkout"]["transactions"]) == 1
    transaction_id = content["data"]["checkout"]["transactions"][0]["id"]
    assert transaction_id == graphene.Node.to_global_id(
        "TransactionItem", transaction.id
    )
