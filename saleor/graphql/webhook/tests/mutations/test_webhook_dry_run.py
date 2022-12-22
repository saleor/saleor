import json
import uuid

import graphene

from .....graphql.tests.utils import assert_no_permission, get_graphql_content
from .....webhook.error_codes import WebhookDryRunErrorCode

WEBHOOK_DRY_RUN_MUTATION = """
    mutation webhookDryRun($id: ID!, $input: WebhookDryRunInput!) {
        webhookDryRun(id: $id, input: $input) {
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
    permission_manage_apps,
    order,
    subscription_order_created_webhook,
    subscription_product_updated_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    variables = {
        "id": webhook_id,
        "input": {"objectId": order_id, "query": webhook.subscription_query},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_apps]
    )
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
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    variables = {
        "id": webhook_id,
        "input": {"objectId": order_id, "query": webhook.subscription_query},
    }

    # when
    response = staff_api_client.post_graphql(query, variables, permissions=[])

    # then
    assert_no_permission(response)


def test_webhook_dry_run_missing_app_permission(
    staff_api_client,
    order,
    subscription_order_created_webhook,
    permission_manage_apps,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)
    app = webhook.app
    app.permissions.set([])

    variables = {
        "id": webhook_id,
        "input": {"objectId": order_id, "query": webhook.subscription_query},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_apps]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert not error["field"]
    assert error["code"] == WebhookDryRunErrorCode.MISSING_APP_PERMISSION.name
    assert (
        error["message"] == "The app doesn't have required permission: manage_orders."
    )


def test_webhook_dry_run_non_existing_id(
    staff_api_client,
    permission_manage_apps,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    order_id = graphene.Node.to_global_id("Order", uuid.uuid4())
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    variables = {
        "id": webhook_id,
        "input": {"objectId": order_id, "query": webhook.subscription_query},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_apps]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "objectId"
    assert error["code"] == WebhookDryRunErrorCode.NOT_FOUND.name
    assert error["message"] == f"Couldn't resolve to a node: {order_id}"


def test_webhook_dry_run_wrong_subscription_query(
    staff_api_client,
    permission_manage_apps,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    subscription = webhook.subscription_query.replace("subscription", "whatever")
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    variables = {
        "id": webhook_id,
        "input": {"objectId": order_id, "query": subscription},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_apps]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "query"
    assert error["code"] == WebhookDryRunErrorCode.GRAPHQL_ERROR.name
    assert error["message"] == "Can't parse an event type from query."


def test_webhook_dry_run_id_does_not_match_event(
    staff_api_client,
    permission_manage_apps,
    product,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.id)
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.id)

    variables = {
        "id": webhook_id,
        "input": {"objectId": product_id, "query": webhook.subscription_query},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_apps]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "objectId"
    assert error["code"] == WebhookDryRunErrorCode.INVALID_ID.name
    assert error["message"] == "ObjectId doesn't match event type."
