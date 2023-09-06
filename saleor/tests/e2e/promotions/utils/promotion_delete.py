from ...utils import get_graphql_content

PROMOTION_DELETE_MUTATION = """
mutation DeletePromotion($id:ID!) {
  promotionDelete(id: $id) {
    errors {
      code
      field
      message
    }
    promotion {
      id
    }
  }
}
"""


def delete_promotion(
    staff_api_client,
    promotion_id,
):
    variables = {"id": promotion_id}

    response = staff_api_client.post_graphql(
        PROMOTION_DELETE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)
    data = content["data"]["promotionDelete"]
    assert data["errors"] == []

    return data
