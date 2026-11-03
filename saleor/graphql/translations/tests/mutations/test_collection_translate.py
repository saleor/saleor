import graphene
import pytest

from .....core.error_codes import TranslationErrorCode
from ....core.enums import LanguageCodeEnum
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

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


COLLECTION_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation (
        $id: ID,
        $externalReference: String,
        $languageCode: LanguageCodeEnum!,
        $input: TranslationInput!
    ) {
        collectionTranslate(
            id: $id,
            externalReference: $externalReference,
            languageCode: $languageCode,
            input: $input
        ) {
            collection {
                externalReference
                translation(languageCode: $languageCode) {
                    name
                    slug
                    language {
                        code
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


def test_by_external_reference(
    staff_api_client, collection, permission_manage_translations, mocker
):
    # given
    external_reference = "collection-ext-ref"
    collection.external_reference = external_reference
    collection.save(update_fields=["external_reference"])
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    language_code = LanguageCodeEnum.PL
    name = "Polish collection"
    slug = "polish-slug"
    variables = {
        "externalReference": external_reference,
        "languageCode": language_code.name,
        "input": {"name": name, "slug": slug},
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["collectionTranslate"]
    assert data["errors"] == []
    assert data["collection"] == {
        "externalReference": external_reference,
        "translation": {
            "name": name,
            "slug": slug,
            "language": {"code": language_code.name},
        },
    }
    translation = collection.translations.get(language_code=language_code.value)
    assert translation.name == name
    assert translation.slug == slug
    mocked_translations_created.assert_called_once_with([translation])


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            "id",
            TranslationErrorCode.REQUIRED,
            "This field is required",
        ),
        (
            "null",
            {"id": None, "externalReference": None},
            "id",
            TranslationErrorCode.REQUIRED,
            "This field is required",
        ),
        (
            "empty",
            {"externalReference": ""},
            None,
            TranslationErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "both",
            {"externalReference": "existing-reference"},
            None,
            TranslationErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'externalReference'",
        ),
        (
            "not_found",
            {"externalReference": "missing-reference"},
            "externalReference",
            TranslationErrorCode.NOT_FOUND,
            "Couldn't resolve to a node: missing-reference",
        ),
    ],
)
def test_external_reference_invalid_identifiers(
    _case,
    identifiers,
    error_field,
    error_code,
    message,
    staff_api_client,
    collection,
    permission_manage_translations,
    mocker,
):
    # given
    collection.external_reference = "existing-reference"
    collection.save(update_fields=["external_reference"])
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("Collection", collection.pk)
    variables["languageCode"] = LanguageCodeEnum.PL.name
    variables["input"] = {"name": "Polish collection"}

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["collectionTranslate"]
    assert data["collection"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    assert collection.translations.exists() is False
    mocked_translations_created.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "client_fixture", "permission_fixture", "is_allowed"),
    [
        ("anonymous", "api_client", None, False),
        ("customer", "user_api_client", None, False),
        ("staff_without_permission", "staff_api_client", None, False),
        (
            "staff_with_permission",
            "staff_api_client",
            "permission_manage_translations",
            True,
        ),
        ("app_without_permission", "app_api_client", None, False),
        (
            "app_with_permission",
            "app_api_client",
            "permission_manage_translations",
            True,
        ),
    ],
)
def test_external_reference_authorization(
    _case,
    client_fixture,
    permission_fixture,
    is_allowed,
    request,
    collection,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    if permission_fixture:
        permission = request.getfixturevalue(permission_fixture)
        if client.app:
            client.app.permissions.add(permission)
        else:
            client.user.user_permissions.add(permission)
    external_reference = "existing-reference"
    collection.external_reference = external_reference
    collection.save(update_fields=["external_reference"])
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    language_code = LanguageCodeEnum.PL
    name = "Polish collection"
    variables = {
        "externalReference": external_reference,
        "languageCode": language_code.name,
        "input": {"name": name},
    }

    # when
    response = client.post_graphql(
        COLLECTION_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["collectionTranslate"]
        assert data["errors"] == []
        assert data["collection"]["translation"]["name"] == name
        translation = collection.translations.get(language_code=language_code.value)
        assert translation.name == name
        mocked_translations_created.assert_called_once_with([translation])
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"collectionTranslate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["collectionTranslate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_TRANSLATIONS"
        )
        assert collection.translations.exists() is False
        mocked_translations_created.assert_not_called()
