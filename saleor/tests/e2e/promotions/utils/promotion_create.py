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
      description
      createdAt
      metadata {
        key
        value
      }
      privateMetadata {
        key
        value
      }
    }
  }
}
"""


def create_promotion(
    staff_api_client,
    promotion_name,
    start_date=None,
    end_date=None,
    description=None,
):
    variables = {
        "input": {
            "name": promotion_name,
            "startDate": start_date,
            "endDate": end_date,
            "description": description,
        }
    }

    response = staff_api_client.post_graphql(
        PROMOTION_CREATE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)

    assert content["data"]["promotionCreate"]["errors"] == []

    data = content["data"]["promotionCreate"]["promotion"]
    assert data["id"] is not None
    return data
