from ...utils import get_graphql_content

PROMOTION_CREATE_MUTATION = """
mutation CreatePromotion($input: PromotionCreateInput!) {
  promotionCreate(input: $input) {
    errors {
      message
      field
      code
    }
    promotion {
      id
      name
      startDate
      endDate
    }
  }
}
"""


def create_promotion(
    staff_api_client,
    promotion_name,
):
    variables = {"input": {"name": promotion_name}}

    response = staff_api_client.post_graphql(
        PROMOTION_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["promotionCreate"]
    assert data["promotion"]["id"] is not None
    return data
