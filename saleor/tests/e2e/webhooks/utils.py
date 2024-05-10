from ..utils import get_graphql_content

WEBHOOK_CREATE_MUTATION = """
mutation WebhookCreate($input: WebhookCreateInput!) {
  webhookCreate(input: $input) {
    errors {
      field
      code
      message
    }
    webhook {
      id
      name
      isActive
      targetUrl
      syncEvents{
        eventType
      }
      asyncEvents{
        eventType
      }
      subscriptionQuery
      customHeaders
    }
    __typename
  }
}
"""


def create_webhook(
    staff_api_client,
    input,
):
    variables = {
        "input": input,
    }

    response = staff_api_client.post_graphql(
        WEBHOOK_CREATE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)

    assert content["data"]["webhookCreate"]["errors"] == []
    data = content["data"]["webhookCreate"]["webhook"]
    assert data["id"] is not None

    return data
