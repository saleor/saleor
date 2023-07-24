from saleor.graphql.tests.utils import get_graphql_content

DRAFT_ORDER_CREATE_MUTATION = """
mutation OrderDraftCreate($input: DraftOrderCreateInput!){
  draftOrderCreate(input: $input){
    errors{
        message
        field}
    order{
        id
        }
    }
}
"""


def draft_order_create(
    api_client,
    channel_id,
):
    variables = {
        "input": {
            "channelId": channel_id,
        }
    }

    response = api_client.post_graphql(
        DRAFT_ORDER_CREATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["draftOrderCreate"]

    return data
