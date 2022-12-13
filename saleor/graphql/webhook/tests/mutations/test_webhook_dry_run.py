import json
import uuid

import graphene

from .....graphql.tests.utils import assert_no_permission, get_graphql_content
from .....webhook.error_codes import WebhookDryRunErrorCode

WEBHOOK_DRY_RUN_MUTATION = """
    mutation webhookDryRun($input: WebhookDryRunInput!) {
        webhookDryRun(input: $input) {
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
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook

    variables = {
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


def test_webhook_dry_run_missing_permission(
    staff_api_client,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook

    variables = {
        "input": {"objectId": order_id, "query": webhook.subscription_query},
    }

    # when
    response = staff_api_client.post_graphql(query, variables, permissions=[])

    # then
    assert_no_permission(response)


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

    variables = {
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

    variables = {
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

    variables = {
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
