from ...utils import get_graphql_content

PROMOTION_RULE_CREATE_MUTATION = """
mutation promotionRuleCreate($input: PromotionRuleCreateInput!) {
  promotionRuleCreate(input: $input) {
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
      predicateType
      cataloguePredicate
      orderPredicate
      channels{
        id
      }
    }
  }
}
"""


def create_promotion_rule(staff_api_client, input):
    variables = {"input": input}

    response = staff_api_client.post_graphql(
        PROMOTION_RULE_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["promotionRuleCreate"]["errors"] == []

    data = content["data"]["promotionRuleCreate"]["promotionRule"]
    assert data["id"] is not None

    return data
