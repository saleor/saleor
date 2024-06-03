import json
from unittest import mock

import graphene

from .....core import EventDeliveryStatus
from .....graphql.tests.utils import get_graphql_content
from .....webhook.error_codes import WebhookTriggerErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import assert_no_permission
from ...subscription_types import WEBHOOK_TYPES_MAP

WEBHOOK_TRIGGER_MUTATION = """
    mutation webhookTrigger($webhookId: ID!, $objectId: ID!) {
        webhookTrigger(webhookId: $webhookId, objectId: $objectId) {
            errors {
                field
                code
                message
            }
            delivery {
                status
                eventType
                payload
            }
        }
    }
    """


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_webhook_trigger_success(
    mock_send_webhook_using_scheme_method,
    async_subscription_webhooks_with_root_objects,
    superuser_api_client,
    webhook_response,
):
    # given
    query = WEBHOOK_TRIGGER_MUTATION

    for event_name, event_type in WEBHOOK_TYPES_MAP.items():
        if (
            not event_type._meta.enable_dry_run
            or event_name not in async_subscription_webhooks_with_root_objects
        ):
            continue

        webhook = async_subscription_webhooks_with_root_objects[event_name][0]
        object = async_subscription_webhooks_with_root_objects[event_name][1]
        object_type = object.__class__.__name__
        events = WebhookEventAsyncType
        if event_name in [
            events.SALE_CREATED,
            events.SALE_UPDATED,
            events.SALE_DELETED,
            events.SALE_TOGGLE,
        ]:
            object_id = graphene.Node.to_global_id("Sale", object.old_sale_id)
        else:
            object_id = graphene.Node.to_global_id(object_type, object.pk)

        webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

        mock_send_webhook_using_scheme_method.return_value = webhook_response

        variables = {"webhookId": webhook_id, "objectId": object_id}

        # when
        response = superuser_api_client.post_graphql(query, variables)
        content = get_graphql_content(response)

        # then
        data = content["data"]["webhookTrigger"]
        assert data
        assert not data["errors"]
        assert data["delivery"]["status"] == EventDeliveryStatus.PENDING.upper()
        assert data["delivery"]["eventType"] == event_name.upper()
        assert not data["delivery"]["payload"]


@mock.patch("saleor.webhook.transport.utils.send_webhook_using_scheme_method")
def test_webhook_trigger_type_not_supported(
    mock_send_webhook_using_scheme_method,
    async_subscription_webhooks_with_root_objects,
    superuser_api_client,
    webhook_response,
):
    # given
    query = WEBHOOK_TRIGGER_MUTATION

    for event_name, event_type in WEBHOOK_TYPES_MAP.items():
        if (
            event_type._meta.enable_dry_run
            or event_name not in async_subscription_webhooks_with_root_objects
        ):
            continue
        webhook = async_subscription_webhooks_with_root_objects[event_name][0]
        object = async_subscription_webhooks_with_root_objects[event_name][1]
        object_type = object.__class__.__name__
        object_id = graphene.Node.to_global_id(object_type, object.pk)

        webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

        mock_send_webhook_using_scheme_method.return_value = webhook_response

        variables = {"webhookId": webhook_id, "objectId": object_id}

        # when
        response = superuser_api_client.post_graphql(query, variables)
        content = get_graphql_content(response)

        # then
        data = content["data"]["webhookTrigger"]
        assert data
        assert data["errors"]
        assert data["errors"] == [
            {
                "field": None,
                "code": "TYPE_NOT_SUPPORTED",
                "message": (
                    f"Event type: {event_type.__name__}, "
                    "which was parsed from webhook's subscription query, "
                    "is not supported."
                ),
            }
        ]


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_webhook_trigger_fail(
    mock_send_webhook_using_scheme_method,
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
    webhook_response_failed,
):
    # given
    query = WEBHOOK_TRIGGER_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    mock_send_webhook_using_scheme_method.return_value = webhook_response_failed

    variables = {"webhookId": webhook_id, "objectId": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["webhookTrigger"]
    assert data
    assert not data["errors"]
    assert data["delivery"]["status"] == EventDeliveryStatus.FAILED.upper()
    assert data["delivery"]["eventType"] == WebhookEventAsyncType.ORDER_CREATED.upper()
    payload = json.loads(data["delivery"]["payload"])
    assert payload["order"]["id"] == order_id


def test_webhook_trigger_missing_user_permission(
    staff_api_client,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_TRIGGER_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    variables = {"webhookId": webhook_id, "objectId": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookTrigger"]["errors"][0]
    assert not error["field"]
    assert error["code"] == WebhookTriggerErrorCode.MISSING_PERMISSION.name
    assert (
        error["message"] == "The user doesn't have required permission: manage_orders."
    )


def test_webhook_trigger_staff_user_not_authorized(
    user_api_client,
    order,
    subscription_order_created_webhook,
    permission_manage_orders,
):
    # given
    user_api_client.user.user_permissions.add(permission_manage_orders)
    query = WEBHOOK_TRIGGER_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    variables = {"webhookId": webhook_id, "objectId": order_id}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_webhook_trigger_missing_subscription_query(
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_TRIGGER_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    webhook.subscription_query = None
    webhook.save(update_fields=["subscription_query"])

    variables = {"webhookId": webhook_id, "objectId": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookTrigger"]["errors"][0]
    assert error["field"] == "webhookId"
    assert error["code"] == WebhookTriggerErrorCode.MISSING_QUERY.name
    assert error["message"] == "Missing subscription query for given webhook."


def test_webhook_trigger_invalid_subscription_query(
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_TRIGGER_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    webhook.subscription_query = webhook.subscription_query.replace(
        "OrderCreated", "UndefinedEvent"
    )
    webhook.save(update_fields=["subscription_query"])

    variables = {"webhookId": webhook_id, "objectId": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookTrigger"]["errors"][0]
    assert not error["field"]
    assert error["code"] == WebhookTriggerErrorCode.GRAPHQL_ERROR.name
    assert 'Unknown type "UndefinedEvent"' in error["message"]


def test_webhook_trigger_synchronous_event_not_supported(
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_payment_authorize_webhook,
):
    # given
    query = WEBHOOK_TRIGGER_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_payment_authorize_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    variables = {"webhookId": webhook_id, "objectId": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookTrigger"]["errors"][0]
    assert not error["field"]
    assert error["code"] == WebhookTriggerErrorCode.TYPE_NOT_SUPPORTED.name
    assert (
        error["message"]
        == "Event type: PaymentAuthorize, which was parsed from webhook's "
        "subscription query, is not supported."
    )


def test_webhook_trigger_object_id_does_not_match_event(
    staff_api_client,
    permission_manage_orders,
    product,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_TRIGGER_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    product_id = graphene.Node.to_global_id("Product", product.id)
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    variables = {"webhookId": webhook_id, "objectId": product_id}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookTrigger"]["errors"][0]
    assert error["field"] == "objectId"
    assert error["code"] == WebhookTriggerErrorCode.INVALID_ID.name
    assert error["message"] == "ObjectId doesn't match event type."


def test_webhook_trigger_for_removed_app(
    staff_api_client,
    order,
    subscription_app_updated_webhook_removed_app,
):
    # given
    query = WEBHOOK_TRIGGER_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_app_updated_webhook_removed_app
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    variables = {"webhookId": webhook_id, "objectId": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["webhookTrigger"]
    assert app_data["delivery"] is None
    assert app_data["errors"][0]["code"] == WebhookTriggerErrorCode.NOT_FOUND.name
    assert app_data["errors"][0]["field"] == "webhookId"
