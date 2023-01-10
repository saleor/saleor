import json
import uuid

import graphene

from .....graphql.tests.utils import get_graphql_content
from .....webhook.error_codes import WebhookDryRunErrorCode

# import pytest


# from .....webhook.event_types import WebhookEventAsyncType

WEBHOOK_DRY_RUN_MUTATION = """
    mutation webhookDryRun($query: String!, $objectId: ID!) {
        webhookDryRun(query: $query, objectId: $objectId) {
            errors {
                field
                code
                message
            }
            payload
        }
    }
    """


def test_webhook_dry_run(
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook

    variables = {"objectId": order_id, "query": webhook.subscription_query}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["webhookDryRun"]
    payload = json.loads(data["payload"])
    assert payload["order"]["id"] == order_id


def test_webhook_dry_run_missing_user_permission(
    staff_api_client,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook

    variables = {"objectId": order_id, "query": webhook.subscription_query}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert not error["field"]
    assert error["code"] == WebhookDryRunErrorCode.MISSING_PERMISSION.name
    assert (
        error["message"] == "The user doesn't have required permission: manage_orders."
    )


def test_webhook_dry_run_non_existing_id(
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", uuid.uuid4())
    webhook = subscription_order_created_webhook

    variables = {"objectId": order_id, "query": webhook.subscription_query}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "objectId"
    assert error["code"] == WebhookDryRunErrorCode.NOT_FOUND.name
    assert error["message"] == f"Couldn't resolve to a node: {order_id}"


def test_webhook_dry_run_wrong_subscription_query(
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    subscription = webhook.subscription_query.replace("subscription", "whatever")

    variables = {"objectId": order_id, "query": subscription}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "query"
    assert error["code"] == WebhookDryRunErrorCode.UNABLE_TO_PARSE.name
    assert error["message"] == "Can't parse an event type from query."


def test_webhook_dry_run_event_type_doesnt_exist(
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    subscription = webhook.subscription_query.replace("OrderCreated", "UndefinedEvent")

    variables = {"objectId": order_id, "query": subscription}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "query"
    assert error["code"] == WebhookDryRunErrorCode.GRAPHQL_ERROR.name
    assert (
        error["message"]
        == "Event type: UndefinedEvent is not defined in graphql schema."
    )


def test_webhook_dry_run_object_id_does_not_match_event(
    staff_api_client,
    permission_manage_orders,
    product,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    product_id = graphene.Node.to_global_id("Product", product.id)
    webhook = subscription_order_created_webhook

    variables = {"objectId": product_id, "query": webhook.subscription_query}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "objectId"
    assert error["code"] == WebhookDryRunErrorCode.INVALID_ID.name
    assert error["message"] == "ObjectId doesn't match event type."


def test_webhook_dry_run_event_type_not_supported(
    staff_api_client,
    permission_manage_orders,
    product,
    subscription_payment_authorize_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    product_id = graphene.Node.to_global_id("Product", product.id)
    webhook = subscription_payment_authorize_webhook

    variables = {"objectId": product_id, "query": webhook.subscription_query}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "query"
    assert error["code"] == WebhookDryRunErrorCode.TYPE_NOT_SUPPORTED.name
    assert error["message"] == "Event type: PaymentAuthorize not supported."


# @pytest.fixture
# def subscription_webhooks_with_objects(
#     subscription_order_created_webhook,
#     subscription_product_created_webhook,
#     order,
#     product
# ):
#     events = WebhookEventAsyncType
#     return {
#         events.ORDER_CREATED: [subscription_order_created_webhook, order],
#         events.PRODUCT_CREATED: [subscription_product_created_webhook, product],
#     }
#
#
# def test_webhook_dry_run_root_types(
#     staff_api_client,
#     permission_manage_apps,
#     permission_manage_orders,
#     permission_manage_products,
#     subscription_webhooks_with_objects,
# ):
#     # given
#     query = WEBHOOK_DRY_RUN_MUTATION
#
#     for event_type, _ in WebhookEventAsyncType.ROOT_TYPE.items():
#         if not subscription_webhooks_with_objects.get(event_type):
#             continue
#
#         webhook = subscription_webhooks_with_objects[event_type][0]
#         object = subscription_webhooks_with_objects[event_type][1]
#
#         object_id = graphene.Node.to_global_id(object.__class__.__name__, object.id)
#
#
#         variables = {"objectId": object_id, "query": webhook.subscription_query}
#
#         # when
#         response = staff_api_client.post_graphql(
#             query, variables, permissions=[permission_manage_apps,
#             permission_manage_orders, permission_manage_products]
#         )
#         breakpoint()
#         content = get_graphql_content(response)
#
#         # then
#         assert content["data"]["webhookDryRun"]
#         assert not content["data"]["webhookDryRun"]["errors"]
