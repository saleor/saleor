from ...utils import get_graphql_content

PROMOTION_RULE_UPDATE_MUTATION = """
mutation promotionRuleCreate($id: ID!, $input: PromotionRuleUpdateInput!) {
  promotionRuleUpdate(id: $id, input: $input) {
    errors {
      field
      message
      code
    }
    promotionRule {
      id
      name
      description
      rewardValueType
      rewardValue
      cataloguePredicate
      orderPredicate
      channels {
        id
      }
    }
  }
}
"""


def raw_update_promotion_rule(
    staff_api_client,
    promotion_rule_id,
    input,
):
    variables = {"id": promotion_rule_id, "input": input}

    response = staff_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    raw_data = content["data"]["promotionRuleUpdate"]

    return raw_data


def update_promotion_rule(
    staff_api_client,
    promotion_rule_id,
    input,
):
    response = raw_update_promotion_rule(
        staff_api_client,
        promotion_rule_id,
        input,
    )

    assert response["errors"] == []

    data = response["promotionRule"]
    return data
