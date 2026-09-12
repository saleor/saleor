import graphene

from ...core.enums import LanguageCodeEnum
from ...tests.utils import get_graphql_content
from ..schema import TranslatableKinds

PRODUCT_MEDIA_TRANSLATION_QUERY = """
    query ProductMediaTranslation($productId: ID!, $channel: String!) {
        product(id: $productId, channel: $channel) {
            media {
                id
                alt
                translation(languageCode: PL) {
                    id
                    alt
                    language {
                        code
                    }
                }
            }
        }
    }
"""


def test_product_media_translation(api_client, product_media_image, channel_USD):
    translated_alt = "Polish alt text"
    translation = product_media_image.translations.create(
        language_code="pl", alt=translated_alt
    )
    product_id = graphene.Node.to_global_id("Product", product_media_image.product_id)
    product_media_id = graphene.Node.to_global_id(
        "ProductMedia", product_media_image.pk
    )
    translation_id = graphene.Node.to_global_id(
        "ProductMediaTranslation", translation.pk
    )

    response = api_client.post_graphql(
        PRODUCT_MEDIA_TRANSLATION_QUERY,
        {"productId": product_id, "channel": channel_USD.slug},
    )

    data = get_graphql_content(response)["data"]["product"]
    assert data["media"] == [
        {
            "id": product_media_id,
            "alt": product_media_image.alt,
            "translation": {
                "id": translation_id,
                "alt": translated_alt,
                "language": {"code": LanguageCodeEnum.PL.name},
            },
        }
    ]


PRODUCT_MEDIA_TRANSLATIONS_QUERY = """
    query ProductMediaTranslations(
        $kind: TranslatableKinds!, $languageCode: LanguageCodeEnum!
    ) {
        translations(kind: $kind, first: 10) {
            edges {
                node {
                    ... on ProductMediaTranslatableContent {
                        id
                        productMediaId
                        alt
                        translation(languageCode: $languageCode) {
                            id
                            alt
                        }
                    }
                }
            }
            totalCount
        }
    }
"""


def test_translations_query_product_media(
    staff_api_client,
    permission_manage_translations,
    product_media_image,
):
    translated_alt = "French alt text"
    translation = product_media_image.translations.create(
        language_code="fr", alt=translated_alt
    )
    content_id = graphene.Node.to_global_id(
        "ProductMediaTranslatableContent", product_media_image.pk
    )
    product_media_id = graphene.Node.to_global_id(
        "ProductMedia", product_media_image.pk
    )
    translation_id = graphene.Node.to_global_id(
        "ProductMediaTranslation", translation.pk
    )
    variables = {
        "kind": TranslatableKinds.PRODUCT_MEDIA.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }

    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_TRANSLATIONS_QUERY,
        variables,
        permissions=[permission_manage_translations],
    )

    data = get_graphql_content(response)["data"]["translations"]
    assert data == {
        "edges": [
            {
                "node": {
                    "id": content_id,
                    "productMediaId": product_media_id,
                    "alt": product_media_image.alt,
                    "translation": {
                        "id": translation_id,
                        "alt": translated_alt,
                    },
                }
            }
        ],
        "totalCount": 1,
    }


PRODUCT_MEDIA_TRANSLATABLE_CONTENT_QUERY = """
    query ProductMediaTranslatableContent(
        $id: ID!, $kind: TranslatableKinds!,
        $languageCode: LanguageCodeEnum!
    ) {
        translation(id: $id, kind: $kind) {
            ... on ProductMediaTranslatableContent {
                id
                productMediaId
                alt
                translation(languageCode: $languageCode) {
                    id
                    alt
                }
            }
        }
    }
"""


def test_translation_query_product_media(
    staff_api_client,
    permission_manage_translations,
    product_media_image,
):
    translated_alt = "French alt text"
    translation = product_media_image.translations.create(
        language_code="fr", alt=translated_alt
    )
    content_id = graphene.Node.to_global_id(
        "ProductMediaTranslatableContent", product_media_image.pk
    )
    product_media_id = graphene.Node.to_global_id(
        "ProductMedia", product_media_image.pk
    )
    translation_id = graphene.Node.to_global_id(
        "ProductMediaTranslation", translation.pk
    )
    variables = {
        "id": product_media_id,
        "kind": TranslatableKinds.PRODUCT_MEDIA.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }

    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_TRANSLATABLE_CONTENT_QUERY,
        variables,
        permissions=[permission_manage_translations],
    )

    data = get_graphql_content(response)["data"]["translation"]
    assert data == {
        "id": content_id,
        "productMediaId": product_media_id,
        "alt": product_media_image.alt,
        "translation": {
            "id": translation_id,
            "alt": translated_alt,
        },
    }
