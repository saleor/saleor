from unittest import mock
from unittest.mock import patch

import graphene
import pytest
from django.test import override_settings

from .....account.models import Address
from .....checkout.actions import call_checkout_info_event
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.utils import PRIVATE_META_APP_SHIPPING_ID, invalidate_checkout
from .....core.models import EventDelivery
from .....plugins.base_plugin import ExcludedShippingMethod
from .....plugins.manager import get_plugins_manager
from .....shipping import models as shipping_models
from .....shipping.utils import convert_to_shipping_method_data
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .....webhook.transport.asynchronous.transport import send_webhook_request_async
from .....webhook.transport.utils import WebhookResponse
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_UPDATE_SHIPPING_METHOD = """
    mutation checkoutShippingMethodUpdate(
            $id: ID, $shippingMethodId: ID){
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


# TODO: Deprecated
@pytest.mark.parametrize("is_valid_shipping_method", [True, False])
@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "clean_delivery_method"
)
@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_method_update(
    mocked_invalidate_checkout,
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
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
        assert mocked_invalidate_checkout.call_count == 1
    else:
        assert len(errors) == 1
        assert errors[0]["field"] == "shippingMethod"
        assert (
            errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
        )
        assert checkout.shipping_method == old_shipping_method
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
    assert PRIVATE_META_APP_SHIPPING_ID in checkout.metadata_storage.private_metadata


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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

    assert not data["errors"]
    assert checkout.shipping_method == shipping_method


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

    assert not data["errors"]
    assert checkout.shipping_method == shipping_method


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

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
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
    checkout.refresh_from_db(fields=["shipping_method"])
    assert checkout.shipping_method is None


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


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_shipping_method_update_triggers_webhooks(
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
        MUTATION_UPDATE_SHIPPING_METHOD,
        {
            "id": to_global_id_or_none(checkout_with_items),
            "shippingMethodId": method_id,
        },
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutShippingMethodUpdate"]["errors"]

    assert wrapped_call_checkout_info_event.called
    assert mocked_send_webhook_request_async.call_count == 1

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 4
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_updated_webhook.id
    ).exists()

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

    assert WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES in sync_deliveries
    tax_delivery = sync_deliveries[WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES]
    assert tax_delivery.webhook_id == tax_webhook.id


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async",
    wraps=send_webhook_request_async.apply_async,
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_shipping_method_update_external_shipping_triggers_webhooks(
    mocked_send_webhook_using_scheme_method,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_info_event,
    setup_checkout_webhooks,
    settings,
    address,
    staff_api_client,
    checkout_with_item,
):
    # given
    mocked_send_webhook_using_scheme_method.return_value = WebhookResponse(content="")
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

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
    mocked_send_webhook_request_sync.side_effect = [
        mock_json_response,
        [],
        [],
    ]

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_webhook.app.identifier}:{response_method_id}"
    )

    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutShippingMethodUpdate"]["errors"]

    assert wrapped_call_checkout_info_event.called
    assert wrapped_call_checkout_info_event.called
    assert mocked_send_webhook_request_async.call_count == 1

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 5
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_updated_webhook.id
    ).exists()

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

    assert WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES in sync_deliveries
    tax_delivery = sync_deliveries[WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES]
    assert tax_delivery.webhook_id == tax_webhook.id


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_shipping_method_update_to_none_triggers_webhooks(
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

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
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
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": checkout_update_delivery.id},
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 3
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_updated_webhook.id
    ).exists()

    shipping_methods_call, filter_shipping_call, tax_delivery_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )
    assert shipping_methods_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id
