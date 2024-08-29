import graphene

from .....product.models import ProductTranslation
from ....core.enums import LanguageCodeEnum
from ....tests.utils import get_graphql_content

PRODUCT_TRANSLATE_MUTATION = """
    mutation (
        $id: ID!,
        $languageCode: LanguageCodeEnum!,
        $input: TranslationInput!
    ) {
       productTranslate(
            id: $id,
            languageCode: $languageCode,
            input: $input
        ) {
            product {
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


def test_product_translate(
    staff_api_client,
    product,
    permission_manage_translations,
):
    # given

    id = graphene.Node.to_global_id("Product", product.id)
    name = "Polish name"
    slug = "polish-name"
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
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTranslate"]
    assert not data["errors"]
    translation_data = data["product"]["translation"]

    assert translation_data["name"] == name
    assert translation_data["language"]["code"] == "PL"
    assert translation_data["slug"] == slug
    translation = product.translations.first()
    assert translation.name == name
    assert translation.slug == slug


def test_product_translate_without_slug(
    staff_api_client,
    product,
    permission_manage_translations,
):
    # given
    id = graphene.Node.to_global_id("Product", product.id)
    name = "Polish name"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {
            "name": name,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTranslate"]
    assert not data["errors"]
    translation_data = data["product"]["translation"]

    assert translation_data["name"] == name
    assert translation_data["language"]["code"] == LanguageCodeEnum.PL.name
    assert translation_data["slug"] is None
    translation = product.translations.first()
    assert translation.name == name
    assert translation.slug is None


def test_product_translate_update(
    staff_api_client,
    product,
    product_translation_fr,
    permission_manage_translations,
):
    # given
    id = graphene.Node.to_global_id("Product", product.id)
    name = "New french name"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.FR.name,
        "input": {
            "name": name,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTranslate"]
    assert not data["errors"]
    translation_data = data["product"]["translation"]

    assert translation_data["name"] == name
    translation = product.translations.first()
    assert translation.name == name


def test_product_translate_update_when_slug_exists(
    staff_api_client,
    product,
    product_translation_fr,
    permission_manage_translations,
):
    # given
    id = graphene.Node.to_global_id("Product", product.id)
    name = "New french name"
    slug = "french-name"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.FR.name,
        "input": {
            "name": name,
        },
    }
    ProductTranslation.objects.filter(
        product=product, language_code=product_translation_fr.language_code
    ).update(slug=slug)

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTranslate"]
    assert not data["errors"]
    translation_data = data["product"]["translation"]

    assert translation_data["name"] == name
    assert translation_data["slug"] == slug
    translation = product.translations.first()
    assert translation.name == name
    assert translation.slug == slug
