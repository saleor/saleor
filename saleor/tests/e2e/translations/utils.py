from ..utils import get_graphql_content

TRANSLATIONS_QUERY = """
query Translations($language: LanguageCodeEnum!, $first: Int, $kind: TranslatableKinds!)
{
  translations(
    kind: $kind
    first: $first
  ) {
    totalCount
    edges {
      node {
        ...PromotionTranslation
        ...PromotionRuleTranslation
        __typename
      }
      __typename
    }
  }
}

fragment PromotionTranslation on PromotionTranslatableContent {
  id
  name
  description
  translation(languageCode:$language){
    id
    name
    description
  }
}

fragment PromotionRuleTranslation on PromotionRuleTranslatableContent {
  id
  description
  translation(languageCode: $language) {
    id
    description
  }
}
"""


def get_translations(
    staff_api_client,
    kind,
    first=10,
    language="EN",
):
    variables = {
        "kind": kind,
        "first": first,
        "language": language,
    }

    response = staff_api_client.post_graphql(
        TRANSLATIONS_QUERY,
        variables,
    )

    content = get_graphql_content(response)

    data = content["data"]

    return data
