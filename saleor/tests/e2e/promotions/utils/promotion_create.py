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
      type
      startDate
      endDate
      description
      rules {
        orderPredicate
        name
        rewardType
        rewardValue
        rewardValueType
        cataloguePredicate
        channels {
          id
        }
        id
        description
      }
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


def raw_create_promotion(
    staff_api_client,
    promotion_name,
    promotion_type,
    rules=None,
    start_date=None,
    end_date=None,
    description=None,
):
    variables = {
        "input": {
            "name": promotion_name,
            "type": promotion_type,
            "rules": rules,
            "startDate": start_date,
            "endDate": end_date,
            "description": description,
        }
    }

    if rules is not None:
        variables["input"]["rules"] = rules

    if start_date is not None:
        variables["input"]["startDate"] = start_date

    if end_date is not None:
        variables["input"]["endDate"] = end_date

    response = staff_api_client.post_graphql(
        PROMOTION_CREATE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)

    raw_data = content["data"]["promotionCreate"]
    return raw_data


def create_promotion(
    staff_api_client,
    promotion_name,
    promotion_type,
    rules=None,
    start_date=None,
    end_date=None,
    description=None,
):
    response = raw_create_promotion(
        staff_api_client,
        promotion_name,
        promotion_type,
        rules,
        start_date,
        end_date,
        description,
    )

    data = response["promotion"]
    assert response["errors"] == []
    assert data["id"] is not None
    return data
