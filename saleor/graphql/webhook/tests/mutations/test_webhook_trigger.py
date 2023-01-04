from unittest import mock

import graphene

from .....graphql.tests.utils import get_graphql_content

WEBHOOK_TRIGGER_MUTATION = """
    mutation webhookTrigger($webhookId: ID!, $objectId: ID!) {
        webhookTrigger(webhookId: $webhookId, objectId: $objectId) {
            errors {
                field
                code
                message
            }
            delivery {
                id
                status
                eventType
            }
        }
    }
    """


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async")
def test_webhook_trigger(
    mocked_send_webhook_request,
    staff_api_client,
    permission_manage_apps,
    permission_manage_orders,
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
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_apps, permission_manage_orders]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["webhookTrigger"]
    assert data
    assert not data["errors"]
