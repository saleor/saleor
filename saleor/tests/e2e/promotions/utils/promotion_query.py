from ...utils import get_graphql_content

PROMOTION_QUERY = """
query PromotionQuery($id:ID!) {
  promotion(id:$id) {
    id
  }
}
"""


def promotion_query(
    staff_api_client,
    promotion_id,
):
    variables = {"id": promotion_id}

    response = staff_api_client.post_graphql(
        PROMOTION_QUERY,
        variables,
    )

    content = get_graphql_content(response)

    data = content["data"]

    return data
