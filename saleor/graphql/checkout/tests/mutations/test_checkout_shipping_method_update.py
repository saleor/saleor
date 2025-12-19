from datetime import timedelta
from decimal import Decimal
from unittest import mock
from unittest.mock import ANY, patch

import graphene
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from .....account.models import Address
from .....checkout.actions import call_checkout_info_event
from .....checkout.calculations import fetch_checkout_data
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import (
    fetch_checkout_info,
    fetch_checkout_lines,
    get_or_fetch_checkout_deliveries,
)
from .....checkout.models import CheckoutDelivery
from .....checkout.utils import PRIVATE_META_APP_SHIPPING_ID, invalidate_checkout
from .....core.models import EventDelivery
from .....plugins.base_plugin import ExcludedShippingMethod
from .....plugins.manager import get_plugins_manager
from .....shipping import models as shipping_models
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_UPDATE_SHIPPING_METHOD = """
    mutation checkoutShippingMethodUpdate($id: ID, $shippingMethodId: ID) {
      checkoutShippingMethodUpdate(id: $id, shippingMethodId: $shippingMethodId) {
        errors {
          field
          message
          code
        }
        checkout {
          token
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
      }
    }
"""


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "get_or_fetch_checkout_deliveries",
    wraps=get_or_fetch_checkout_deliveries,
)
@patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_method_update(
    mocked_invalidate_checkout,
    mock_get_or_fetch_checkout_deliveries,
    staff_api_client,
    shipping_method,
    checkout_with_item_and_shipping_method,
):
    # given
    checkout = checkout_with_item_and_shipping_method
    query = MUTATION_UPDATE_SHIPPING_METHOD
    previous_last_change = checkout.last_change

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = staff_api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "shippingMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    checkout.refresh_from_db()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mock_get_or_fetch_checkout_deliveries.assert_called_once_with(
        checkout_info,
    )
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["token"] == str(checkout.token)
    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout.call_count == 1


@freeze_time("2023-01-01 12:00:00")
@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "get_or_fetch_checkout_deliveries",
    wraps=get_or_fetch_checkout_deliveries,
)
@patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_method_update_not_valid_shipping_method(
    mocked_invalidate_checkout,
    mock_get_or_fetch_checkout_deliveries,
    staff_api_client,
    other_shipping_method,
    checkout_with_item_and_shipping_method,
):
    # given
    checkout = checkout_with_item_and_shipping_method
    checkout.delivery_methods_stale_at = timezone.now() + timedelta(minutes=10)
    checkout.save(update_fields=["delivery_methods_stale_at"])

    old_shipping_method = checkout.assigned_delivery
    previous_last_change = checkout.last_change

    query = MUTATION_UPDATE_SHIPPING_METHOD

    # other_shipping_method is not present in denormalized checkout shipping methods
    method_id = graphene.Node.to_global_id("ShippingMethod", other_shipping_method.id)

    # when
    response = staff_api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "shippingMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    checkout.refresh_from_db()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mock_get_or_fetch_checkout_deliveries.assert_called_once_with(
        checkout_info,
    )
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert checkout.assigned_delivery == old_shipping_method
    assert checkout.last_change == previous_last_change


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
    method_price = Decimal(10)
    method_name = "Provider - Economy"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": method_name,
            "amount": method_price,
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    fetch_checkout_data(
        checkout_info,
        manager,
        lines,
    )
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["token"] == str(checkout_with_item.token)

    assert checkout.assigned_delivery.shipping_method_id == method_id
    assert checkout.undiscounted_base_shipping_price_amount == method_price
    assert checkout.shipping_method_name == method_name
    assert (
        PRIVATE_META_APP_SHIPPING_ID not in checkout.metadata_storage.private_metadata
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_shipping_method_update_deletes_external_shipping_when_not_valid(
    mock_send_request,
    staff_api_client,
    address,
    checkout_with_item,
    shipping_app,
    channel_USD,
    settings,
    shipping_method,
):
    # given
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

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    checkout.metadata_storage.private_metadata = {
        PRIVATE_META_APP_SHIPPING_ID: graphene.Node.to_global_id(
            "app", f"{shipping_app.id}:{response_method_id}"
        )
    }
    checkout.metadata_storage.save()

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]
    assert not errors
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert (
        PRIVATE_META_APP_SHIPPING_ID not in checkout.metadata_storage.private_metadata
    )


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
    webhook_reason = "disabled by webhook"
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
    assert checkout.assigned_delivery is None
    assert checkout.undiscounted_base_shipping_price_amount == Decimal(0)
    assert checkout.shipping_method_name is None


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
    assert checkout.assigned_delivery is None
    assert checkout.undiscounted_base_shipping_price_amount == Decimal(0)
    assert checkout.shipping_method_name is None
    assert (
        mock_is_shipping_method_available.call_count
        == shipping_models.ShippingMethod.objects.count()
    )


def test_checkout_shipping_method_update_with_not_all_required_shipping_address_data(
    staff_api_client,
    shipping_method,
    checkout_with_item,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = Address.objects.create(country="US")
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD

    shipping_method.postal_code_rules.create(start="00123", end="12345")
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    fetch_checkout_data(
        checkout_info,
        manager,
        lines,
    )

    assert not data["errors"]
    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)
    assert (
        checkout.undiscounted_base_shipping_price_amount
        == shipping_method.channel_listings.get().price_amount
    )
    assert checkout.shipping_method_name == shipping_method.name


def test_checkout_shipping_method_update_with_not_valid_shipping_address_data(
    staff_api_client,
    shipping_method,
    checkout_with_item,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = Address.objects.create(
        country="US",
        city="New York",
        city_area="ABC",
        street_address_1="New street",
        postal_code="53-601",
    )  # incorrect postalCode
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD

    shipping_method.postal_code_rules.create(start="00123", end="12345")
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    fetch_checkout_data(
        checkout_info,
        manager,
        lines,
    )

    assert not data["errors"]
    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)
    assert (
        checkout.undiscounted_base_shipping_price_amount
        == shipping_method.channel_listings.get().price_amount
    )
    assert checkout.shipping_method_name == shipping_method.name


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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    fetch_checkout_data(
        checkout_info,
        manager,
        lines,
    )

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert checkout.assigned_delivery is None
    assert checkout.undiscounted_base_shipping_price_amount == Decimal(0)
    assert checkout.shipping_method_name is None


def test_checkout_update_shipping_method_with_digital(
    api_client, checkout_with_digital_item, address, shipping_method
):
    """Test updating the shipping method of a digital order throws an error."""

    checkout = checkout_with_digital_item
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.pk)
    variables = {"id": to_global_id_or_none(checkout), "shippingMethodId": method_id}

    # Put a shipping address, to ensure it is still handled properly
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    response = api_client.post_graphql(MUTATION_UPDATE_SHIPPING_METHOD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingMethodUpdate"]

    assert data["errors"] == [
        {
            "field": "shippingMethod",
            "message": "This checkout doesn't need shipping",
            "code": CheckoutErrorCode.SHIPPING_NOT_REQUIRED.name,
        }
    ]

    # Ensure the shipping method was unchanged
    checkout.refresh_from_db()
    assert checkout.assigned_delivery is None
    assert checkout.undiscounted_base_shipping_price_amount == Decimal(0)
    assert checkout.shipping_method_name is None


def test_with_active_problems_flow(
    api_client,
    checkout_with_problems,
    shipping_method,
):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {
            "id": to_global_id_or_none(checkout_with_problems),
            "shippingMethodId": method_id,
        },
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutShippingMethodUpdate"]["errors"]


MUTATION_UPDATE_SHIPPING_METHOD_WITH_ONLY_ID = """
    mutation checkoutShippingMethodUpdate($id: ID, $shippingMethodId: ID) {
      checkoutShippingMethodUpdate(id: $id, shippingMethodId: $shippingMethodId) {
        errors {
          field
          message
          code
        }
        checkout {
          id
        }
      }
    }
"""


@patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_shipping_method_update_triggers_webhooks(
    mocked_generate_deferred_payloads,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_info_event,
    setup_checkout_webhooks,
    settings,
    address,
    api_client,
    checkout_with_items,
    shipping_method,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    checkout_with_items.shipping_address = address
    checkout_with_items.save(update_fields=["shipping_address"])
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD_WITH_ONLY_ID,
        {
            "id": to_global_id_or_none(checkout_with_items),
            "shippingMethodId": method_id,
        },
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutShippingMethodUpdate"]["errors"]

    assert wrapped_call_checkout_info_event.called

    # confirm that event delivery was generated for each async webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )

    mocked_generate_deferred_payloads.assert_called_once_with(
        kwargs={
            "event_delivery_ids": [checkout_update_delivery.id],
            "deferred_payload_data": {
                "model_name": "checkout.checkout",
                "object_id": checkout_with_items.pk,
                "requestor_model_name": None,
                "requestor_object_id": None,
                "request_time": None,
            },
            "send_webhook_queue": settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            "telemetry_context": ANY,
        },
        MessageGroupId="example.com",
    )

    # Deferred payload covers the async actions
    assert not mocked_send_webhook_request_async.called

    sync_deliveries = {
        call.args[0].event_type: call.args[0]
        for call in mocked_send_webhook_request_sync.mock_calls
    }

    assert WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT in sync_deliveries
    shipping_methods_delivery = sync_deliveries[
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    ]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id

    assert WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS in sync_deliveries
    filter_shipping_delivery = sync_deliveries[
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    ]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id

    assert WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES not in sync_deliveries


@patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_shipping_method_update_to_none_triggers_webhooks(
    mocked_generate_deferred_payloads,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_info_event,
    setup_checkout_webhooks,
    settings,
    address,
    api_client,
    checkout_with_items,
    checkout_delivery,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    checkout_with_items.shipping_address = address
    checkout_with_items.assigned_delivery = checkout_delivery(checkout_with_items)
    checkout_with_items.save(update_fields=["shipping_address", "assigned_delivery"])

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD_WITH_ONLY_ID,
        {
            "id": to_global_id_or_none(checkout_with_items),
            "shippingMethodId": None,
        },
    )

    # then

    content = get_graphql_content(response)

    assert not content["data"]["checkoutShippingMethodUpdate"]["errors"]

    assert wrapped_call_checkout_info_event.called

    # confirm that event delivery was generated for each async webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )

    mocked_generate_deferred_payloads.assert_called_once_with(
        kwargs={
            "event_delivery_ids": [checkout_update_delivery.id],
            "deferred_payload_data": {
                "model_name": "checkout.checkout",
                "object_id": checkout_with_items.pk,
                "requestor_model_name": None,
                "requestor_object_id": None,
                "request_time": None,
            },
            "send_webhook_queue": settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            "telemetry_context": ANY,
        },
        MessageGroupId="example.com",
    )

    # Deferred payload covers the sync and async actions
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_method_update_from_external_shipping_to_different_external(
    mocked_invalidate_checkout,
    mocked_send_webhook_request_sync,
    mocked_call_checkout_info_event,
    settings,
    shipping_app,
    checkout_with_delivery_method_for_external_shipping,
    api_client,
):
    # given
    checkout = checkout_with_delivery_method_for_external_shipping

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "new-abcd"
    response_shipping_name = "New Provider - Economy"
    response_shipping_price = "10"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": response_shipping_name,
            "amount": response_shipping_price,
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mocked_send_webhook_request_sync.return_value = mock_json_response

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout), "shippingMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == method_id
    assert data["checkout"]["deliveryMethod"]["name"] == response_shipping_name

    checkout.refresh_from_db()

    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery.shipping_method_id == method_id
    assert checkout.shipping_method_name == response_shipping_name

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_method_update_from_external_shipping_to_the_same_external(
    mocked_invalidate_checkout,
    mocked_send_webhook_request_sync,
    mocked_call_checkout_info_event,
    address,
    settings,
    shipping_app,
    checkout_with_item,
    api_client,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "new-abcd"
    response_shipping_name = "New Provider - Economy"
    response_shipping_price = "10"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": response_shipping_name,
            "amount": response_shipping_price,
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]

    mocked_send_webhook_request_sync.return_value = mock_json_response

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout,
        external_shipping_method_id=method_id,
        name=response_shipping_name,
        price_amount=response_shipping_price,
        currency="USD",
        maximum_delivery_days=7,
        is_external=True,
    )
    checkout.shipping_method_name = response_shipping_name
    checkout.undiscounted_base_shipping_price_amount = Decimal(response_shipping_price)
    checkout.save()

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout), "shippingMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == method_id
    assert data["checkout"]["deliveryMethod"]["name"] == response_shipping_name

    checkout.refresh_from_db()

    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery.shipping_method_id == method_id
    assert checkout.undiscounted_base_shipping_price_amount == Decimal(
        response_shipping_price
    )

    mocked_invalidate_checkout.assert_not_called()
    mocked_call_checkout_info_event.assert_not_called()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_method_update_from_external_shipping_to_built_in_method(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_delivery_method_for_external_shipping,
    shipping_method,
    api_client,
):
    # given
    checkout = checkout_with_delivery_method_for_external_shipping

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {
            "id": to_global_id_or_none(checkout),
            "shippingMethodId": to_global_id_or_none(shipping_method),
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        shipping_method
    )
    assert data["checkout"]["deliveryMethod"]["name"] == shipping_method.name

    checkout.refresh_from_db()

    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)
    assert checkout.collection_point_id is None
    assert checkout.shipping_method_name == shipping_method.name

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_method_update_from_external_shipping_to_none(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_delivery_method_for_external_shipping,
    api_client,
):
    # given
    checkout = checkout_with_delivery_method_for_external_shipping

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout), "shippingMethodId": None},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"] is None

    checkout.refresh_from_db()

    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery is None
    assert checkout.shipping_method_name is None

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_method_update_from_built_in_shipping_to_different_built_in(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_shipping_method,
    other_shipping_method,
    api_client,
):
    # given
    checkout = checkout_with_shipping_method

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {
            "id": to_global_id_or_none(checkout),
            "shippingMethodId": to_global_id_or_none(other_shipping_method),
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        other_shipping_method
    )
    assert data["checkout"]["deliveryMethod"]["name"] == other_shipping_method.name

    checkout.refresh_from_db()
    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery.shipping_method_id == str(
        other_shipping_method.id
    )
    assert checkout.shipping_method_name == other_shipping_method.name

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_method_update_from_built_in_shipping_to_external(
    mocked_invalidate_checkout,
    mocked_send_webhook_request_sync,
    mocked_call_checkout_info_event,
    settings,
    checkout_with_shipping_method,
    shipping_app,
    api_client,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "new-abcd"
    response_shipping_name = "New Provider - Economy"
    response_shipping_price = "10"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": response_shipping_name,
            "amount": response_shipping_price,
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]

    mocked_send_webhook_request_sync.return_value = mock_json_response

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    checkout = checkout_with_shipping_method

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout), "shippingMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == method_id
    assert data["checkout"]["deliveryMethod"]["name"] == response_shipping_name

    checkout.refresh_from_db()
    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery.shipping_method_id == method_id
    assert checkout.shipping_method_name == response_shipping_name

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_method_update_from_built_in_shipping_to_the_same_built_in(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_shipping_method,
    api_client,
):
    # given
    checkout = checkout_with_shipping_method

    assigned_delivery = checkout.assigned_delivery
    price = assigned_delivery.price
    checkout.shipping_method_name = assigned_delivery.name
    checkout.undiscounted_base_shipping_price_amount = price.amount
    checkout.save()

    method_id = graphene.Node.to_global_id(
        "ShippingMethod", assigned_delivery.shipping_method_id
    )
    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {
            "id": to_global_id_or_none(checkout),
            "shippingMethodId": method_id,
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == method_id
    assert data["checkout"]["deliveryMethod"]["name"] == assigned_delivery.name

    checkout.refresh_from_db()
    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery_id == assigned_delivery.id
    assert checkout.shipping_method_name == assigned_delivery.name

    mocked_invalidate_checkout.assert_not_called()
    mocked_call_checkout_info_event.assert_not_called()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_method_update_from_built_in_shipping_to_none(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_shipping_method,
    api_client,
):
    # given
    checkout = checkout_with_shipping_method

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout), "shippingMethodId": None},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"] is None

    checkout.refresh_from_db()
    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery_id is None
    assert checkout.shipping_method_name is None

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()
