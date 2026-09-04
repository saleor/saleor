import graphene

from ....core.enums import LanguageCodeEnum
from ....tests.utils import get_graphql_content

CATEGORY_TRANSLATE_MUTATION = """
    mutation (
        $id: ID!,
        $languageCode: LanguageCodeEnum!,
        $input: TranslationInput!
    ) {
       categoryTranslate(
            id: $id,
            languageCode: $languageCode,
            input: $input
        ) {
            category {
                translation(languageCode: $languageCode) {
                    name
                    slug
                    language {
                        code
                    }
                    __typename
                }
            }
            errors {
                message
                code
                field
            }
        }
    }
"""


def test_category_translate(
    staff_api_client,
    category,
    permission_manage_translations,
):
    # given

    id = graphene.Node.to_global_id("Category", category.id)
    name = "Polish category"
    slug = "polish-category"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {
            "name": name,
            "slug": slug,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        CATEGORY_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["categoryTranslate"]
    assert not data["errors"]
    translation_data = data["category"]["translation"]

    assert translation_data["name"] == name
    assert translation_data["language"]["code"] == "PL"
    assert translation_data["slug"] == slug
    translation = category.translations.first()
    assert translation.name == name
    assert translation.slug == slug


def test_category_translate_without_slug(
    staff_api_client,
    category,
    permission_manage_translations,
):
    # given

    id = graphene.Node.to_global_id("Category", category.id)
    name = "Polish category"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {
            "name": name,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        CATEGORY_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["categoryTranslate"]
    assert not data["errors"]
    translation_data = data["category"]["translation"]

    assert translation_data["name"] == name
    assert translation_data["language"]["code"] == LanguageCodeEnum.PL.name
    assert translation_data["slug"] is None
    translation = category.translations.first()
    assert translation.name == name
    assert translation.slug is None
