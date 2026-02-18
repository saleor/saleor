import json
import uuid
from decimal import Decimal
from unittest import mock
from unittest.mock import call

import graphene
import pytest
from measurement.measures import Weight
from prices import Money

from ....graphql.core.utils import to_global_id_or_none
from ....graphql.tests.utils import get_graphql_content
from ....graphql.webhook.utils import get_subscription_query_hash
from ....shipping.interface import ExcludedShippingMethod, ShippingMethodData
from ....shipping.models import ShippingMethod
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook
from ....webhook.response_schemas.shipping import logger as schema_logger
from ....webhook.response_schemas.utils.annotations import logger as annotations_logger
from ....webhook.transport.shipping_helpers import to_shipping_app_id
from ....webhook.transport.utils import generate_cache_key_for_webhook
from ...webhooks.exclude_shipping import (
    CACHE_EXCLUDED_SHIPPING_TIME,
    _generate_excluded_shipping_methods_for_checkout_payload,
    _get_cache_data_for_exclude_shipping_methods,
    _get_excluded_shipping_methods_from_response,
    _get_excluded_shipping_methods_or_fetch,
    excluded_shipping_methods_for_checkout,
)

CHECKOUT_QUERY_SHIPPING_METHOD = """
query Checkout($id: ID){
  checkout(id: $id) {
    shippingMethods {
      id
      name
      active
    }
    availableShippingMethods {
      id
      name
      active
    }
  }
}
"""


@pytest.fixture
def available_shipping_methods():
    return [
        ShippingMethodData(
            id="1",
            price=Money(Decimal(10), "usd"),
            name=uuid.uuid4().hex,
            maximum_order_weight=Weight(kg=0),
            minimum_order_weight=Weight(kg=0),
            maximum_delivery_days=0,
            minimum_delivery_days=5,
        ),
        ShippingMethodData(
            id="2",
            price=Money(Decimal(10), "usd"),
            name=uuid.uuid4().hex,
            maximum_order_weight=Weight(kg=0),
            minimum_order_weight=Weight(kg=0),
            maximum_delivery_days=0,
            minimum_delivery_days=5,
        ),
    ]


@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout"
)
def test_checkout_deliveries(
    mocked_webhook,
    staff_api_client,
    checkout_ready_to_complete,
    permission_manage_checkouts,
    settings,
    shipping_method_weight_based,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"
    excluded_shipping_method_id = (
        checkout_ready_to_complete.assigned_delivery.shipping_method_id
    )
    mocked_webhook.return_value = [
        ExcludedShippingMethod(excluded_shipping_method_id, webhook_reason)
    ]
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    # when
    response = staff_api_client.post_graphql(
        CHECKOUT_QUERY_SHIPPING_METHOD,
        variables={"id": to_global_id_or_none(checkout_ready_to_complete)},
    )
    content = get_graphql_content(response)
    checkout_data = content["data"]["checkout"]

    shipping_methods = checkout_data["shippingMethods"]
    # then
    assert len(shipping_methods) == 2
    inactive_method = list(
        filter(
            lambda s: s["id"]
            == graphene.Node.to_global_id(
                "ShippingMethod", excluded_shipping_method_id
            ),
            shipping_methods,
        )
    )
    assert not inactive_method[0]["active"]


@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout"
)
def test_checkout_available_shipping_methods(
    mocked_webhook,
    staff_api_client,
    checkout_ready_to_complete,
    permission_manage_checkouts,
    settings,
    shipping_method_weight_based,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"

    excluded_shipping_method_id = (
        checkout_ready_to_complete.assigned_delivery.shipping_method_id
    )
    mocked_webhook.return_value = [
        ExcludedShippingMethod(excluded_shipping_method_id, webhook_reason)
    ]

    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    # when
    response = staff_api_client.post_graphql(
        CHECKOUT_QUERY_SHIPPING_METHOD,
        variables={"id": to_global_id_or_none(checkout_ready_to_complete)},
    )
    content = get_graphql_content(response)
    shipping_methods = content["data"]["checkout"]["availableShippingMethods"]
    # then
    assert len(shipping_methods) == 1
    assert shipping_methods[0]["active"]


@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout"
)
def test_checkout_deliveries_webhook_called_once(
    mocked_webhook,
    staff_api_client,
    checkout_ready_to_complete,
    permission_manage_checkouts,
):
    # given
    mocked_webhook.side_effect = [[], AssertionError("called twice.")]
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    # when
    response = staff_api_client.post_graphql(
        CHECKOUT_QUERY_SHIPPING_METHOD,
        variables={"id": to_global_id_or_none(checkout_ready_to_complete)},
    )
    content = get_graphql_content(response)
    checkout_data = content["data"]["checkout"]
    # then
    expected_count = ShippingMethod.objects.count()
    assert len(checkout_data["availableShippingMethods"]) == expected_count
    assert len(checkout_data["shippingMethods"]) == expected_count
    assert mocked_webhook.called


def test_get_cache_data_for_exclude_shipping_methods(checkout_with_items):
    # given
    payload_str = _generate_excluded_shipping_methods_for_checkout_payload(
        checkout_with_items, []
    )
    assert "last_change" in payload_str
    assert "meta" in payload_str

    # when
    cache_data = _get_cache_data_for_exclude_shipping_methods(payload_str)

    # then
    assert "last_change" not in cache_data
    assert "meta" not in cache_data


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping."
    "_generate_excluded_shipping_methods_for_checkout_payload"
)
def test_excluded_shipping_methods_for_checkout_webhook_without_pregenerated_payload(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    checkout_with_items,
    available_shipping_methods,
    app_exclude_shipping_for_checkout,
    settings,
):
    # given
    shipping_app = app_exclude_shipping_for_checkout
    shipping_webhook = shipping_app.webhooks.get()
    webhook_reason = "Checkout contains dangerous products."

    webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }

    mocked_webhook.return_value = webhook_response

    payload_dict = {"checkout": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
    mocked_payload.return_value = payload

    # when
    excluded_methods = excluded_shipping_methods_for_checkout(
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    )
    # then
    assert len(excluded_methods) == 1
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason

    mocked_webhook.assert_called_once_with(
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        payload,
        shipping_webhook,
        False,
        subscribable_object=(checkout_with_items, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    expected_cache_key = generate_cache_key_for_webhook(
        payload_dict,
        shipping_webhook.target_url,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        shipping_app.id,
    )

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        webhook_response,
        timeout=CACHE_EXCLUDED_SHIPPING_TIME,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping."
    "_generate_excluded_shipping_methods_for_checkout_payload"
)
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_excluded_shipping_methods_for_checkout_webhook_with_subscription_base_pregenerated_payload(
    mocked_subscription_payload,
    mocked_static_payload,
    mocked_webhook,
    mocked_cache_set,
    checkout_with_items,
    available_shipping_methods,
    exclude_shipping_app_with_subscription,
    settings,
):
    # given
    shipping_app = exclude_shipping_app_with_subscription
    shipping_webhook = shipping_app.webhooks.get()
    webhook_reason = "Checkout contains dangerous products."

    webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }

    mocked_webhook.return_value = webhook_response

    payload_dict = {"checkout": {"id": 1, "some_field": "12"}}
    query_hash = get_subscription_query_hash(shipping_webhook.subscription_query)
    pregenerated_payloads = {shipping_app.id: {query_hash: payload_dict}}
    payload = json.dumps(payload_dict)
    mocked_static_payload.return_value = payload

    # when
    excluded_methods = excluded_shipping_methods_for_checkout(
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
        pregenerated_subscription_payloads=pregenerated_payloads,
    )
    # then
    assert len(excluded_methods) == 1
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason

    mocked_webhook.assert_called_once_with(
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        payload,
        shipping_webhook,
        False,
        subscribable_object=(checkout_with_items, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=payload_dict,
    )
    expected_cache_key = generate_cache_key_for_webhook(
        payload_dict,
        shipping_webhook.target_url,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        shipping_app.id,
    )

    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        webhook_response,
        timeout=CACHE_EXCLUDED_SHIPPING_TIME,
    )
    mocked_subscription_payload.assert_not_called()


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping."
    "_generate_excluded_shipping_methods_for_checkout_payload"
)
def test_multiple_app_with_excluded_shipping_methods_for_checkout(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    checkout_with_items,
    available_shipping_methods,
    app_exclude_shipping_for_checkout,
    second_app_exclude_shipping_for_checkout,
    settings,
):
    # given
    shipping_app = app_exclude_shipping_for_checkout
    shipping_webhook = shipping_app.webhooks.get()

    second_shipping_app = second_app_exclude_shipping_for_checkout
    second_shipping_webhook = second_shipping_app.webhooks.get()

    webhook_reason = "Checkout contains dangerous products."
    webhook_second_reason = "Shipping is not applicable for this checkout."

    first_webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }
    second_webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_second_reason,
            },
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "2"),
                "reason": webhook_second_reason,
            },
        ]
    }

    mocked_webhook.side_effect = [first_webhook_response, second_webhook_response]

    payload_dict = {"checkout": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
    mocked_payload.return_value = payload

    # when
    excluded_methods = excluded_shipping_methods_for_checkout(
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    )

    # then
    assert len(excluded_methods) == 2
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    assert webhook_second_reason in em.reason
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    mocked_webhook.assert_any_call(
        event_type,
        payload,
        shipping_webhook,
        False,
        subscribable_object=(checkout_with_items, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    mocked_webhook.assert_any_call(
        event_type,
        payload,
        second_shipping_webhook,
        False,
        subscribable_object=(checkout_with_items, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    assert mocked_webhook.call_count == 2

    expected_cache_for_first_webhook_key = generate_cache_key_for_webhook(
        payload_dict, shipping_webhook.target_url, event_type, shipping_app.id
    )
    expected_cache_for_second_webhook_key = generate_cache_key_for_webhook(
        payload_dict,
        second_shipping_webhook.target_url,
        event_type,
        second_shipping_app.id,
    )

    assert expected_cache_for_first_webhook_key != expected_cache_for_second_webhook_key

    mocked_cache_set.assert_has_calls(
        [
            call(
                expected_cache_for_first_webhook_key,
                first_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
            call(
                expected_cache_for_second_webhook_key,
                second_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
        ]
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping."
    "_generate_excluded_shipping_methods_for_checkout_payload"
)
def test_multiple_webhooks_on_the_same_app_with_excluded_shipping_methods_for_checkout(
    mocked_payload,
    mocked_webhook,
    mocked_cache_set,
    checkout_with_items,
    available_shipping_methods,
    app_exclude_shipping_for_checkout,
    settings,
):
    # given
    shipping_app = app_exclude_shipping_for_checkout
    first_webhook = shipping_app.webhooks.get()
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS

    # create the second webhook with the same event
    second_webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=shipping_app,
        target_url="https://shipping-gateway.com/apiv2/",
    )
    second_webhook.events.create(
        event_type=event_type,
        webhook=second_webhook,
    )

    webhook_reason = "Checkout contains dangerous products."
    webhook_second_reason = "Shipping is not applicable for this checkout."

    first_webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }
    second_webhook_response = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_second_reason,
            },
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "2"),
                "reason": webhook_second_reason,
            },
        ]
    }

    mocked_webhook.side_effect = [first_webhook_response, second_webhook_response]

    payload_dict = {"checkout": {"id": 1, "some_field": "12"}}
    payload = json.dumps(payload_dict)
    mocked_payload.return_value = payload

    # when
    excluded_methods = excluded_shipping_methods_for_checkout(
        checkout=checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    )

    # then
    assert len(excluded_methods) == 2
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    assert webhook_second_reason in em.reason

    mocked_webhook.assert_any_call(
        event_type,
        payload,
        first_webhook,
        False,
        subscribable_object=(checkout_with_items, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    mocked_webhook.assert_any_call(
        event_type,
        payload,
        second_webhook,
        False,
        subscribable_object=(checkout_with_items, available_shipping_methods),
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        request=None,
        requestor=None,
        pregenerated_subscription_payload=None,
    )
    assert mocked_webhook.call_count == 2

    expected_cache_for_first_webhook_key = generate_cache_key_for_webhook(
        payload_dict, first_webhook.target_url, event_type, shipping_app.id
    )
    expected_cache_for_second_webhook_key = generate_cache_key_for_webhook(
        payload_dict, second_webhook.target_url, event_type, shipping_app.id
    )
    assert expected_cache_for_first_webhook_key != expected_cache_for_second_webhook_key

    mocked_cache_set.assert_has_calls(
        [
            call(
                expected_cache_for_first_webhook_key,
                first_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
            call(
                expected_cache_for_second_webhook_key,
                second_webhook_response,
                timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            ),
        ]
    )


@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping._parse_excluded_shipping_methods"
)
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping._get_excluded_shipping_methods_from_response"
)
def test_get_excluded_shipping_methods_or_fetch_invalid_response_type(
    mocked_get_excluded,
    mocked_webhook_sync_trigger,
    mocked_parse,
    app,
    checkout,
):
    # given
    mocked_webhook_sync_trigger.return_value = ["incorrect_type"]
    webhook = Webhook.objects.create(
        name="Simple webhook", app=app, target_url="http://www.example.com/test"
    )
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    webhook.events.create(event_type=event_type)
    webhooks = Webhook.objects.all()

    # when
    _get_excluded_shipping_methods_or_fetch(
        webhooks, event_type, '{"test":"payload"}', checkout, False, None
    )
    # then
    mocked_get_excluded.asssert_not_called()
    mocked_parse.assert_called_once_with([])


@mock.patch.object(annotations_logger, "warning")
@mock.patch.object(schema_logger, "warning")
def test_parse_excluded_shipping_methods_response(
    mocked_schema_logger, mocked_annotations_logger, app
):
    # given
    external_id = to_shipping_app_id(app, "test-1234")
    response = {
        "excluded_methods": [
            {
                "id": "",
            },
            {
                "id": "not-an-id",
            },
            {
                "id": graphene.Node.to_global_id("Car", "1"),
            },
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "2"),
            },
            {
                "id": external_id,
            },
        ]
    }
    webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=app,
        target_url="https://shipping-gateway.com/apiv2/",
    )

    # when
    excluded_methods = _get_excluded_shipping_methods_from_response(response, webhook)

    # then
    assert len(excluded_methods) == 2
    assert excluded_methods[0].id == "2"
    assert excluded_methods[1].id == external_id
    # 2 warning for each invalid data
    # warning for malformed id
    assert mocked_schema_logger.call_count == 3
    # warning for skipping shipping method
    assert mocked_annotations_logger.call_count == 3


@mock.patch.object(annotations_logger, "warning")
@mock.patch.object(schema_logger, "warning")
def test_parse_excluded_shipping_methods_response_invalid(
    mocked_schema_logger, mocked_annotations_logger, app
):
    # given
    response = {
        "excluded_methods": [
            {
                "id": "not-an-id",
            },
        ]
    }
    webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=app,
        target_url="https://shipping-gateway.com/apiv2/",
    )

    # when
    excluded_methods = _get_excluded_shipping_methods_from_response(response, webhook)

    # then
    assert not excluded_methods
    assert mocked_schema_logger.call_count == 1
    assert (
        "Malformed ShippingMethod id was provided:"
        in mocked_schema_logger.call_args[0][0]
    )
    assert mocked_annotations_logger.call_count == 1
    error_msg = mocked_annotations_logger.call_args[0][1]
    assert "Skipping invalid shipping method (FilterShippingMethodsSchema)" in error_msg


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_excluded_shipping_methods_for_checkout(
    mocked_webhook,
    checkout_with_items,
    available_shipping_methods,
    app_exclude_shipping_for_checkout,
):
    # given
    webhook_reason = "Order contains dangerous products."

    mocked_webhook.return_value = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }

    # when
    excluded_methods = excluded_shipping_methods_for_checkout(
        checkout_with_items,
        available_shipping_methods=available_shipping_methods,
        allow_replica=False,
        requestor=None,
    )

    # then
    assert len(excluded_methods) == 1
    em = excluded_methods[0]
    assert em.id == "1"
    assert webhook_reason in em.reason
    mocked_webhook.assert_called_once()
