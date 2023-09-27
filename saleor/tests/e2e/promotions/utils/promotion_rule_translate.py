from ...utils import get_graphql_content

PROMOTION_RULE_TRANSLATE_MUTATION = """
mutation promotionRuleTranslate($id: ID!, $input: PromotionRuleTranslationInput!,
$languageCode: LanguageCodeEnum!) {
  promotionRuleTranslate(id: $id, input: $input, languageCode: $languageCode) {
    errors {
      field
      code
      message
    }
    promotionRule {
      id
      translation(languageCode: $languageCode) {
        id
        language {
          code
        }
        name
        description
      }
    }
  }
}
"""


def translate_promotion_rule(
    staff_api_client, promotion_rule_id, language_code="EN", input=None
):
    variables = {
        "id": promotion_rule_id,
        "languageCode": language_code,
        "input": input,
    }

    response = staff_api_client.post_graphql(
        PROMOTION_RULE_TRANSLATE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)

    assert content["data"]["promotionRuleTranslate"]["errors"] == []

    data = content["data"]["promotionRuleTranslate"]["promotionRule"]["translation"]
    assert data["id"] is not None
    return data
