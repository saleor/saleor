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
      channels {
        id
      }
    }
  }
}
"""


def update_promotion_rule(
    staff_api_client,
    promotion_id,
    catalogue_predicate,
    add_channels=None,
    remove_channels=None,
):
    if not add_channels:
        add_channels = []

    if not remove_channels:
        remove_channels = []

    variables = {
        "id": promotion_id,
        "input": {
            "cataloguePredicate": catalogue_predicate,
            "addChannels": add_channels,
            "removeChannels": remove_channels,
        },
    }

    response = staff_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["promotionRuleUpdate"]["errors"] == []

    data = content["data"]["promotionRuleUpdate"]["promotionRule"]
    print(data)
    return data
