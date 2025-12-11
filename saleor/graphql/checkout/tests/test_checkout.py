import datetime
import json
from decimal import Decimal
from unittest import mock

import freezegun
import graphene
import pytest
from django.core.exceptions import ValidationError
from django.db.models import F
from django.test import override_settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django_countries.fields import Country
from freezegun import freeze_time
from measurement.measures import Weight
from prices import Money

from ....checkout import base_calculations, calculations
from ....checkout.calculations import (
    _calculate_and_add_tax,
    _fetch_checkout_prices_if_expired,
    fetch_checkout_data,
)
from ....checkout.checkout_cleaner import (
    clean_checkout_payment,
    clean_checkout_shipping,
)
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.models import Checkout
from ....checkout.utils import (
    PRIVATE_META_APP_SHIPPING_ID,
    add_variant_to_checkout,
    add_voucher_to_checkout,
)
from ....core.db.connection import allow_writer
from ....core.prices import quantize_price
from ....discount import DiscountValueType, VoucherType
from ....giftcard.const import (
    GIFT_CARD_PAYMENT_GATEWAY_ID,
    GIFT_CARD_PAYMENT_GATEWAY_NAME,
)
from ....payment import TransactionAction
from ....payment.interface import (
    ListStoredPaymentMethodsRequestData,
    PaymentGateway,
    PaymentMethodCreditCardInfo,
    PaymentMethodData,
)
from ....plugins.manager import get_plugins_manager
from ....plugins.tests.sample_plugins import ActiveDummyPaymentGateway
from ....product.models import (
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
)
from ....shipping.models import ShippingMethod, ShippingMethodTranslation
from ....tests import race_condition
from ....tests.utils import dummy_editorjs
from ....warehouse import WarehouseClickAndCollectOption
from ....warehouse.models import PreorderReservation, Reservation, Stock, Warehouse
from ...core.utils import to_global_id_or_none
from ...payment.enums import TokenizedPaymentFlowEnum
from ...tests.utils import assert_no_permission, get_graphql_content
from ..enums import CheckoutAuthorizeStatusEnum, CheckoutChargeStatusEnum


@pytest.fixture
def expected_dummy_gateway():
    return {
        "id": "mirumee.payments.dummy",
        "name": "Dummy",
        "config": [{"field": "store_customer_card", "value": "false"}],
        "currencies": ["USD", "PLN"],
    }


@pytest.fixture
def expected_gift_card_payment_gateway():
    return {
        "config": [],
        "currencies": [
            "USD",
        ],
        "id": GIFT_CARD_PAYMENT_GATEWAY_ID,
        "name": GIFT_CARD_PAYMENT_GATEWAY_NAME,
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
    expected_gift_card_payment_gateway,
):
    query = GET_CHECKOUT_PAYMENTS_QUERY
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["availablePaymentGateways"] == [
        expected_dummy_gateway,
        expected_gift_card_payment_gateway,
    ]


@mock.patch("saleor.plugins.manager.PluginsManager.list_payment_gateways")
def test_checkout_available_payment_gateways_valid_info_sent(
    mocked_list_gateways,
    api_client,
    checkout_with_item,
    checkout_info,
    checkout_lines_info,
):
    # given
    checkout = checkout_with_item
    channel_slug = checkout.channel.slug
    currency = checkout.currency
    query = GET_CHECKOUT_PAYMENTS_QUERY
    variables = {"id": to_global_id_or_none(checkout_with_item)}

    # when
    api_client.post_graphql(query, variables)

    # then
    checkout_info.manager = mock.ANY
    checkout_info.database_connection_name = mock.ANY
    mocked_list_gateways.assert_called_with(
        currency=currency,
        checkout_info=checkout_info,
        checkout_lines=checkout_lines_info,
        channel_slug=channel_slug,
        active_only=True,
    )


def test_checkout_available_payment_gateways_currency_specified_USD(
    api_client,
    checkout_with_item,
    expected_dummy_gateway,
    expected_gift_card_payment_gateway,
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
        expected_gift_card_payment_gateway["id"],
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
    api_client, checkout_with_item, address, shipping_zone, checkout_delivery
):
    # given
    checkout_with_item.shipping_address = address
    checkout_with_item.assigned_delivery = checkout_delivery(checkout_with_item)
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
    query = GET_CHECKOUT_SELECTED_SHIPPING_METHOD
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

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
    assert data["shippingMethod"]["minimumOrderWeight"] is None
    assert data["shippingMethod"]["maximumOrderWeight"] is None
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
    staff_api_client,
    checkout_with_item,
    shipping_zone,
    checkout_delivery,
    permission_manage_shipping,
    address,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    shipping_method = shipping_zone.shipping_methods.get()
    metadata_key = "md key"
    metadata_value = "md value"
    shipping_method.store_value_in_private_metadata({metadata_key: metadata_value})
    shipping_method.save()

    checkout_with_item.assigned_delivery = checkout_delivery(checkout_with_item)
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    # when
    query = GET_CHECKOUT_SELECTED_SHIPPING_METHOD_PRIVATE_FIELDS
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = staff_api_client.post_graphql(query, variables)

    # then
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
    api_client,
    checkout_with_item,
    address,
    shipping_zone,
    checkout_delivery,
    field,
):
    # given
    shipping_method = shipping_zone.shipping_methods.first()
    metadata_key = "md key"
    metadata_value = "md value"
    raw_description = "Description"
    description = dummy_editorjs(raw_description)
    shipping_method.description = description
    shipping_method.store_value_in_metadata({metadata_key: metadata_value})
    shipping_method.save()
    translated_name = "Dostawa ekspresowa"
    ShippingMethodTranslation.objects.create(
        language_code="pl", shipping_method=shipping_method, name=translated_name
    )

    checkout_with_item.shipping_address = address
    checkout_with_item.assigned_delivery = checkout_delivery(checkout_with_item)
    checkout_with_item.delivery_methods_stale_at = timezone.now()
    checkout_with_item.save()

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
    assert data[field][0]["type"] is None
    assert raw_description in data[field][0]["description"]
    assert data[field][0]["active"]
    assert data[field][0]["message"] == ""
    assert data[field][0]["minimumDeliveryDays"] is None
    assert data[field][0]["maximumDeliveryDays"] is None
    assert data[field][0]["minimumOrderWeight"] is None
    assert data[field][0]["maximumOrderWeight"] is None
    assert data[field][0]["metadata"][0]["key"] == metadata_key
    assert data[field][0]["metadata"][0]["value"] == metadata_value
    assert data[field][0]["translation"]["name"] == translated_name


GET_CHECKOUT_SHIPPING_METHODS_QUERY = """
query getCheckout($id: ID) {
    checkout(id: $id) {
		shippingMethods{
            id
            name
        }
    }
}
"""


@mock.patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.excluded_shipping_methods_for_checkout"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_query_checkout_empty_address_with_shipping_method_without_exclude_webhook(
    mock_excluded_shipping_methods_for_checkout,
    api_client,
    checkout_with_item,
    shipping_method,
):
    # given checkout without address
    # and checkout in channel with available shipping methods

    checkout_with_item.metadata_storage.private_metadata = {
        PRIVATE_META_APP_SHIPPING_ID: "TEST_METHOD"
    }
    checkout_with_item.shipping_address = None
    checkout_with_item.billing_address = None

    checkout_with_item.save(update_fields=["shipping_address", "billing_address"])

    # when query is invoked
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    api_client.post_graphql(GET_CHECKOUT_SHIPPING_METHODS_QUERY, variables)

    # then webhook plugin is not executing excluded_shipping_methods_for_checkout

    mock_excluded_shipping_methods_for_checkout.assert_not_called()


@mock.patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.excluded_shipping_methods_for_checkout"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_query_checkout_with_address_with_shipping_method_without_exclude_webhook(
    mock_excluded_shipping_methods_for_checkout,
    api_client,
    checkout_with_item,
    shipping_method,
    address,
):
    # GIVEN checkout with address
    # AND checkout in channel with available shipping methods

    checkout_with_item.metadata_storage.private_metadata = {
        PRIVATE_META_APP_SHIPPING_ID: "TEST_METHOD"
    }
    checkout_with_item.shipping_address = address
    checkout_with_item.billing_address = address

    checkout_with_item.save(update_fields=["shipping_address", "billing_address"])

    # when query is invoked
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    api_client.post_graphql(GET_CHECKOUT_SHIPPING_METHODS_QUERY, variables)

    # then webhook plugin is not executing excluded_shipping_methods_for_checkout

    mock_excluded_shipping_methods_for_checkout.assert_called_once()


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_preventing_circular_payload_generation_when_listing_shipping_methods_for_checkout(
    mock_send_webhook_request_sync,
    api_client,
    checkout_with_item,
    address,
    subscription_shipping_list_methods_for_checkout_webhook,
    caplog,
):
    # This test ensures that the listing external shipping methods are resistant to circular webhooks calls.
    # We call `shipping_methods` field inside `ShippingListMethodsForCheckout` subscription. This resolver should
    # always return only internal shipping methods.
    # given
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    expected_external_shipping_name = "Provider - Economy"
    mock_send_webhook_request_sync.return_value = [
        {
            "amount": "10",
            "currency": checkout_with_item.currency,
            "id": "abcd",
            "name": expected_external_shipping_name,
        },
    ]

    # when
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    response = api_client.post_graphql(GET_CHECKOUT_SHIPPING_METHODS_QUERY, variables)

    # then
    shipping_method = ShippingMethod.objects.get()
    content = get_graphql_content(response)
    # Check if webhook was called with correct payload
    assert mock_send_webhook_request_sync.call_count == 1
    event_delivery = mock_send_webhook_request_sync.call_args[0][0]
    payload = event_delivery.payload.get_payload()
    assert json.loads(payload) == {
        "checkout": {
            "id": to_global_id_or_none(checkout_with_item),
        },
        "shippingMethods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", shipping_method.id),
                "name": shipping_method.name,
            },
        ],
    }
    # Check if shipping methods are correct
    shipping_method_names = {
        shipping_method_data["name"]
        for shipping_method_data in content["data"]["checkout"]["shippingMethods"]
    }
    assert shipping_method_names == {
        expected_external_shipping_name,
        shipping_method.name,
    }
    # Ensure that any logs are generated via circular webhook calls. When webhooks are called in this way, they can
    # generate the 'Subscription did not return a payload' log.
    assert len(caplog.records) == 0


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


def test_checkout_deliveries_with_price_based_shipping_method_and_discount(
    api_client,
    checkout_with_item,
    address,
    shipping_method,
):
    checkout_with_item.shipping_address = address
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

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


def test_checkout_deliveries_with_price_based_shipping_and_shipping_discount(
    api_client,
    checkout_with_item,
    address,
    shipping_method,
    voucher_shipping_type,
):
    """Test that shipping discounts properly qualify checkout for price-based shipping."""
    checkout_with_item.shipping_address = address
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

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


def test_checkout_deliveries_with_price_based_method_and_product_voucher(
    api_client, checkout_with_item, address, shipping_method, voucher, channel_USD
):
    """Test that product discounts properly qualify checkout for price-based shipping."""
    # given
    checkout_with_item.shipping_address = address
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)

    line = checkout_with_item.lines.first()

    voucher.products.add(line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save()

    voucher_percent_value = Decimal(50)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount_value = voucher_percent_value
    voucher_channel_listing.save()

    checkout_with_item.save(update_fields=["shipping_address"])

    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    add_voucher_to_checkout(
        manager, checkout_info, lines, voucher, voucher.codes.first()
    )

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    shipping_method.name = "Price based"
    shipping_method.save(update_fields=["name"])

    shipping_channel_listing = shipping_method.channel_listings.get(
        channel=checkout_with_item.channel
    )
    shipping_channel_listing.price_amount = Decimal(0)

    # set minimum order price on 50% of total. It's to ensure that discount was not
    # doubled during shipping methods fetching. If it was subtotal would be 0
    shipping_channel_listing.minimum_order_price_amount = subtotal.gross.amount / 2
    shipping_channel_listing.save(
        update_fields=["minimum_order_price_amount", "price_amount"]
    )

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_item)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
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


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
    api_client, staff_api_client, checkout_with_preorders_only, channel_USD
):
    # given
    expected_collection_points = list(
        Warehouse.objects.for_channel(channel_USD.id)
        .exclude(
            click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
        )
        .values("name")
    )

    # when
    response = staff_api_client.post_graphql(
        QUERY_GET_ALL_COLLECTION_POINTS_FROM_CHECKOUT,
        variables={"id": to_global_id_or_none(checkout_with_preorders_only)},
    )

    # then
    response_content = get_graphql_content(response)
    assert (
        expected_collection_points
        == response_content["data"]["checkout"]["availableCollectionPoints"]
    )


def test_available_collection_points_for_preorders_and_regular_variants_in_checkout(
    api_client,
    staff_api_client,
    checkout_with_preorders_and_regular_variant,
    preorder_variant_with_end_date,
    warehouses_for_cc,
):
    # given
    warehouse = warehouses_for_cc[1]
    Stock.objects.create(
        warehouse=warehouse,
        product_variant=preorder_variant_with_end_date,
        quantity=10,
    )
    expected_collection_points = [{"name": warehouse.name}]

    # wne
    response = staff_api_client.post_graphql(
        QUERY_GET_ALL_COLLECTION_POINTS_FROM_CHECKOUT,
        variables={
            "id": to_global_id_or_none(checkout_with_preorders_and_regular_variant)
        },
    )

    # then
    response_content = get_graphql_content(response)
    assert (
        expected_collection_points
        == response_content["data"]["checkout"]["availableCollectionPoints"]
    )


def test_checkout_available_collection_points_with_lines_avail_in_1_local_and_1_all(
    api_client, checkout_with_items_for_cc, stocks_for_cc
):
    # given
    expected_collection_points = [
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": "Warehouse4"},
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": "Warehouse2"},
    ]

    query = GET_CHECKOUT_AVAILABLE_COLLECTION_POINTS
    variables = {"id": to_global_id_or_none(checkout_with_items_for_cc)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
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


def test_checkout_available_collection_points_two_lines_for_same_checkout(
    api_client, checkout_with_items_for_cc, stocks_for_cc
):
    # given
    expected_collection_points = [
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": "Warehouse4"},
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": "Warehouse2"},
    ]

    line = checkout_with_items_for_cc.lines.first()
    line_2 = checkout_with_items_for_cc.lines.all()[1]
    line_2.variant = line.variant
    line_2.save(update_fields=["variant"])

    query = GET_CHECKOUT_AVAILABLE_COLLECTION_POINTS
    variables = {"id": to_global_id_or_none(checkout_with_items_for_cc)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    received_collection_points = content["data"]["checkout"][
        "availableCollectionPoints"
    ]

    assert len(received_collection_points) == len(expected_collection_points)
    assert all(c in expected_collection_points for c in received_collection_points)


def test_checkout_avail_collect_points_only_all_warehouse_quantity_collected(
    api_client, checkout_with_item_for_cc, warehouses_for_cc
):
    # given
    query = GET_CHECKOUT_AVAILABLE_COLLECTION_POINTS
    line = checkout_with_item_for_cc.lines.first()
    line.quantity = 5
    line.save(update_fields=["quantity"])

    all_warehouse = warehouses_for_cc[1]
    local_warehouse_1 = warehouses_for_cc[2]
    local_warehouse_2 = warehouses_for_cc[3]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line.variant, quantity=0),
            Stock(
                warehouse=local_warehouse_1, product_variant=line.variant, quantity=2
            ),
            Stock(
                warehouse=local_warehouse_2, product_variant=line.variant, quantity=4
            ),
        ]
    )

    variables = {"id": to_global_id_or_none(checkout_with_item_for_cc)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableCollectionPoints"] == [
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": all_warehouse.name}
    ]


def test_checkout_avail_collect_points_all_warehouse_quantity_from_disabled_warehouse(
    api_client, checkout_with_item_for_cc, warehouses_for_cc
):
    # given
    query = GET_CHECKOUT_AVAILABLE_COLLECTION_POINTS
    line = checkout_with_item_for_cc.lines.first()
    line.quantity = 5
    line.save(update_fields=["quantity"])

    all_warehouse = warehouses_for_cc[1]
    disabled_warehouse = warehouses_for_cc[0]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line.variant, quantity=0),
            Stock(
                warehouse=disabled_warehouse, product_variant=line.variant, quantity=10
            ),
        ]
    )

    variables = {"id": to_global_id_or_none(checkout_with_item_for_cc)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableCollectionPoints"] == [
        {"address": {"streetAddress1": "Tęczowa 7"}, "name": all_warehouse.name}
    ]


def test_checkout_avail_collect_points_returns_empty_list_when_no_channels(
    api_client, warehouse_for_cc, checkout_with_items_for_cc
):
    query = GET_CHECKOUT_AVAILABLE_COLLECTION_POINTS
    checkout_with_items_for_cc.channel.warehouses.remove(warehouse_for_cc)

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


QUERY_CHECKOUT_USER_ID = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
           user {
               id
           }
        }
    }
    """


def test_anonymous_client_can_fetch_anonymous_checkout_user(api_client, checkout):
    # given
    query = QUERY_CHECKOUT_USER_ID
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(query, variables)

    # then

    content = get_graphql_content(response)
    assert not content["data"]["checkout"]["user"]


def test_anonymous_client_cant_fetch_checkout_with_attached_user_with_user_data(
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
    assert_no_permission(response)


def test_anonymous_client_can_fetch_checkout_with_attached_user_without_user_data(
    api_client, checkout, customer_user
):
    # given
    checkout.user = customer_user
    checkout.save()

    query = QUERY_CHECKOUT
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]


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


def test_query_checkout_as_staff_with_no_permission_for_inactive_channel(
    staff_api_client,
    checkout,
    customer_user,
    permission_manage_checkouts,
):
    # given
    query = QUERY_CHECKOUT
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    channel = checkout.channel
    channel.is_active = False
    channel.save(update_fields=["is_active"])
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        check_no_permissions=False,
    )

    # then
    assert_no_permission(response)


def test_query_checkout_as_app_with_no_permission_for_inactive_channel(
    app_api_client,
    checkout,
    customer_user,
    permission_manage_checkouts,
):
    # given
    query = QUERY_CHECKOUT
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    channel = checkout.channel
    channel.is_active = False
    channel.save(update_fields=["is_active"])
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = app_api_client.post_graphql(
        query,
        variables,
        check_no_permissions=False,
    )

    # then
    assert_no_permission(response)


@pytest.mark.parametrize("permission", ["checkouts", "user", "payments"])
def test_query_checkout_as_staff_with_permission_for_inactive_channel(
    staff_api_client,
    checkout,
    customer_user,
    permission_manage_payments,
    permission_manage_checkouts,
    permission_impersonate_user,
    permission,
):
    # given
    permissions = {
        "checkouts": permission_manage_checkouts,
        "user": permission_impersonate_user,
        "payments": permission_manage_payments,
    }
    query = QUERY_CHECKOUT
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    channel = checkout.channel
    channel.is_active = False
    channel.save(update_fields=["is_active"])
    variables = {"id": to_global_id_or_none(checkout)}
    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permissions.get(permission)],
        check_no_permissions=False,
    )
    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]


@pytest.mark.parametrize("permission", ["checkouts", "user", "payments"])
def test_query_checkout_as_app_with_permission_for_inactive_channel(
    app_api_client,
    checkout,
    customer_user,
    permission_manage_payments,
    permission_manage_checkouts,
    permission_impersonate_user,
    permission,
):
    # given
    permissions = {
        "checkouts": permission_manage_checkouts,
        "user": permission_impersonate_user,
        "payments": permission_manage_payments,
    }
    query = QUERY_CHECKOUT
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    channel = checkout.channel
    channel.is_active = False
    channel.save(update_fields=["is_active"])
    variables = {"id": to_global_id_or_none(checkout)}
    # when
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[permissions.get(permission)],
        check_no_permissions=False,
    )
    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]


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


def test_query_anonymous_customer_checkout_as_app_manage_checkouts(
    app_api_client, checkout, permission_manage_checkouts
):
    # given
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_anonymous_customer_checkout_as_app_handle_payments(
    app_api_client, checkout, permission_manage_payments
):
    # given
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_payments],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_customer_checkout_as_anonymous_customer(
    api_client, checkout, customer_user
):
    # given
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]


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
    # given
    checkout.user = staff_user
    checkout.save(update_fields=["user"])
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]


def test_query_other_customer_checkout_as_customer_for_inactive_channel(
    user_api_client, checkout, staff_user
):
    # given
    checkout.user = staff_user
    channel = checkout.channel
    checkout.save(update_fields=["user"])
    channel.is_active = False
    channel.save(update_fields=["is_active"])
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)

    # then
    assert_no_permission(response)


def test_query_customer_checkout_as_staff_user_manage_checkouts(
    app_api_client, checkout, customer_user, permission_manage_checkouts
):
    # given
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_customer_checkout_as_staff_user_handle_payments(
    app_api_client, checkout, customer_user, permission_manage_payments
):
    # given
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_payments],
        check_no_permissions=False,
    )

    # then
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
    displayGrossPrices
    token
    discount {
      amount
    }
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
    problems {
      ... on CheckoutLineProblemVariantNotAvailable {
        __typename
        line {
          id
        }
      }
    }
    lines {
      id
      isGift
      quantity
      variant {
        id
        pricing {
          onSale
          price {
            gross {
              amount
            }
          }
          priceUndiscounted {
            gross {
              amount
            }
          }
          pricePrior {
            gross {
              amount
            }
        }
        }
        product {
          id
          isAvailable
          isAvailableForPurchase
          pricing{
            onSale
            discount{
              gross{
                amount
              }
            }
            discountPrior {
              gross{
                amount
              }
            }
            priceRange{
              start{
                gross{
                  amount
                }
              }
              stop{
                gross{
                  amount
                }
              }
            }
            priceRangeUndiscounted{
              start{
                gross{
                  amount
                }
              }
              stop{
                gross{
                  amount
                }
              }
            }
            priceRangePrior{
              start{
                gross{
                  amount
                }
              }
              stop{
                gross{
                  amount
                }
              }
            }
          }
        }
      }
      unitPrice {
        gross {
          amount
        }
      }
      undiscountedUnitPrice {
        amount
        currency
      }
      priorUnitPrice {
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
      priorTotalPrice {
        amount
        currency
      }
      problems {
        ... on CheckoutLineProblemVariantNotAvailable {
          __typename
        }
      }
    }
  }
}
"""


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_prices_when_line_without_listing(
    channel_listing_model, listing_filter_field, user_api_client, checkout_with_item
):
    # given
    checkout = checkout_with_item
    line_without_listing = checkout_with_item.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: line_without_listing.variant_id},
    ).delete()

    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout)}
    checkout.price_expiration = timezone.now()
    checkout.save()

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert len(data["lines"]) == checkout.lines.count()
    response_api_line_without_listing = [
        line_data
        for line_data in data["lines"]
        if line_data["id"] == to_global_id_or_none(line_without_listing)
    ][0]

    assert response_api_line_without_listing["variant"]["pricing"] is None
    assert (
        response_api_line_without_listing["unitPrice"]["gross"]["amount"]
        == line_without_listing.undiscounted_unit_price_amount
    )
    assert (
        response_api_line_without_listing["undiscountedUnitPrice"]["amount"]
        == line_without_listing.undiscounted_unit_price_amount
    )
    assert (
        response_api_line_without_listing["totalPrice"]["gross"]["amount"]
        == line_without_listing.undiscounted_unit_price_amount
        * line_without_listing.quantity
    )
    assert (
        response_api_line_without_listing["undiscountedTotalPrice"]["amount"]
        == line_without_listing.undiscounted_unit_price_amount
        * line_without_listing.quantity
    )
    checkout_problems = data["problems"]
    assert len(checkout_problems) == 1
    assert (
        checkout_problems[0]["__typename"] == "CheckoutLineProblemVariantNotAvailable"
    )
    assert checkout_problems[0]["line"]["id"] == to_global_id_or_none(
        line_without_listing
    )
    assert len(response_api_line_without_listing["problems"]) == 1
    assert (
        response_api_line_without_listing["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )


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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    total = calculations.calculate_checkout_total(
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
    )
    assert (
        data["lines"][0]["unitPrice"]["gross"]["amount"]
        == line_total_price.gross.amount / line_info.line.quantity
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.variant.get_price(
        line_info.channel_listing,
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    shipping_price = base_calculations.base_checkout_delivery_price(
        checkout_info, lines
    )
    assert (
        data["totalPrice"]["gross"]["amount"]
        == checkout_line.quantity * price_override + shipping_price.amount
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


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_prices_checkout_with_custom_prices_when_line_without_listing(
    channel_listing_model, listing_filter_field, user_api_client, checkout_with_item
):
    # given
    checkout = checkout_with_item

    line_without_listing = checkout_with_item.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: line_without_listing.variant_id},
    ).delete()

    price_override = Decimal("20.00")
    line_without_listing.price_override = price_override
    line_without_listing.undiscounted_unit_price_amount = price_override
    line_without_listing.save(
        update_fields=["price_override", "undiscounted_unit_price_amount"]
    )
    checkout.price_expiration = timezone.now()
    checkout.save()

    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert len(data["lines"]) == checkout.lines.count()
    response_api_line_without_listing = [
        line_data
        for line_data in data["lines"]
        if line_data["id"] == to_global_id_or_none(line_without_listing)
    ][0]

    assert response_api_line_without_listing["variant"]["pricing"] is None
    assert (
        response_api_line_without_listing["unitPrice"]["gross"]["amount"]
        == price_override
    )
    assert (
        response_api_line_without_listing["undiscountedUnitPrice"]["amount"]
        == price_override
    )
    assert (
        response_api_line_without_listing["totalPrice"]["gross"]["amount"]
        == price_override * line_without_listing.quantity
    )
    assert (
        response_api_line_without_listing["undiscountedTotalPrice"]["amount"]
        == price_override * line_without_listing.quantity
    )
    checkout_problems = data["problems"]
    assert len(checkout_problems) == 1
    assert (
        checkout_problems[0]["__typename"] == "CheckoutLineProblemVariantNotAvailable"
    )
    assert checkout_problems[0]["line"]["id"] == to_global_id_or_none(
        line_without_listing
    )
    assert len(response_api_line_without_listing["problems"]) == 1
    assert (
        response_api_line_without_listing["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )


def test_checkout_prices_with_promotion(
    user_api_client, checkout_with_item_on_promotion
):
    # given
    query = QUERY_CHECKOUT_PRICES
    checkout = checkout_with_item_on_promotion
    variables = {"id": to_global_id_or_none(checkout)}

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == checkout.lines.count()

    total = calculations.calculate_checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert data["totalPrice"]["gross"]["amount"] == (total.gross.amount)
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert data["subtotalPrice"]["gross"]["amount"] == (subtotal.gross.amount)
    line_info = lines[0]
    assert line_info.line.quantity > 0
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    assert data["lines"][0]["unitPrice"]["gross"]["amount"] == round(
        line_total_price.gross.amount / line_info.line.quantity, 2
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.variant.get_base_price(
        line_info.channel_listing,
        line_info.line.price_override,
    )
    undiscounted_total_price = undiscounted_unit_price.amount * line_info.line.quantity
    assert (
        data["lines"][0]["undiscountedUnitPrice"]["amount"]
        == undiscounted_unit_price.amount
    )
    assert (
        data["lines"][0]["undiscountedTotalPrice"]["amount"] == undiscounted_total_price
    )
    assert line_total_price.gross.amount < undiscounted_total_price

    assert data["lines"][0]["priorUnitPrice"] is not None
    prior_unit_price_amount = (
        line_info.variant.get_prior_price_amount(line_info.channel_listing) or 0
    )
    prior_total_price = prior_unit_price_amount * line_info.line.quantity
    assert data["lines"][0]["priorUnitPrice"]["amount"] == prior_unit_price_amount
    assert data["lines"][0]["priorTotalPrice"]["amount"] == prior_total_price


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_prices_with_promotion_when_line_without_listing(
    channel_listing_model,
    listing_filter_field,
    user_api_client,
    checkout_with_item_on_promotion,
):
    # given
    query = QUERY_CHECKOUT_PRICES

    checkout = checkout_with_item_on_promotion

    variables = {"id": to_global_id_or_none(checkout)}

    line_without_listing = checkout.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: line_without_listing.variant_id},
    ).delete()

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    line_info = [line for line in lines if line.line.pk == line_without_listing.pk][0]
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    line_unit_price = calculations.checkout_line_unit_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )

    assert len(data["lines"]) == checkout.lines.count()
    response_api_line_without_listing = [
        line_data
        for line_data in data["lines"]
        if line_data["id"] == to_global_id_or_none(line_without_listing)
    ][0]

    assert response_api_line_without_listing["variant"]["pricing"] is None
    assert (
        response_api_line_without_listing["unitPrice"]["gross"]["amount"]
        == line_unit_price.gross.amount
    )
    assert (
        response_api_line_without_listing["undiscountedUnitPrice"]["amount"]
        == line_without_listing.undiscounted_unit_price_amount
    )
    assert (
        response_api_line_without_listing["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    assert (
        response_api_line_without_listing["undiscountedTotalPrice"]["amount"]
        == line_without_listing.undiscounted_unit_price_amount
        * line_without_listing.quantity
    )
    assert line_unit_price.gross < line_without_listing.undiscounted_unit_price
    assert (
        line_total_price.gross
        < line_without_listing.undiscounted_unit_price * line_without_listing.quantity
    )

    checkout_problems = data["problems"]
    assert len(checkout_problems) == 1
    assert (
        checkout_problems[0]["__typename"] == "CheckoutLineProblemVariantNotAvailable"
    )
    assert checkout_problems[0]["line"]["id"] == to_global_id_or_none(
        line_without_listing
    )
    assert len(response_api_line_without_listing["problems"]) == 1
    assert (
        response_api_line_without_listing["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )


def test_checkout_prices_with_order_promotion(
    user_api_client, checkout_with_item_and_order_discount
):
    # given
    query = QUERY_CHECKOUT_PRICES
    checkout = checkout_with_item_and_order_discount
    variables = {"id": to_global_id_or_none(checkout)}

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == checkout.lines.count()

    line = checkout.lines.first()
    variant = line.variant
    variant_listing = variant.channel_listings.get(channel=checkout.channel)
    unit_price = variant.get_price(variant_listing)
    subtotal_price = unit_price * line.quantity
    shipping_price = base_calculations.base_checkout_delivery_price(
        checkout_info, lines
    )
    total_price = subtotal_price + shipping_price
    discount_amount = checkout.discounts.first().amount_value

    assert data["discount"]["amount"] == checkout.discount_amount
    assert data["totalPrice"]["gross"]["amount"] == (
        total_price.amount - discount_amount
    )
    assert data["subtotalPrice"]["gross"]["amount"] == (
        subtotal_price.amount - discount_amount
    )
    assert str(data["lines"][0]["unitPrice"]["gross"]["amount"]) == str(
        round((subtotal_price.amount - discount_amount) / line.quantity, 2)
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == subtotal_price.amount - discount_amount
    )

    assert data["lines"][0]["undiscountedUnitPrice"]["amount"] == unit_price.amount
    assert data["lines"][0]["undiscountedTotalPrice"]["amount"] == subtotal_price.amount


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_prices_with_order_promotion_when_line_without_listing(
    channel_listing_model,
    listing_filter_field,
    user_api_client,
    checkout_with_item_and_order_discount,
):
    # given
    query = QUERY_CHECKOUT_PRICES
    checkout = checkout_with_item_and_order_discount
    variables = {"id": to_global_id_or_none(checkout)}

    line_without_listing = checkout.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: line_without_listing.variant_id},
    ).delete()

    checkout.price_expiration = timezone.now()
    checkout.save()

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    line_info = [line for line in lines if line.line.pk == line_without_listing.pk][0]
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    line_unit_price = calculations.checkout_line_unit_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )

    assert len(data["lines"]) == checkout.lines.count()
    response_api_line_without_listing = [
        line_data
        for line_data in data["lines"]
        if line_data["id"] == to_global_id_or_none(line_without_listing)
    ][0]

    assert response_api_line_without_listing["variant"]["pricing"] is None
    assert str(
        response_api_line_without_listing["unitPrice"]["gross"]["amount"]
    ) == str(round(line_unit_price.gross.amount, 2))
    assert (
        response_api_line_without_listing["undiscountedUnitPrice"]["amount"]
        == line_without_listing.undiscounted_unit_price_amount
    )
    assert (
        response_api_line_without_listing["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    assert (
        response_api_line_without_listing["undiscountedTotalPrice"]["amount"]
        == line_without_listing.undiscounted_unit_price_amount
        * line_without_listing.quantity
    )
    assert line_unit_price.gross < line_without_listing.undiscounted_unit_price
    assert (
        line_total_price.gross
        < line_without_listing.undiscounted_unit_price * line_without_listing.quantity
    )

    checkout_problems = data["problems"]
    assert len(checkout_problems) == 1
    assert (
        checkout_problems[0]["__typename"] == "CheckoutLineProblemVariantNotAvailable"
    )
    assert checkout_problems[0]["line"]["id"] == to_global_id_or_none(
        line_without_listing
    )
    assert len(response_api_line_without_listing["problems"]) == 1
    assert (
        response_api_line_without_listing["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )


def test_checkout_prices_with_gift_promotion(
    user_api_client, checkout_with_item_and_gift_promotion, gift_promotion_rule
):
    # given
    query = QUERY_CHECKOUT_PRICES
    checkout = checkout_with_item_and_gift_promotion
    variants = gift_promotion_rule.gifts.all()
    variant_listings = ProductVariantChannelListing.objects.filter(variant__in=variants)
    top_price, variant_id = max(
        variant_listings.values_list("discounted_price_amount", "variant")
    )

    variables = {"id": to_global_id_or_none(checkout)}

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == checkout.lines.count()

    line = checkout.lines.get(is_gift=False)
    variant = line.variant
    variant_listing = variant.channel_listings.get(channel=checkout.channel)
    unit_price = variant.get_price(variant_listing)
    subtotal_price = unit_price * line.quantity
    shipping_price = base_calculations.base_checkout_delivery_price(
        checkout_info, lines
    )
    total_price = subtotal_price + shipping_price

    assert data["discount"]["amount"] == 0
    assert data["totalPrice"]["gross"]["amount"] == (total_price.amount)
    assert data["subtotalPrice"]["gross"]["amount"] == (subtotal_price.amount)
    line_data = [
        line_data for line_data in data["lines"] if line_data["isGift"] is False
    ][0]
    assert line_data["unitPrice"]["gross"]["amount"] == (
        round((subtotal_price.amount) / line.quantity, 2)
    )
    assert line_data["totalPrice"]["gross"]["amount"] == subtotal_price.amount

    assert line_data["undiscountedUnitPrice"]["amount"] == unit_price.amount
    assert line_data["undiscountedTotalPrice"]["amount"] == subtotal_price.amount
    gift_line = [
        line_data for line_data in data["lines"] if line_data["isGift"] is True
    ][0]
    assert gift_line["unitPrice"]["gross"]["amount"] == 0
    assert gift_line["totalPrice"]["gross"]["amount"] == 0
    assert gift_line["undiscountedUnitPrice"]["amount"] == top_price
    assert gift_line["undiscountedTotalPrice"]["amount"] == top_price
    assert gift_line["variant"]["id"] == graphene.Node.to_global_id(
        "ProductVariant", variant_id
    )


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_prices_with_gift_promotion_when_line_without_listing(
    channel_listing_model,
    listing_filter_field,
    user_api_client,
    checkout_with_item_and_gift_promotion,
    gift_promotion_rule,
):
    # given
    query = QUERY_CHECKOUT_PRICES
    checkout = checkout_with_item_and_gift_promotion
    line_without_listing = checkout.lines.get(is_gift=True)

    variants = gift_promotion_rule.gifts.all()
    variant_listings = ProductVariantChannelListing.objects.filter(variant__in=variants)
    top_price, variant_id = max(
        variant_listings.values_list("discounted_price_amount", "variant")
    )

    variables = {"id": to_global_id_or_none(checkout)}

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    line_info = [line for line in lines if line.line.pk == line_without_listing.pk][0]

    # Calculate the prices based on the existing gift line
    calculations.checkout_line_unit_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: line_without_listing.variant_id},
    ).delete()

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert len(data["lines"]) == checkout.lines.count()
    response_api_line_without_listing = [
        line_data
        for line_data in data["lines"]
        if line_data["id"] == to_global_id_or_none(line_without_listing)
    ][0]

    assert response_api_line_without_listing["variant"]["pricing"] is None
    assert response_api_line_without_listing["unitPrice"]["gross"]["amount"] == 0
    assert (
        response_api_line_without_listing["undiscountedUnitPrice"]["amount"]
        == top_price
    )
    assert response_api_line_without_listing["totalPrice"]["gross"]["amount"] == 0
    assert (
        response_api_line_without_listing["undiscountedTotalPrice"]["amount"]
        == top_price
    )

    checkout_problems = data["problems"]
    assert len(checkout_problems) == 1
    assert (
        checkout_problems[0]["__typename"] == "CheckoutLineProblemVariantNotAvailable"
    )
    assert checkout_problems[0]["line"]["id"] == to_global_id_or_none(
        line_without_listing
    )
    assert len(response_api_line_without_listing["problems"]) == 1
    assert (
        response_api_line_without_listing["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )


def test_checkout_prices_with_promotion_line_deleted_in_meantime(
    user_api_client, checkout_with_item_on_promotion
):
    # given
    query = QUERY_CHECKOUT_PRICES
    checkout = checkout_with_item_on_promotion
    variables = {"id": to_global_id_or_none(checkout)}

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    line_count = checkout.lines.count()

    def delete_checkout_line(*args, **kwargs):
        checkout.lines.first().delete()

    # when
    with race_condition.RunBefore(
        "saleor.graphql.checkout.dataloaders.promotion_rule_infos.CheckoutLineByIdLoader.load_many",
        delete_checkout_line,
    ):
        with allow_writer():
            response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == line_count

    # clear the rules info for total and subtotal calculations,
    # as the values cannot be fetched for deleted line
    lines[0].rules_info = []

    total = calculations.calculate_checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert data["totalPrice"]["gross"]["amount"] == (total.gross.amount)
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert data["subtotalPrice"]["gross"]["amount"] == (subtotal.gross.amount)
    line_info = lines[0]
    assert line_info.line.quantity > 0
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    assert data["lines"][0]["unitPrice"]["gross"]["amount"] == round(
        line_total_price.gross.amount / line_info.line.quantity, 2
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.variant.get_base_price(
        line_info.channel_listing,
        line_info.line.price_override,
    )
    undiscounted_total_price = undiscounted_unit_price.amount * line_info.line.quantity
    assert (
        data["lines"][0]["undiscountedUnitPrice"]["amount"]
        == undiscounted_unit_price.amount
    )
    assert (
        data["lines"][0]["undiscountedTotalPrice"]["amount"] == undiscounted_total_price
    )


def test_checkout_prices_with_promotion_one_line_deleted_in_meantime(
    user_api_client, checkout_with_item_on_promotion, product_list
):
    # given
    query = QUERY_CHECKOUT_PRICES
    checkout = checkout_with_item_on_promotion
    variables = {"id": to_global_id_or_none(checkout)}

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    product = product_list[-1]
    add_variant_to_checkout(checkout_info, product.variants.last(), 1)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    line_count = checkout.lines.count()

    total = calculations.calculate_checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )

    def delete_checkout_line(*args, **kwargs):
        checkout_with_item_on_promotion.lines.last().delete()

    # when
    with race_condition.RunBefore(
        "saleor.graphql.checkout.dataloaders.promotion_rule_infos.CheckoutLineByIdLoader.load_many",
        delete_checkout_line,
    ):
        with allow_writer():
            response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == line_count

    assert data["totalPrice"]["gross"]["amount"] == (total.gross.amount)
    assert data["subtotalPrice"]["gross"]["amount"] == (subtotal.gross.amount)
    line_info = lines[0]
    assert line_info.line.quantity > 0
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    assert data["lines"][0]["unitPrice"]["gross"]["amount"] == round(
        line_total_price.gross.amount / line_info.line.quantity, 2
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.variant.get_base_price(
        line_info.channel_listing,
        line_info.line.price_override,
    )
    undiscounted_total_price = undiscounted_unit_price.amount * line_info.line.quantity
    assert (
        data["lines"][0]["undiscountedUnitPrice"]["amount"]
        == undiscounted_unit_price.amount
    )
    assert (
        data["lines"][0]["undiscountedTotalPrice"]["amount"] == undiscounted_total_price
    )
    assert line_total_price.gross.amount < undiscounted_total_price


def test_checkout_display_gross_prices_use_default(user_api_client, checkout_with_item):
    # given
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    tax_config = checkout_with_item.channel.tax_configuration
    tax_config.country_exceptions.all().delete()

    # when
    response = user_api_client.post_graphql(QUERY_CHECKOUT_PRICES, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["displayGrossPrices"] == tax_config.display_gross_prices


@mock.patch(
    "saleor.checkout.calculations._calculate_and_add_tax",
    wraps=_calculate_and_add_tax,
)
@mock.patch(
    "saleor.checkout.calculations.fetch_checkout_data",
    wraps=fetch_checkout_data,
)
def test_checkout_prices_with_checkout_updated_during_price_recalculation(
    mock_fetch_checkout_data,
    mock_calculate_and_add_tax,
    user_api_client,
    checkout_with_prices,
):
    # given
    expected_email = "new_email@example.com"
    checkout = checkout_with_prices
    variables = {
        "id": to_global_id_or_none(checkout),
    }
    total_before_recalculation = checkout.total
    lines_before_recalculation = list(checkout.lines.all())
    freeze_time_str = "2024-01-01T12:00:00+00:00"

    # when
    def modify_checkout(*args, **kwargs):
        with freeze_time(freeze_time_str):
            with allow_writer():
                checkout_to_modify = Checkout.objects.get(pk=checkout.pk)
                checkout_to_modify.lines.update(quantity=F("quantity") + 1)
                checkout_to_modify.email = expected_email
                checkout_to_modify.save(update_fields=["email", "last_change"])

    with race_condition.RunAfter(
        "saleor.checkout.calculations._calculate_and_add_tax", modify_checkout
    ):
        response = user_api_client.post_graphql(QUERY_CHECKOUT_PRICES, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)

    # Ensure that the checkout prices recalculation was triggered more than one time
    assert mock_fetch_checkout_data.call_count > 1

    # Ensure that the checkout price are recalculated only one time
    assert mock_calculate_and_add_tax.call_count == 1

    checkout.refresh_from_db()
    assert checkout.email == expected_email
    assert checkout.last_change.isoformat() == freeze_time_str

    # Confirm that total price hasn't changed in database due to recalculation
    assert checkout.total == total_before_recalculation
    # Confirm that total price has changed in query response due to recalculation
    assert (
        data["totalPrice"]["gross"]["amount"] != total_before_recalculation.gross.amount
    )

    for line_before_recalculation, result_line, line in zip(
        lines_before_recalculation, data["lines"], checkout.lines.all(), strict=True
    ):
        # Confirm that returned line quantities are same as before simulated update was applied to the database
        assert line_before_recalculation.quantity == result_line["quantity"]
        # Confirm that line quantities have been updated in database
        assert line_before_recalculation.quantity + 1 == line.quantity


def test_checkout_display_gross_prices_use_country_exception(
    user_api_client, checkout_with_item
):
    # given
    variables = {"id": to_global_id_or_none(checkout_with_item)}
    tax_config = checkout_with_item.channel.tax_configuration
    tax_config.country_exceptions.all().delete()
    country_code = checkout_with_item.get_country()
    tax_country_config = tax_config.country_exceptions.create(
        country=country_code, display_gross_prices=False
    )

    # when
    response = user_api_client.post_graphql(QUERY_CHECKOUT_PRICES, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["displayGrossPrices"] == tax_country_config.display_gross_prices


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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.calculate_checkout_total(
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
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    assert data["lines"][0]["unitPrice"]["gross"]["amount"] == round(
        line_total_price.gross.amount / line_info.line.quantity, 2
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.variant.get_price(
        line_info.channel_listing,
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


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_prices_with_specific_voucher_when_line_without_listing(
    channel_listing_model,
    listing_filter_field,
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
):
    # given
    checkout = checkout_with_item_and_voucher_specific_products
    line_without_listing = checkout.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: line_without_listing.variant_id},
    ).delete()

    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == checkout.lines.count()
    response_api_line_without_listing = [
        line_data
        for line_data in data["lines"]
        if line_data["id"] == to_global_id_or_none(line_without_listing)
    ][0]
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.calculate_checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_info.shipping_address,
    )
    assert data["totalPrice"]["gross"]["amount"] == total.gross.amount
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_info.shipping_address,
    )
    assert data["subtotalPrice"]["gross"]["amount"] == subtotal.gross.amount
    line_info = lines[0]
    assert line_info.line.quantity > 0
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    assert response_api_line_without_listing["unitPrice"]["gross"]["amount"] == round(
        line_total_price.gross.amount / line_info.line.quantity, 2
    )
    assert (
        response_api_line_without_listing["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.undiscounted_unit_price
    undiscounted_line_total = undiscounted_unit_price * line_info.line.quantity
    assert line_total_price.gross < undiscounted_line_total
    assert (
        response_api_line_without_listing["undiscountedUnitPrice"]["amount"]
        == undiscounted_unit_price.amount
    )
    assert (
        response_api_line_without_listing["undiscountedTotalPrice"]["amount"]
        == undiscounted_line_total.amount
    )
    checkout_problems = data["problems"]
    assert len(checkout_problems) == 1
    assert (
        checkout_problems[0]["__typename"] == "CheckoutLineProblemVariantNotAvailable"
    )
    assert checkout_problems[0]["line"]["id"] == to_global_id_or_none(
        line_without_listing
    )
    assert len(response_api_line_without_listing["problems"]) == 1
    assert (
        response_api_line_without_listing["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
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
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total(
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
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
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
        line_info.channel_listing,
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


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_prices_with_voucher_once_per_order_when_line_without_listing(
    channel_listing_model,
    listing_filter_field,
    user_api_client,
    checkout_with_item_and_voucher_once_per_order,
):
    # given
    checkout = checkout_with_item_and_voucher_once_per_order

    line_without_listing = checkout.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: line_without_listing.variant_id},
    ).delete()

    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == checkout.lines.count()

    response_api_line_without_listing = [
        line_data
        for line_data in data["lines"]
        if line_data["id"] == to_global_id_or_none(line_without_listing)
    ][0]

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total(
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
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    assert response_api_line_without_listing["unitPrice"]["gross"]["amount"] == float(
        quantize_price(
            line_total_price.gross.amount / line_info.line.quantity, checkout.currency
        )
    )
    assert (
        response_api_line_without_listing["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.undiscounted_unit_price
    undiscounted_line_total = undiscounted_unit_price * line_info.line.quantity
    assert line_total_price.gross < undiscounted_line_total

    assert (
        response_api_line_without_listing["undiscountedUnitPrice"]["amount"]
        == undiscounted_unit_price.amount
    )
    assert (
        response_api_line_without_listing["undiscountedTotalPrice"]["amount"]
        == undiscounted_unit_price.amount * line_info.line.quantity
    )

    checkout_problems = data["problems"]
    assert len(checkout_problems) == 1
    assert (
        checkout_problems[0]["__typename"] == "CheckoutLineProblemVariantNotAvailable"
    )
    assert checkout_problems[0]["line"]["id"] == to_global_id_or_none(
        line_without_listing
    )
    assert len(response_api_line_without_listing["problems"]) == 1
    assert (
        response_api_line_without_listing["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )


def test_checkout_prices_with_voucher(user_api_client, checkout_with_item_and_voucher):
    # given
    checkout = checkout_with_item_and_voucher
    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == checkout.lines.count()
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total(
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
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
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
        line_info.channel_listing,
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


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_prices_with_voucher_when_line_without_listing(
    channel_listing_model,
    listing_filter_field,
    user_api_client,
    checkout_with_item_and_voucher,
):
    # given
    checkout = checkout_with_item_and_voucher

    line_without_listing = checkout.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: line_without_listing.variant_id},
    ).delete()

    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == checkout.lines.count()

    response_api_line_without_listing = [
        line_data
        for line_data in data["lines"]
        if line_data["id"] == to_global_id_or_none(line_without_listing)
    ][0]

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_info.shipping_address,
    )
    assert data["totalPrice"]["gross"]["amount"] == total.gross.amount
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_info.shipping_address,
    )
    assert data["subtotalPrice"]["gross"]["amount"] == subtotal.gross.amount
    line_info = lines[0]
    assert line_info.line.quantity > 0
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    assert response_api_line_without_listing["unitPrice"]["gross"]["amount"] == float(
        quantize_price(
            line_total_price.gross.amount / line_info.line.quantity, checkout.currency
        )
    )
    assert (
        response_api_line_without_listing["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.undiscounted_unit_price
    undiscounted_line_total = undiscounted_unit_price * line_info.line.quantity

    assert line_total_price.gross < undiscounted_line_total
    assert (
        response_api_line_without_listing["undiscountedUnitPrice"]["amount"]
        == undiscounted_unit_price.amount
    )
    assert (
        response_api_line_without_listing["undiscountedTotalPrice"]["amount"]
        == undiscounted_unit_price.amount * line_info.line.quantity
    )

    checkout_problems = data["problems"]
    assert len(checkout_problems) == 1
    assert (
        checkout_problems[0]["__typename"] == "CheckoutLineProblemVariantNotAvailable"
    )
    assert checkout_problems[0]["line"]["id"] == to_global_id_or_none(
        line_without_listing
    )
    assert len(response_api_line_without_listing["problems"]) == 1
    assert (
        response_api_line_without_listing["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )


def test_checkout_prices_with_voucher_code_that_doesnt_exist(
    user_api_client, checkout_with_item_and_voucher, voucher
):
    # given
    checkout = checkout_with_item_and_voucher
    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout)}
    voucher.delete()

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == checkout.lines.count()
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total(
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
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
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
        line_info.channel_listing,
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


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_prices_voucher_code_that_doesnt_exist_when_line_without_listing(
    channel_listing_model,
    listing_filter_field,
    user_api_client,
    checkout_with_item_and_voucher,
    voucher,
):
    # given
    checkout = checkout_with_item_and_voucher

    line_without_listing = checkout.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: line_without_listing.variant_id},
    ).delete()

    query = QUERY_CHECKOUT_PRICES
    variables = {"id": to_global_id_or_none(checkout)}
    voucher.delete()

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == checkout.lines.count()

    response_api_line_without_listing = [
        line_data
        for line_data in data["lines"]
        if line_data["id"] == to_global_id_or_none(line_without_listing)
    ][0]

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total(
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
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    assert response_api_line_without_listing["unitPrice"]["gross"]["amount"] == float(
        quantize_price(
            line_total_price.gross.amount / line_info.line.quantity, checkout.currency
        )
    )
    assert (
        response_api_line_without_listing["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    undiscounted_unit_price = line_info.undiscounted_unit_price

    assert (
        response_api_line_without_listing["undiscountedUnitPrice"]["amount"]
        == undiscounted_unit_price.amount
    )
    assert (
        response_api_line_without_listing["undiscountedTotalPrice"]["amount"]
        == undiscounted_unit_price.amount * line_info.line.quantity
    )
    assert undiscounted_unit_price * line_info.line.quantity == line_total_price.gross

    checkout_problems = data["problems"]
    assert len(checkout_problems) == 1
    assert (
        checkout_problems[0]["__typename"] == "CheckoutLineProblemVariantNotAvailable"
    )
    assert checkout_problems[0]["line"]["id"] == to_global_id_or_none(
        line_without_listing
    )
    assert len(response_api_line_without_listing["problems"]) == 1
    assert (
        response_api_line_without_listing["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )


def test_checkout_prices_variant_listing_price_changed(
    user_api_client, checkout_with_item
):
    # given
    query = QUERY_CHECKOUT_PRICES

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    calculations.fetch_checkout_data(
        checkout_info,
        manager,
        lines,
        force_update=True,
    )

    line = lines[0]
    listing = line.variant.channel_listings.get(
        channel_id=checkout_with_item.channel_id
    )
    price_amount = Decimal("2.00")
    listing.discounted_price_amount = price_amount
    listing.price_amount = price_amount
    listing.save(update_fields=["price_amount", "discounted_price_amount"])

    variables = {"id": to_global_id_or_none(checkout_with_item)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout_with_item.token)
    assert len(data["lines"]) == checkout_with_item.lines.count()

    total = calculations.calculate_checkout_total(
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
    )
    assert (
        data["lines"][0]["unitPrice"]["gross"]["amount"]
        == line_total_price.gross.amount / line_info.line.quantity
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    assert (
        data["lines"][0]["undiscountedUnitPrice"]["amount"]
        == line_info.line.undiscounted_unit_price_amount
    )
    assert (
        data["lines"][0]["undiscountedTotalPrice"]["amount"]
        == line_info.line.undiscounted_unit_price_amount * line_info.line.quantity
    )


def test_checkout_prices_expired_variant_listing_price_changed(
    user_api_client, checkout_with_item
):
    # given
    query = QUERY_CHECKOUT_PRICES

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    calculations.fetch_checkout_data(
        checkout_info,
        manager,
        lines,
        force_update=True,
    )
    checkout_with_item.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout_with_item.discount_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout_with_item.save(update_fields=["price_expiration", "discount_expiration"])

    line = lines[0]
    listing = line.variant.channel_listings.get(
        channel_id=checkout_with_item.channel_id
    )
    price_amount = Decimal("2.00")
    listing.discounted_price_amount = price_amount
    listing.price_amount = price_amount
    listing.save(update_fields=["price_amount", "discounted_price_amount"])

    variables = {"id": to_global_id_or_none(checkout_with_item)}

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout_with_item.token)
    assert len(data["lines"]) == checkout_with_item.lines.count()

    checkout_info.checkout.refresh_from_db()
    total = calculations.calculate_checkout_total(
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
    line_info.line.refresh_from_db()
    assert line_info.line.quantity > 0
    line_total_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=line_info,
    )
    assert (
        data["lines"][0]["unitPrice"]["gross"]["amount"]
        == line_total_price.gross.amount / line_info.line.quantity
    )
    assert (
        data["lines"][0]["totalPrice"]["gross"]["amount"]
        == line_total_price.gross.amount
    )
    assert (
        data["lines"][0]["undiscountedUnitPrice"]["amount"]
        == line_info.line.undiscounted_unit_price_amount
        == price_amount
    )
    assert (
        data["lines"][0]["undiscountedTotalPrice"]["amount"]
        == line_info.line.undiscounted_unit_price_amount * line_info.line.quantity
        == price_amount * line_info.line.quantity
    )


CHECKOUTS_QUERY = """
    {
        checkouts(first: 20) {
            edges {
                node {
                    token
                    totalPrice {
                        currency
                        gross {
                            amount
                        }
                    }
                }
            }
        }
    }
"""


CHECKOUTS_WITH_LINES_TOTAL_PRICE_QUERY = """
    {
        checkouts(first: 20) {
            edges {
                node {
                    token
                    lines{
                        totalPrice {
                            currency
                            gross {
                                amount
                            }
                        }
                    }
                }
            }
        }
    }
"""


def test_staff_user_can_query_checkouts_with_handle_payments_permission(
    checkout_with_item, staff_api_client, permission_manage_payments
):
    # given
    checkout = checkout_with_item

    # when
    response = staff_api_client.post_graphql(
        CHECKOUTS_QUERY,
        {},
        permissions=[permission_manage_payments],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    received_checkout = content["data"]["checkouts"]["edges"][0]["node"]
    assert str(checkout.token) == received_checkout["token"]


def test_app_can_query_checkouts_with_handle_payments_permission(
    checkout_with_item, app_api_client, permission_manage_payments
):
    # given
    checkout = checkout_with_item

    # when
    response = app_api_client.post_graphql(
        CHECKOUTS_QUERY,
        {},
        permissions=[permission_manage_payments],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    received_checkout = content["data"]["checkouts"]["edges"][0]["node"]
    assert str(checkout.token) == received_checkout["token"]


def test_query_checkouts(
    checkout_with_item, staff_api_client, permission_manage_checkouts
):
    # given
    checkout = checkout_with_item

    # when
    response = staff_api_client.post_graphql(
        CHECKOUTS_QUERY, {}, permissions=[permission_manage_checkouts]
    )

    # then
    content = get_graphql_content(response)
    received_checkout = content["data"]["checkouts"]["edges"][0]["node"]
    assert str(checkout.token) == received_checkout["token"]


@pytest.mark.parametrize(
    "query", [CHECKOUTS_QUERY, CHECKOUTS_WITH_LINES_TOTAL_PRICE_QUERY]
)
@mock.patch(
    "saleor.checkout.calculations._fetch_checkout_prices_if_expired",
    wraps=_fetch_checkout_prices_if_expired,
)
@mock.patch("saleor.checkout.calculations._calculate_and_add_tax")
def test_query_checkouts_do_not_trigger_sync_tax_webhooks(
    mocked_calculate_and_add_tax,
    mocked_fetch_checkout_prices_if_expired,
    query,
    checkout_with_item,
    staff_api_client,
    permission_manage_checkouts,
    tax_configuration_tax_app,
):
    # given
    checkout = checkout_with_item
    checkout.price_expiration = timezone.now()
    checkout.save()

    # when
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["checkouts"]["edges"])

    lines, _ = fetch_checkout_lines(checkout_with_item)

    mocked_calculate_and_add_tax.assert_not_called()
    mocked_fetch_checkout_prices_if_expired.assert_called_once_with(
        checkout_info=mock.ANY,
        allow_sync_webhooks=False,
        database_connection_name=mock.ANY,
        force_update=False,
        lines=lines,
        manager=mock.ANY,
        pregenerated_subscription_payloads=mock.ANY,
    )


@pytest.mark.parametrize(
    "query", [CHECKOUTS_QUERY, CHECKOUTS_WITH_LINES_TOTAL_PRICE_QUERY]
)
@mock.patch(
    "saleor.checkout.calculations._fetch_checkout_prices_if_expired",
    wraps=_fetch_checkout_prices_if_expired,
)
@mock.patch("saleor.checkout.calculations.update_checkout_prices_with_flat_rates")
def test_query_checkouts_calculate_flat_taxes(
    mocked_update_order_prices_with_flat_rates,
    mocked_fetch_checkout_prices_if_expired,
    query,
    checkout_with_item,
    staff_api_client,
    permission_manage_checkouts,
    tax_configuration_flat_rates,
):
    # given
    checkout = checkout_with_item
    checkout.price_expiration = timezone.now()
    checkout.save()

    # when
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["checkouts"]["edges"])

    lines, _ = fetch_checkout_lines(checkout_with_item)

    mocked_update_order_prices_with_flat_rates.assert_called_once_with(
        checkout_with_item,
        mock.ANY,
        lines,
        tax_configuration_flat_rates.prices_entered_with_tax,
        database_connection_name=mock.ANY,
    )
    mocked_fetch_checkout_prices_if_expired.assert_called_once_with(
        checkout_info=mock.ANY,
        allow_sync_webhooks=False,
        database_connection_name=mock.ANY,
        force_update=False,
        lines=lines,
        manager=mock.ANY,
        pregenerated_subscription_payloads=mock.ANY,
    )


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
    # when
    response = staff_api_client.post_graphql(
        CHECKOUTS_QUERY, {}, permissions=[permission_manage_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["checkouts"]["edges"]) == 5


CHECKOUT_LINES_WITH_TOTAL_PRICE = """
{
    checkoutLines(first: 20) {
        edges {
            node {
                id
                totalPrice {
                    currency
                    gross {
                        amount
                    }
                }
            }
        }
    }
}
"""


@mock.patch(
    "saleor.checkout.calculations._fetch_checkout_prices_if_expired",
    wraps=_fetch_checkout_prices_if_expired,
)
@mock.patch("saleor.checkout.calculations._calculate_and_add_tax")
def test_query_checkout_lines_do_not_trigger_sync_tax_webhooks(
    mocked_calculate_and_add_tax,
    mocked_fetch_checkout_prices_if_expired,
    checkout_with_item,
    staff_api_client,
    permission_manage_checkouts,
    tax_configuration_tax_app,
):
    # given
    checkout = checkout_with_item
    checkout.price_expiration = timezone.now()
    checkout.save()

    # when
    response = staff_api_client.post_graphql(
        CHECKOUT_LINES_WITH_TOTAL_PRICE, {}, permissions=[permission_manage_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["checkoutLines"]["edges"])

    lines, _ = fetch_checkout_lines(checkout_with_item)

    mocked_calculate_and_add_tax.assert_not_called()
    mocked_fetch_checkout_prices_if_expired.assert_called_once_with(
        checkout_info=mock.ANY,
        allow_sync_webhooks=False,
        database_connection_name=mock.ANY,
        force_update=False,
        lines=lines,
        manager=mock.ANY,
        pregenerated_subscription_payloads=mock.ANY,
    )


@mock.patch(
    "saleor.checkout.calculations._fetch_checkout_prices_if_expired",
    wraps=_fetch_checkout_prices_if_expired,
)
@mock.patch("saleor.checkout.calculations.update_checkout_prices_with_flat_rates")
def test_query_checkout_lines_calculate_flat_taxes(
    mocked_update_order_prices_with_flat_rates,
    mocked_fetch_checkout_prices_if_expired,
    checkout_with_item,
    staff_api_client,
    permission_manage_checkouts,
    tax_configuration_flat_rates,
):
    # given
    checkout = checkout_with_item
    checkout.price_expiration = timezone.now()
    checkout.save()

    # when
    response = staff_api_client.post_graphql(
        CHECKOUT_LINES_WITH_TOTAL_PRICE, {}, permissions=[permission_manage_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["checkoutLines"]["edges"])

    lines, _ = fetch_checkout_lines(checkout_with_item)

    mocked_update_order_prices_with_flat_rates.assert_called_once_with(
        checkout_with_item,
        mock.ANY,
        lines,
        tax_configuration_flat_rates.prices_entered_with_tax,
        database_connection_name=mock.ANY,
    )
    mocked_fetch_checkout_prices_if_expired.assert_called_once_with(
        checkout_info=mock.ANY,
        allow_sync_webhooks=False,
        database_connection_name=mock.ANY,
        force_update=False,
        lines=lines,
        manager=mock.ANY,
        pregenerated_subscription_payloads=mock.ANY,
    )


def test_query_checkout_lines(
    checkout_with_item, staff_api_client, permission_manage_checkouts
):
    query = """
    {
        checkoutLines(first: 20) {
            edges {
                node {
                    id
                    isGift
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
    is_gift_flags = [line["node"]["isGift"] for line in lines]
    assert all(item is False for item in is_gift_flags)


def test_query_checkout_lines_with_meta(
    checkout_with_item, staff_api_client, permission_manage_checkouts
):
    query = """
    {
        checkoutLines(first: 20) {
            edges {
                node {
                    id
                    metadata {
                        key
                        value
                    }
                    privateMetadata {
                        key
                        value
                    }
                }
            }
        }
    }
    """
    checkout = checkout_with_item
    items = list(checkout)

    metadata_key = "md key"
    metadata_value = "md value"

    for item in items:
        item.store_value_in_private_metadata({metadata_key: metadata_value})
        item.store_value_in_metadata({metadata_key: metadata_value})
        item.save()

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_checkouts]
    )
    content = get_graphql_content(response)
    lines = content["data"]["checkoutLines"]["edges"]
    expected_lines = [
        {
            "node": {
                "id": graphene.Node.to_global_id("CheckoutLine", item.pk),
                "metadata": [{"key": metadata_key, "value": metadata_value}],
                "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
            }
        }
        for item in items
    ]
    assert lines == expected_lines


def test_clean_checkout(
    checkout_with_item,
    payment_dummy,
    address,
    shipping_method,
    checkout_delivery,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    manager = get_plugins_manager(allow_replica=False)
    total = calculations.calculate_checkout_total(
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
        manager, checkout_info, lines, CheckoutErrorCode, last_payment=payment
    )


def test_clean_checkout_no_shipping_method(checkout_with_item, address):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    with pytest.raises(ValidationError) as e:
        clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)

    msg = "Shipping method is not set"
    assert e.value.error_dict["shipping_method"][0].message == msg


def test_clean_checkout_no_shipping_address(
    checkout_with_item, shipping_method, checkout_delivery
):
    checkout = checkout_with_item
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    with pytest.raises(ValidationError) as e:
        clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)
    msg = "Shipping address is not set"
    assert e.value.error_dict["shipping_address"][0].message == msg


def test_clean_checkout_invalid_shipping_method(
    checkout_with_item,
    address,
    shipping_zone_without_countries,
    checkout_delivery,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    shipping_method = shipping_zone_without_countries.shipping_methods.first()
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.save()
    checkout.assigned_delivery.is_valid = False
    checkout.assigned_delivery.save(update_fields=["is_valid"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
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
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    with pytest.raises(ValidationError) as e:
        clean_checkout_payment(
            manager, checkout_info, lines, CheckoutErrorCode, last_payment=payment
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
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    with pytest.raises(ValidationError) as e:
        clean_checkout_payment(
            manager, checkout_info, lines, CheckoutErrorCode, last_payment=payment
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
        name="Credit card",
        psp_reference="123",
        currency="USD",
        authorized_value=Decimal(15),
        available_actions=[TransactionAction.CHARGE, TransactionAction.CANCEL],
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
        name="Credit card",
        psp_reference="123",
        currency="USD",
        authorized_value=Decimal(15),
        available_actions=[TransactionAction.CHARGE, TransactionAction.CANCEL],
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
        "TransactionItem", transaction.token
    )


def test_checkout_transactions_with_handle_payments(
    staff_api_client, checkout, permission_manage_payments
):
    # given
    transaction = checkout.payment_transactions.create(
        name="Credit card",
        psp_reference="123",
        currency="USD",
        authorized_value=Decimal(15),
        available_actions=[TransactionAction.CHARGE, TransactionAction.CANCEL],
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
        "TransactionItem", transaction.token
    )


QUERY_CHECKOUT_STATUSES_AND_BALANCE = """
query getCheckout($id: ID) {
  checkout(id: $id) {
    updatedAt
    chargeStatus
    authorizeStatus
    totalBalance {
      currency
      amount
    }
  }
}
"""


def test_checkout_payment_statuses(
    user_api_client,
    checkout_with_prices,
):
    # given
    checkout_with_prices.payment_transactions.create(
        name="Credit card",
        psp_reference="123",
        currency="USD",
        authorized_value=Decimal(15),
        charged_value=Decimal(5),
        charge_pending_value=Decimal(6),
        available_actions=[TransactionAction.CHARGE, TransactionAction.CANCEL],
    )
    query = QUERY_CHECKOUT_STATUSES_AND_BALANCE
    variables = {"id": to_global_id_or_none(checkout_with_prices)}

    # when
    response = user_api_client.post_graphql(
        query,
        variables,
    )

    # then
    checkout_with_prices.refresh_from_db()
    content = get_graphql_content(response)
    assert (
        content["data"]["checkout"]["chargeStatus"]
        == CheckoutChargeStatusEnum.PARTIAL.name
    )
    assert (
        content["data"]["checkout"]["authorizeStatus"]
        == CheckoutAuthorizeStatusEnum.PARTIAL.name
    )


def test_checkout_balance(
    user_api_client,
    checkout_with_prices,
):
    # given
    transaction = checkout_with_prices.payment_transactions.create(
        name="Credit card",
        psp_reference="123",
        currency="USD",
        authorized_value=Decimal(15),
        charged_value=Decimal(5),
        charge_pending_value=Decimal(6),
        available_actions=[TransactionAction.CHARGE, TransactionAction.CANCEL],
    )
    query = QUERY_CHECKOUT_STATUSES_AND_BALANCE
    variables = {"id": to_global_id_or_none(checkout_with_prices)}

    # when
    response = user_api_client.post_graphql(
        query,
        variables,
    )

    # then
    checkout_with_prices.refresh_from_db()
    content = get_graphql_content(response)
    assert (
        content["data"]["checkout"]["totalBalance"]["amount"]
        == transaction.charged_value
        + transaction.charge_pending_value
        - checkout_with_prices.total.gross.amount
    )


def test_checkout_metadata(checkout, user_api_client):
    # given
    checkout.metadata_storage.metadata = {"foo": "bar"}
    checkout.metadata_storage.save()

    query = """
        query getCheckout($id: ID) {
            checkout(id: $id) {
                metadata {
                    key
                    value
                }
                foo: metafield(key: "foo")
                nonexistent: metafield(key: "nonexistent")
                metafields
            }
        }
    """
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["metadata"] == [{"key": "foo", "value": "bar"}]
    assert content["data"]["checkout"]["foo"] == "bar"
    assert content["data"]["checkout"]["nonexistent"] is None
    assert content["data"]["checkout"]["metafields"] == {"foo": "bar"}


def test_checkout_no_metadata(checkout, user_api_client):
    # given
    checkout.metadata_storage.delete()

    query = """
        query getCheckout($id: ID) {
            checkout(id: $id) {
                metadata {
                    key
                    value
                }
                metafield(key: "foo")
                metafields
            }
        }
    """
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["metadata"] == []
    assert content["data"]["checkout"]["metafield"] is None
    assert content["data"]["checkout"]["metafields"] == {}


QUERY_CHECKOUT_STORED_PAYMENT_METHODS = """
query getCheckout($id: ID, $amount: PositiveDecimal) {
  checkout(id: $id) {
    storedPaymentMethods(amount: $amount){
      id
      gateway{
        name
        id
        config{
          field
          value
        }
        currencies
      }
      paymentMethodId
      creditCardInfo{
        brand
        firstDigits
        lastDigits
        expMonth
        expYear
      }
      supportedPaymentFlows
      type
      name
      data
    }
  }
}
"""


@mock.patch("saleor.plugins.manager.PluginsManager.list_stored_payment_methods")
def test_checkout_with_stored_payment_methods_empty_response(
    mocked_list_stored_payment_methods,
    user_api_client,
    checkout_with_prices,
):
    # given
    checkout_with_prices.user = user_api_client.user
    checkout_with_prices.save(update_fields=["user"])

    mocked_list_stored_payment_methods.return_value = []
    query = QUERY_CHECKOUT_STORED_PAYMENT_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_prices)}

    request_data = ListStoredPaymentMethodsRequestData(
        user=checkout_with_prices.user,
        channel=checkout_with_prices.channel,
    )

    # when
    response = user_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response)

    mocked_list_stored_payment_methods.assert_called_once_with(request_data)
    assert content["data"]["checkout"]["storedPaymentMethods"] == []


@mock.patch("saleor.plugins.manager.PluginsManager.list_stored_payment_methods")
def test_checkout_with_stored_payment_methods(
    mocked_list_stored_payment_methods,
    user_api_client,
    checkout_with_prices,
):
    # given
    checkout_with_prices.user = user_api_client.user
    checkout_with_prices.save(update_fields=["user"])

    payment_method_id = "app:payment-method-id"
    external_id = "payment-method-id"
    supported_payment_flow = TokenizedPaymentFlowEnum.INTERACTIVE
    payment_method_type = "credit-card"
    payment_method_name = "Payment method name"
    payment_method_data = {"additional_data": "value"}

    payment_gateway_id = "gateway-id"
    payment_gateway_name = "gateway-name"

    credit_card_brand = "brand"
    credit_card_first_digits = "123"
    credit_card_last_digits = "456"
    credit_card_exp_month = 1
    credit_card_exp_year = 2021

    mocked_list_stored_payment_methods.return_value = [
        PaymentMethodData(
            id=payment_method_id,
            external_id=external_id,
            supported_payment_flows=[supported_payment_flow.value],
            type=payment_method_type,
            credit_card_info=PaymentMethodCreditCardInfo(
                brand=credit_card_brand,
                first_digits=credit_card_first_digits,
                last_digits=credit_card_last_digits,
                exp_month=credit_card_exp_month,
                exp_year=credit_card_exp_year,
            ),
            name=payment_method_name,
            data=payment_method_data,
            gateway=PaymentGateway(
                id=payment_gateway_id,
                name=payment_gateway_name,
                currencies=[checkout_with_prices.currency],
                config=[],
            ),
        )
    ]

    query = QUERY_CHECKOUT_STORED_PAYMENT_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_prices)}

    request_data = ListStoredPaymentMethodsRequestData(
        user=checkout_with_prices.user,
        channel=checkout_with_prices.channel,
    )

    # when
    response = user_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response)

    mocked_list_stored_payment_methods.assert_called_once_with(request_data)
    assert content["data"]["checkout"]["storedPaymentMethods"] == [
        {
            "id": payment_method_id,
            "gateway": {
                "name": payment_gateway_name,
                "id": payment_gateway_id,
                "config": [],
                "currencies": [checkout_with_prices.currency],
            },
            "paymentMethodId": external_id,
            "creditCardInfo": {
                "brand": credit_card_brand,
                "firstDigits": credit_card_first_digits,
                "lastDigits": credit_card_last_digits,
                "expMonth": credit_card_exp_month,
                "expYear": credit_card_exp_year,
            },
            "supportedPaymentFlows": [supported_payment_flow.name],
            "type": payment_method_type,
            "name": payment_method_name,
            "data": payment_method_data,
        }
    ]


@mock.patch("saleor.plugins.manager.PluginsManager.list_stored_payment_methods")
def test_checkout_with_stored_payment_methods_requested_by_staff_user(
    mocked_list_stored_payment_methods,
    staff_api_client,
    checkout_with_prices,
    customer_user2,
    permission_manage_checkouts,
    permission_manage_users,
):
    # given
    checkout_with_prices.user = customer_user2
    checkout_with_prices.save(update_fields=["user"])

    staff_api_client.user.user_permissions.add(permission_manage_checkouts)

    mocked_list_stored_payment_methods.return_value = []
    query = QUERY_CHECKOUT_STORED_PAYMENT_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_prices)}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    assert customer_user2 != staff_api_client.user

    content = get_graphql_content(response)

    assert not mocked_list_stored_payment_methods.called
    assert content["data"]["checkout"]["storedPaymentMethods"] == []


@mock.patch("saleor.plugins.manager.PluginsManager.list_stored_payment_methods")
def test_checkout_with_stored_payment_methods_requested_by_app(
    mocked_list_stored_payment_methods,
    app_api_client,
    checkout_with_prices,
    customer_user2,
    permission_manage_checkouts,
    permission_manage_users,
):
    # given
    app = app_api_client.app
    app.permissions.add(
        permission_manage_checkouts,
        permission_manage_users,
    )
    checkout_with_prices.user = customer_user2
    checkout_with_prices.save(update_fields=["user"])

    mocked_list_stored_payment_methods.return_value = []
    query = QUERY_CHECKOUT_STORED_PAYMENT_METHODS
    variables = {"id": to_global_id_or_none(checkout_with_prices)}

    # when
    response = app_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response)

    assert not mocked_list_stored_payment_methods.called
    assert content["data"]["checkout"]["storedPaymentMethods"] == []


CHECKOUT_WITH_VOUCHER_QUERY = """
query getCheckout($id: ID) {
    checkout(id: $id) {
        voucher {
            id
            code
            name
        }
    }
}
"""


def test_query_checkout_voucher(
    staff_api_client,
    checkout_with_voucher_free_shipping,
    permission_manage_discounts,
    voucher_free_shipping,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_discounts)
    query = CHECKOUT_WITH_VOUCHER_QUERY
    checkout = checkout_with_voucher_free_shipping
    voucher = voucher_free_shipping
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    voucher_data = content["data"]["checkout"]["voucher"]
    assert voucher_data["id"] == to_global_id_or_none(voucher)
    assert voucher_data["code"] == voucher.code
    assert voucher_data["name"] == voucher.name


def test_query_checkout_voucher_by_customer_no_permission(
    user_api_client,
    checkout_with_voucher_free_shipping,
    voucher_free_shipping,
):
    # given
    query = CHECKOUT_WITH_VOUCHER_QUERY
    checkout = checkout_with_voucher_free_shipping
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


CHECKOUT_EMAIL_QUERY = """
query getCheckout($id: ID) {
    checkout(id: $id) {
        email
    }
}
"""


def test_query_checkout_email_for_anonymous_user_without_email(
    user_api_client,
    checkout_with_item,
):
    # given
    checkout = checkout_with_item
    checkout.user = None
    checkout.email = None
    checkout.save(update_fields=["email", "user"])

    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(CHECKOUT_EMAIL_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["email"] is None


def test_query_checkout_email_for_anonymous_user(
    user_api_client,
    checkout_with_item,
):
    # given
    expected_email = "expected@example.com"

    checkout = checkout_with_item
    assert checkout.user is None
    checkout.email = expected_email
    checkout.save(update_fields=["email"])

    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(CHECKOUT_EMAIL_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["email"] == expected_email


def test_query_checkout_email_with_explicit_email_for_authenticated_user(
    user_api_client,
    checkout_with_item,
):
    # given
    expected_email = "expected@example.com"

    checkout = checkout_with_item
    checkout.user = user_api_client.user
    checkout.email = expected_email
    checkout.save(update_fields=["user", "email"])

    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(CHECKOUT_EMAIL_QUERY, variables)

    # then
    content = get_graphql_content(response)
    # Return the email explicitly assigned to the user
    assert content["data"]["checkout"]["email"] == expected_email


@freezegun.freeze_time("2023-01-01 12:00:00")
def test_query_checkout_delivery_method_invalidates_taxes_when_delivery_price_is_changed(
    user_api_client, checkout_with_item, checkout_delivery, shipping_method, address
):
    # This test confirms that any change in the price of assigned delivery method
    # will invalidate checkout prices and taxes even when shipping method is not changed.
    # This confirms that the `deliveryMethod` field behaves the same way as before
    # denormalizing deliveries on DB side.

    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)

    checkout.price_expiration = timezone.now() + datetime.timedelta(minutes=5)
    checkout.delivery_methods_stale_at = timezone.now() - datetime.timedelta(minutes=5)
    checkout.save()

    current_checkout_delivery_price = checkout.assigned_delivery.price_amount

    # Change shipping method price
    shipping_method.channel_listings.all().update(
        price_amount=current_checkout_delivery_price + 10
    )

    variables = {"id": to_global_id_or_none(checkout)}

    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            deliveryMethod {
                ... on ShippingMethod{
                  id
                }
            }
        }
    }
    """

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    assert checkout.price_expiration == timezone.now()
    assert content["data"]["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        shipping_method
    )


@freezegun.freeze_time("2023-01-01 12:00:00")
def test_query_checkout_delivery_method_invalidates_taxes_when_delivery_tax_class_is_changed(
    user_api_client,
    checkout_with_item,
    checkout_delivery,
    shipping_method,
    address,
    tax_class_zero_rates,
):
    # This test confirms that any change in the tax class of assigned delivery method
    # will invalidate checkout prices and taxes even when shipping method is not changed.
    # This confirms that the `deliveryMethod` field behaves the same way as before
    # denormalizing deliveries on DB side.

    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.delivery_methods_stale_at = timezone.now() - datetime.timedelta(minutes=5)
    checkout.price_expiration = timezone.now() + datetime.timedelta(minutes=5)
    checkout.save()

    # Change tax class of shipping
    assert shipping_method.tax_class != tax_class_zero_rates
    shipping_method.tax_class = tax_class_zero_rates
    shipping_method.save(update_fields=["tax_class"])

    variables = {"id": to_global_id_or_none(checkout)}

    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            deliveryMethod {
                ... on ShippingMethod{
                  id
                }
            }
        }
    }
    """

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    assert checkout.price_expiration == timezone.now()
    assert content["data"]["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        shipping_method
    )


@freezegun.freeze_time("2023-01-01 12:00:00")
def test_query_checkout_delivery_method_dont_invalidate_taxes_when_nothing_changed(
    user_api_client,
    checkout_with_item,
    checkout_delivery,
    shipping_method,
    address,
):
    # This test confirms that no change in the assigned delivery method
    # will not trigger invalidation of checkout prices and taxes.
    # This confirms that the `deliveryMethod` field behaves the same way as before
    # denormalizing deliveries on DB side.

    # given
    expected_price_expiration = timezone.now() + datetime.timedelta(minutes=5)

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.delivery_methods_stale_at = timezone.now() - datetime.timedelta(minutes=5)
    checkout.price_expiration = expected_price_expiration
    checkout.save()

    variables = {"id": to_global_id_or_none(checkout)}

    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            deliveryMethod {
                ... on ShippingMethod{
                  id
                }
            }
        }
    }
    """

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    assert checkout.price_expiration == expected_price_expiration
    assert content["data"]["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        shipping_method
    )


@freezegun.freeze_time("2023-01-01 12:00:00")
def test_query_checkout_shipping_method_invalidates_taxes_when_shipping_price_is_changed(
    user_api_client, checkout_with_item, checkout_delivery, shipping_method, address
):
    # This test confirms that any change in the price of assigned delivery method
    # will invalidate checkout prices and taxes even when shipping method is not changed.
    # This confirms that the `shippingMethod` field behaves the same way as before
    # denormalizing deliveries on DB side.

    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)

    checkout.price_expiration = timezone.now() + datetime.timedelta(minutes=5)
    checkout.delivery_methods_stale_at = timezone.now() - datetime.timedelta(minutes=5)
    checkout.save()

    current_checkout_delivery_price = checkout.assigned_delivery.price_amount

    # Change shipping method price
    shipping_method.channel_listings.all().update(
        price_amount=current_checkout_delivery_price + 10
    )

    variables = {"id": to_global_id_or_none(checkout)}

    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            shippingMethod {
                id
            }
        }
    }
    """

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    assert checkout.price_expiration == timezone.now()
    assert content["data"]["checkout"]["shippingMethod"]["id"] == to_global_id_or_none(
        shipping_method
    )


@freezegun.freeze_time("2023-01-01 12:00:00")
def test_query_checkout_shipping_method_invalidates_taxes_when_shipping_tax_class_is_changed(
    user_api_client,
    checkout_with_item,
    checkout_delivery,
    shipping_method,
    address,
    tax_class_zero_rates,
):
    # This test confirms that any change in the tax class of assigned delivery method
    # will invalidate checkout prices and taxes even when shipping method is not changed.
    # This confirms that the `shippingMethod` field behaves the same way as before
    # denormalizing deliveries on DB side.

    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.delivery_methods_stale_at = timezone.now() - datetime.timedelta(minutes=5)
    checkout.price_expiration = timezone.now() + datetime.timedelta(minutes=5)
    checkout.save()

    # Change tax class of shipping
    assert shipping_method.tax_class != tax_class_zero_rates
    shipping_method.tax_class = tax_class_zero_rates
    shipping_method.save(update_fields=["tax_class"])

    variables = {"id": to_global_id_or_none(checkout)}

    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            shippingMethod {
                id
            }
        }
    }
    """

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    assert checkout.price_expiration == timezone.now()
    assert content["data"]["checkout"]["shippingMethod"]["id"] == to_global_id_or_none(
        shipping_method
    )


@freezegun.freeze_time("2023-01-01 12:00:00")
def test_query_checkout_shipping_method_dont_invalidate_taxes_when_nothing_changed(
    user_api_client,
    checkout_with_item,
    checkout_delivery,
    shipping_method,
    address,
):
    # This test confirms that no change in the assigned delivery method
    # will not trigger invalidation of checkout prices and taxes.
    # This confirms that the `shippingMethod` field behaves the same way as before
    # denormalizing deliveries on DB side.

    # given
    expected_price_expiration = timezone.now() + datetime.timedelta(minutes=5)

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.delivery_methods_stale_at = timezone.now() - datetime.timedelta(minutes=5)
    checkout.price_expiration = expected_price_expiration
    checkout.save()

    variables = {"id": to_global_id_or_none(checkout)}

    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            shippingMethod {
                id
            }
        }
    }
    """

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    assert checkout.price_expiration == expected_price_expiration
    assert content["data"]["checkout"]["shippingMethod"]["id"] == to_global_id_or_none(
        shipping_method
    )


def test_checkout_delivery_returns_external_shipping_methods(
    user_api_client, checkout_with_delivery_method_for_external_shipping
):
    # given
    checkout = checkout_with_delivery_method_for_external_shipping
    delivery = checkout.assigned_delivery

    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            delivery {
                id
                shippingMethod {
                    id
                    name
                }
            }
        }
    }
    """
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkout"]["delivery"]
    assert data is not None
    assert data["id"] == to_global_id_or_none(delivery)
    assert data["shippingMethod"]["name"] == delivery.name


def test_checkout_delivery_returns_built_in_shipping_methods(
    user_api_client, checkout_with_item, checkout_delivery, shipping_method, address
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.save()

    delivery = checkout.assigned_delivery

    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            delivery {
                id
                shippingMethod {
                    id
                    name
                }
            }
        }
    }
    """
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkout"]["delivery"]
    assert data is not None
    assert data["id"] == to_global_id_or_none(delivery)
    assert data["shippingMethod"]["name"] == shipping_method.name


def test_checkout_delivery_returns_none_when_no_delivery_assigned(
    user_api_client, checkout_with_item
):
    # given
    checkout = checkout_with_item
    assert checkout.assigned_delivery_id is None

    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            delivery {
                id
                shippingMethod {
                    id
                    name
                }
            }
        }
    }
    """
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["delivery"] is None


@freezegun.freeze_time("2023-01-01 12:00:00")
@mock.patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.get_shipping_methods_for_checkout"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_delivery_do_not_trigger_any_webhook_calls(
    mocked_shipping_webhook_fetch,
    user_api_client,
    checkout_with_item,
    checkout_delivery,
    shipping_method,
    address,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.delivery_methods_stale_at = timezone.now()
    checkout.save()

    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            delivery {
                id
                shippingMethod {
                    id
                    name
                }
            }
        }
    }
    """
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["delivery"] is not None
    # Ensure no webhook was triggered
    mocked_shipping_webhook_fetch.assert_not_called()


@mock.patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.get_shipping_methods_for_checkout"
)
def test_checkout_delivery_returns_shipping_when_marked_as_invalid(
    mocked_shipping_webhook_fetch,
    user_api_client,
    checkout_with_item,
    checkout_delivery,
    shipping_method,
    address,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.save()

    delivery = checkout.assigned_delivery
    # Mark the delivery as invalid
    delivery.is_valid = False
    delivery.save(update_fields=["is_valid"])

    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            delivery {
                id
                shippingMethod {
                    id
                    name
                }
            }
        }
    }
    """
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkout"]["delivery"]
    # The delivery field should still return the delivery object even when marked as invalid
    assert data is not None
    assert data["id"] == to_global_id_or_none(delivery)
    assert data["shippingMethod"]["name"] == shipping_method.name
    mocked_shipping_webhook_fetch.assert_not_called()
