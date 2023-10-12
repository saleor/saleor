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
      cataloguePredicate
      channels{
        id
      }
    }
  }
}
"""


def create_promotion_rule(
    staff_api_client,
    promotion_id,
    catalogue_predicate,
    reward_value_type="PERCENTAGE",
    reward_value=5.00,
    promotion_rule_name="Test rule",
    channel_id=None,
    description=None,
):
    if not channel_id:
        channel_id = []

    variables = {
        "input": {
            "promotion": promotion_id,
            "name": promotion_rule_name,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "channels": channel_id,
            "cataloguePredicate": catalogue_predicate,
            "description": description,
        }
    }

    response = staff_api_client.post_graphql(
        PROMOTION_RULE_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["promotionRuleCreate"]["errors"] == []

    data = content["data"]["promotionRuleCreate"]["promotionRule"]
    assert data["id"] is not None
    assert data["name"] == promotion_rule_name
    assert data["rewardValueType"] == reward_value_type
    assert data["rewardValue"] == reward_value
    return data
