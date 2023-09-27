from ...utils import get_graphql_content

PROMOTION_TRANSLATE_MUTATION = """
mutation PromotionTranslate($id: ID!, $input: PromotionTranslationInput!,
$languageCode: LanguageCodeEnum!) {
  promotionTranslate(id: $id, input: $input, languageCode: $languageCode) {
    errors {
      field
      code
      message
    }
    promotion {
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


def translate_promotion(staff_api_client, promotion_id, language_code="EN", input=None):
    variables = {
        "id": promotion_id,
        "languageCode": language_code,
        "input": input,
    }

    response = staff_api_client.post_graphql(
        PROMOTION_TRANSLATE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)

    assert content["data"]["promotionTranslate"]["errors"] == []

    data = content["data"]["promotionTranslate"]["promotion"]["translation"]
    assert data["id"] is not None
    return data
