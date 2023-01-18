import json
from unittest import mock

import graphene

from .....core import EventDeliveryStatus
from .....graphql.tests.utils import get_graphql_content
from .....webhook.error_codes import WebhookTriggerErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import assert_no_permission

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


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_using_scheme_method")
def test_webhook_trigger_success(
    mock_send_webhook_using_scheme_method,
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
    webhook_response,
):
    # given
    query = WEBHOOK_TRIGGER_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    mock_send_webhook_using_scheme_method.return_value = webhook_response

    variables = {"webhookId": webhook_id, "objectId": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["webhookTrigger"]
    assert data
    assert not data["errors"]
    assert data["delivery"]["status"] == EventDeliveryStatus.PENDING.upper()
    assert data["delivery"]["eventType"] == WebhookEventAsyncType.ORDER_CREATED.upper()
    assert not data["delivery"]["payload"]


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_using_scheme_method")
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


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async")
def test_webhook_trigger_missing_user_permission(
    mocked_send_webhook_request,
    staff_api_client,
    order,
    subscription_order_created_webhook,
):
    # given
    mocked_send_webhook_request.return_value = None
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


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async")
def test_webhook_trigger_staff_user_not_authorized(
    mocked_send_webhook_request,
    user_api_client,
    order,
    subscription_order_created_webhook,
    permission_manage_orders,
):
    # given
    mocked_send_webhook_request.return_value = None
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


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async")
def test_webhook_trigger_missing_subscription_query(
    mocked_send_webhook_request,
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    mocked_send_webhook_request.return_value = None
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


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async")
def test_webhook_trigger_wrong_subscription_query(
    mocked_send_webhook_request,
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    mocked_send_webhook_request.return_value = None
    query = WEBHOOK_TRIGGER_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    webhook.subscription_query = webhook.subscription_query.replace(
        "subscription", "whatever"
    )
    webhook.save(update_fields=["subscription_query"])

    variables = {"webhookId": webhook_id, "objectId": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookTrigger"]["errors"][0]
    assert not error["field"]
    assert error["code"] == WebhookTriggerErrorCode.UNABLE_TO_PARSE.name
    assert (
        error["message"]
        == "Can't parse an event type from webhook's subscription query."
    )


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async")
def test_webhook_trigger_event_type_undefined(
    mocked_send_webhook_request,
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    mocked_send_webhook_request.return_value = None
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
    assert (
        error["message"]
        == "Event type: UndefinedEvent, which was parsed from webhook's "
        "subscription query, is not defined in graphql schema."
    )


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async")
def test_webhook_trigger_event_not_supported(
    mocked_send_webhook_request,
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_payment_authorize_webhook,
):
    # given
    mocked_send_webhook_request.return_value = None
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


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async")
def test_webhook_trigger_object_id_does_not_match_event(
    mocked_send_webhook_request,
    staff_api_client,
    permission_manage_orders,
    product,
    subscription_order_created_webhook,
):
    # given
    mocked_send_webhook_request.return_value = None
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
