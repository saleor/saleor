import graphene
import pytest

from ....core.enums import LanguageCodeEnum, TranslationErrorCode
from ....tests.utils import get_graphql_content

CATEGORY_TRANSLATE_MUTATION = """
    mutation (
        $id: ID!,
        $languageCode: LanguageCodeEnum!,
        $input: CategoryTranslationInput!
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

CATEGORY_BACKGROUND_IMAGE_ALT_TRANSLATE_MUTATION = """
    mutation (
        $id: ID!,
        $languageCode: LanguageCodeEnum!,
        $input: CategoryTranslationInput!
    ) {
       categoryTranslate(
            id: $id,
            languageCode: $languageCode,
            input: $input
        ) {
            category {
                translation(languageCode: $languageCode) {
                    backgroundImageAlt
                    translatableContent {
                        backgroundImageAlt
                    }
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


def test_background_image_alt(
    staff_api_client,
    category,
    permission_manage_translations,
):
    category_id = graphene.Node.to_global_id("Category", category.pk)
    translated_alt = "Polish category background image alt text"
    variables = {
        "id": category_id,
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {"backgroundImageAlt": translated_alt},
    }

    response = staff_api_client.post_graphql(
        CATEGORY_BACKGROUND_IMAGE_ALT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    data = get_graphql_content(response)["data"]["categoryTranslate"]
    translation = category.translations.get(language_code="pl")
    assert data == {
        "category": {
            "translation": {
                "backgroundImageAlt": translated_alt,
                "translatableContent": {
                    "backgroundImageAlt": category.background_image_alt
                },
            }
        },
        "errors": [],
    }
    assert translation.background_image_alt == translated_alt


def test_rejects_background_image_alt_above_character_limit(
    staff_api_client,
    category,
    permission_manage_translations,
):
    character_limit = 128
    translated_alt = "a" * (character_limit + 1)
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {"backgroundImageAlt": translated_alt},
    }

    response = staff_api_client.post_graphql(
        CATEGORY_BACKGROUND_IMAGE_ALT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    data = get_graphql_content(response)["data"]["categoryTranslate"]
    assert data["category"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": "backgroundImageAlt",
        "code": TranslationErrorCode.INVALID.name,
        "message": (
            f"Ensure this value has at most {character_limit} characters "
            f"(it has {len(translated_alt)})."
        ),
    }
    assert category.translations.exists() is False


@pytest.mark.parametrize(
    ("_case", "translation_input"),
    [
        ("omitted", {}),
        ("explicit_null", {"backgroundImageAlt": None}),
    ],
)
def test_empty_background_image_alt_input_uses_default(
    _case,
    translation_input,
    staff_api_client,
    category,
    permission_manage_translations,
):
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "languageCode": LanguageCodeEnum.PL.name,
        "input": translation_input,
    }

    response = staff_api_client.post_graphql(
        CATEGORY_BACKGROUND_IMAGE_ALT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    data = get_graphql_content(response)["data"]["categoryTranslate"]
    assert data["errors"] == []
    assert data["category"]["translation"]["backgroundImageAlt"] == ""
    translation = category.translations.get(language_code="pl")
    assert translation.background_image_alt == ""


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
