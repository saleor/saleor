import graphene

from .....graphql.tests.utils import get_graphql_content

WEBHOOK_TRIGGER_MUTATION = """
    mutation webhookTrigger($id: ID!, $input: WebhookTriggerInput!) {
        webhookTrigger(id: $id, input: $input) {
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
            payload
        }
    }
    """


def test_webhook_trigger(
    staff_api_client,
    permission_manage_apps,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_TRIGGER_MUTATION
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
    data = content["data"]["webhookTrigger"]
    assert data
    # delivery = data["delivery"]
    # errors = data["errors"]
