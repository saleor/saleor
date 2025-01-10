import graphene

from ....core.enums import LanguageCodeEnum
from ....tests.utils import get_graphql_content

COLLECTION_TRANSLATE_MUTATION = """
    mutation (
        $id: ID!,
        $languageCode: LanguageCodeEnum!,
        $input: TranslationInput!
    ) {
        collectionTranslate(
            id: $id,
            languageCode: $languageCode,
            input: $input
        ) {
            collection {
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


def test_collection_translate(
    staff_api_client,
    published_collection,
    permission_manage_translations,
):
    # given

    id = graphene.Node.to_global_id("Collection", published_collection.id)
    name = "Polish Collection"
    slug = "polish-collection"
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
        COLLECTION_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionTranslate"]
    assert not data["errors"]
    translation_data = data["collection"]["translation"]

    assert translation_data["name"] == name
    assert translation_data["language"]["code"] == LanguageCodeEnum.PL.name
    assert translation_data["slug"] == slug
    translation = published_collection.translations.first()
    assert translation.name == name
    assert translation.slug == slug


def test_collection_translate_without_slug(
    staff_api_client,
    published_collection,
    permission_manage_translations,
):
    # given

    id = graphene.Node.to_global_id("Collection", published_collection.id)
    name = "Polish Collection"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {
            "name": name,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionTranslate"]
    assert not data["errors"]
    translation_data = data["collection"]["translation"]

    assert translation_data["name"] == name
    assert translation_data["language"]["code"] == LanguageCodeEnum.PL.name
    assert translation_data["slug"] is None
    translation = published_collection.translations.first()
    assert translation.name == name
    assert translation.slug is None


def test_collection_translate_slug_conflict(
    staff_api_client,
    unpublished_collection,
    collection_translation_fr,
    permission_manage_translations,
):
    id = graphene.Node.to_global_id("Collection", unpublished_collection.id)
    name = "Unpublished french collection"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.FR.name,
        "input": {"name": name, "slug": collection_translation_fr.slug},
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionTranslate"]

    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert (
        errors[0]["message"]
        == "Translation with this slug and language code already exists"
    )


def test_collection_translate_without_slug_change(
    staff_api_client,
    published_collection,
    collection_translation_fr,
    permission_manage_translations,
):
    id = graphene.Node.to_global_id("Collection", published_collection.id)
    name = "Updated french collection"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.FR.name,
        "input": {"name": name, "slug": collection_translation_fr.slug},
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionTranslate"]
    assert not data["errors"]
    translation_data = data["collection"]["translation"]

    assert translation_data["name"] == name
    assert translation_data["slug"] == collection_translation_fr.slug
    translation = published_collection.translations.first()
    assert translation.name == name
    assert translation.slug == collection_translation_fr.slug
