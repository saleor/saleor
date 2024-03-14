from unittest import mock

import graphene
import pytest
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time
from prices import Money, TaxedMoney

from .....checkout import calculations
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....core import EventDeliveryStatus
from .....core.models import EventDelivery
from .....order import OrderStatus
from .....order.models import Order
from .....payment.model_helpers import get_subtotal
from .....plugins import PLUGIN_IDENTIFIER_PREFIX
from .....plugins.manager import get_plugins_manager
from .....plugins.tests.sample_plugins import PluginSample
from .....plugins.webhook.conftest import (  # noqa: F401
    tax_data_response,
    tax_line_data_response,
)
from .....webhook.event_types import WebhookEventSyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_CHECKOUT_COMPLETE = """
    mutation checkoutComplete(
            $id: ID,
            $redirectUrl: String,
            $metadata: [MetadataInput!],
        ) {
        checkoutComplete(
                id: $id,
                redirectUrl: $redirectUrl,
                metadata: $metadata,
            ) {
            order {
                id
                token
                original
                origin
                deliveryMethod {
                    ... on Warehouse {
                        id
                    }
                    ... on ShippingMethod {
                        id
                    }
                }
                total {
                    currency
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
                subtotal {
                    currency
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
                undiscountedTotal {
                    currency
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
            }
            errors {
                field,
                message,
                variants,
                code
            }
            confirmationNeeded
            confirmationData
        }
    }
    """


def test_checkout_complete_unconfirmed_order_already_exists(
    user_api_client,
    order_with_lines,
    checkout_with_gift_card,
):
    checkout = checkout_with_gift_card
    orders_count = Order.objects.count()
    order_with_lines.status = OrderStatus.UNCONFIRMED
    order_with_lines.checkout_token = checkout.pk
    order_with_lines.save()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_data = data["order"]
    assert Order.objects.count() == orders_count
    assert order_data["id"] == graphene.Node.to_global_id("Order", order_with_lines.id)
    assert str(order_with_lines.id) == order_data["token"]
    assert order_data["origin"] == order_with_lines.origin.upper()
    assert not order_data["original"]


def test_checkout_complete_order_already_exists(
    user_api_client,
    order_with_lines,
    checkout_with_gift_card,
):
    checkout = checkout_with_gift_card
    orders_count = Order.objects.count()
    order_with_lines.checkout_token = checkout.pk
    order_with_lines.save()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_data = data["order"]
    assert Order.objects.count() == orders_count
    assert order_data["id"] == graphene.Node.to_global_id("Order", order_with_lines.id)
    assert str(order_with_lines.id) == order_data["token"]
    assert order_data["origin"] == order_with_lines.origin.upper()
    assert not order_data["original"]

    order = Order.objects.get()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["net"]["amount"] == subtotal.net.amount


def test_checkout_complete_with_inactive_channel_order_already_exists(
    user_api_client,
    order_with_lines,
    checkout_with_gift_card,
):
    checkout = checkout_with_gift_card
    order_with_lines.checkout_token = checkout.pk
    channel = order_with_lines.channel
    channel.is_active = False
    channel.save()
    order_with_lines.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.CHANNEL_INACTIVE.name
    assert data["errors"][0]["field"] == "channel"


def test_checkout_complete_no_checkout_email(
    user_api_client,
    checkout_with_gift_card,
):
    checkout = checkout_with_gift_card
    checkout.email = None
    checkout.save(update_fields=["email"])

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.EMAIL_NOT_SET.name


@pytest.mark.integration
def test_checkout_complete_0_total_value_no_payment(
    user_api_client,
    checkout_with_item_total_0,
    address,
):
    checkout = checkout_with_item_total_0
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    checkout.refresh_from_db()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.total.gross == total.gross
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["net"]["amount"] == subtotal.net.amount
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address is None
    assert order.shipping_method is None

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_checkout_complete_0_total_value_from_voucher(
    user_api_client,
    checkout_without_shipping_required,
    shipping_method,
    address,
    voucher,
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.voucher_code = voucher.code
    checkout.discount = Money("10.00", "USD")

    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    checkout.refresh_from_db()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.total.gross == total.gross
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["net"]["amount"] == subtotal.net.amount
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address is None
    assert order.shipping_method is None

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_checkout_complete_0_total_value_from_giftcard(
    user_api_client,
    checkout_without_shipping_required,
    address,
    gift_card,
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.gift_cards.add(gift_card)
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    checkout.refresh_from_db()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.total.gross == total.gross
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["net"]["amount"] == subtotal.net.amount
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address is None
    assert order.shipping_method is None

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@freeze_time()
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_complete_fails_with_invalid_tax_app(
    mock_request,
    user_api_client,
    checkout_without_shipping_required,
    channel_USD,
    address,
    tax_app,
    tax_data_response,  # noqa: F811
    settings,
):
    # given
    mock_request.return_value = tax_data_response

    checkout = checkout_without_shipping_required
    checkout.price_expiration = timezone.now()

    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.metadata_storage.save()
    checkout.save()

    channel_USD.tax_configuration.tax_app_id = "invalid"
    channel_USD.tax_configuration.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.TAX_ERROR.name
    assert data["errors"][0]["message"] == "Configured Tax App didn't responded."
    assert not EventDelivery.objects.exists()

    checkout.refresh_from_db()
    assert checkout.price_expiration == timezone.now() + settings.CHECKOUT_PRICES_TTL
    assert checkout.tax_error == "Empty tax data."


@freeze_time()
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_complete_calls_correct_tax_app(
    mock_request,
    user_api_client,
    checkout_without_shipping_required,
    channel_USD,
    address,
    tax_app,
    tax_data_response,  # noqa: F811
    settings,
):
    # given
    mock_request.return_value = tax_data_response

    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.price_expiration = timezone.now()
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.metadata_storage.save()
    checkout.save()

    tax_app.identifier = "test_app"
    tax_app.save()
    channel_USD.tax_configuration.tax_app_id = "test_app"
    channel_USD.tax_configuration.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    assert delivery.webhook.app == tax_app
    mock_request.assert_called_once_with(delivery)

    checkout.refresh_from_db()
    assert checkout.price_expiration == timezone.now() + settings.CHECKOUT_PRICES_TTL
    assert checkout.tax_error is None


@freeze_time()
@mock.patch(
    "saleor.plugins.tests.sample_plugins.PluginSample.calculate_checkout_line_total"
)
@override_settings(PLUGINS=["saleor.plugins.tests.sample_plugins.PluginSample"])
def test_checkout_complete_calls_failing_plugin(
    mock_calculate_checkout_line_total,
    user_api_client,
    checkout_without_shipping_required,
    channel_USD,
    address,
    settings,
):
    # given
    def side_effect(checkout_info, *args, **kwargs):
        price = Money("10.0", checkout_info.checkout.currency)
        checkout_info.checkout.tax_error = "Test error"
        return TaxedMoney(price, price)

    mock_calculate_checkout_line_total.side_effect = side_effect

    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.price_expiration = timezone.now()
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.metadata_storage.save()
    checkout.save()

    channel_USD.tax_configuration.tax_app_id = (
        PLUGIN_IDENTIFIER_PREFIX + PluginSample.PLUGIN_ID
    )
    channel_USD.tax_configuration.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.TAX_ERROR.name
    assert data["errors"][0]["message"] == "Configured Tax App didn't responded."

    checkout.refresh_from_db()
    assert checkout.price_expiration == timezone.now() + settings.CHECKOUT_PRICES_TTL
    assert checkout.tax_error == "Empty tax data."


@freeze_time()
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_complete_calls_correct_force_tax_calculation_when_tax_error_was_saved(
    mock_request,
    user_api_client,
    checkout_without_shipping_required,
    channel_USD,
    address,
    tax_app,
    tax_data_response,  # noqa: F811
    settings,
):
    # given
    mock_request.return_value = tax_data_response

    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.price_expiration = (
        timezone.now() + settings.CHECKOUT_PRICES_TTL + timezone.timedelta(hours=1)
    )
    checkout.tax_error = "Test error."

    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.metadata_storage.save()
    checkout.save()

    tax_app.identifier = "test_app"
    tax_app.save()
    channel_USD.tax_configuration.tax_app_id = "test_app"
    channel_USD.tax_configuration.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    assert delivery.webhook.app == tax_app
    mock_request.assert_called_once_with(delivery)

    checkout.refresh_from_db()
    assert checkout.price_expiration == timezone.now() + settings.CHECKOUT_PRICES_TTL
    assert checkout.tax_error is None
