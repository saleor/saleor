from unittest.mock import patch

import graphene
import pytest

from ....core.enums import LanguageCodeEnum, TranslationErrorCode
from ....tests.utils import get_graphql_content
from ...mutations import AttributeBulkTranslate

ATTRIBUTE_BULK_TRANSLATE_MUTATION = """
    mutation AttributeBulkTranslate(
        $translations: [AttributeBulkTranslateInput!]!
    ) {
        attributeBulkTranslate(translations: $translations) {
            results {
                errors {
                    path
                    code
                    message
                }
                translation {
                    id
                    name
                    language {
                        code
                    }
                }
            }
            count
        }
    }
"""


def test_attribute_bulk_translate_get_translations_returns_valid_translations(
    color_attribute_with_translations, second_color_attribute_with_translations
):
    # given
    requested_language_code = LanguageCodeEnum.PL.value
    translations = {
        0: {
            "id": color_attribute_with_translations.id,
            "language_code": requested_language_code,
            "translation_fields": {
                "name": "Czerwony",
            },
        },
    }

    # when
    translations = AttributeBulkTranslate.get_translations(
        cleaned_inputs_map=translations,
        base_objects=[color_attribute_with_translations.id],
    )

    # then
    for translation in translations:
        assert translation.attribute_id == color_attribute_with_translations.id
        assert translation.language_code == requested_language_code


@pytest.mark.parametrize("identifier_field", ["external_reference", "id"])
def test_attribute_bulk_translate_get_base_objects_returns_valid_objects(
    identifier_field,
    color_attribute_with_translations,
    second_color_attribute_with_translations,
):
    # given
    requested_language_code = LanguageCodeEnum.PL.value

    color_attribute_with_translations.external_reference = "ext_ref"
    color_attribute_with_translations.save()

    translations = {
        0: {
            identifier_field: getattr(
                color_attribute_with_translations, identifier_field
            ),
            "language_code": requested_language_code,
            "translation_fields": {
                "name": "Czerwony",
            },
        },
    }

    # when
    base_objects = AttributeBulkTranslate.get_base_objects(translations)

    # then
    assert base_objects == [color_attribute_with_translations]


@patch("saleor.plugins.manager.PluginsManager.translations_created")
def test_attribute_bulk_translate_creates_translations(
    created_webhook_mock,
    staff_api_client,
    color_attribute,
    permission_manage_translations,
    settings,
):
    # given
    assert color_attribute.translations.count() == 0

    attr_global_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    translations = [
        {
            "id": attr_global_id,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
            },
        },
        {
            "id": attr_global_id,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "Rot",
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkTranslate"]

    # then

    assert color_attribute.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "Czerwony"
    assert data["results"][1]["translation"]["name"] == "Rot"
    assert created_webhook_mock.call_count == 1


@patch("saleor.plugins.manager.PluginsManager.translations_updated")
def test_attribute_bulk_translate_updates_translations(
    updated_webhook_mock,
    staff_api_client,
    color_attribute_with_translations,
    permission_manage_translations,
    settings,
):
    # given
    assert color_attribute_with_translations.translations.count() == 2

    attr_global_id = graphene.Node.to_global_id(
        "Attribute", color_attribute_with_translations.id
    )
    translations = [
        {
            "id": attr_global_id,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "NewCzerwony",
            },
        },
        {
            "id": attr_global_id,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "NewRot",
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkTranslate"]

    # then

    assert color_attribute_with_translations.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "NewCzerwony"
    assert data["results"][1]["translation"]["name"] == "NewRot"
    assert updated_webhook_mock.call_count == 1


@patch("saleor.plugins.manager.PluginsManager.translations_created")
def test_attribute_bulk_translate_creates_translations_using_attr_external_ref(
    created_webhook_mock,
    staff_api_client,
    color_attribute,
    permission_manage_translations,
    settings,
):
    # given
    assert color_attribute.translations.count() == 0
    color_attribute.external_reference = "color_attribute"
    color_attribute.save(update_fields=["external_reference"])

    translations = [
        {
            "externalReference": color_attribute.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
            },
        },
        {
            "externalReference": color_attribute.external_reference,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "Rot",
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkTranslate"]

    # then
    assert color_attribute.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "Czerwony"
    assert data["results"][1]["translation"]["name"] == "Rot"
    assert created_webhook_mock.call_count == 1


@patch("saleor.plugins.manager.PluginsManager.translations_updated")
def test_attribute_bulk_translate_updates_translations_using_attr_external_ref(
    updated_webhook_mock,
    staff_api_client,
    color_attribute_with_translations,
    permission_manage_translations,
    settings,
):
    # given
    assert color_attribute_with_translations.translations.count() == 2
    color_attribute_with_translations.external_reference = "color_attribute"
    color_attribute_with_translations.save(update_fields=["external_reference"])

    translations = [
        {
            "externalReference": color_attribute_with_translations.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "NewCzerwony",
            },
        },
        {
            "externalReference": color_attribute_with_translations.external_reference,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "NewRot",
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkTranslate"]

    # then

    assert color_attribute_with_translations.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "NewCzerwony"
    assert data["results"][1]["translation"]["name"] == "NewRot"
    assert updated_webhook_mock.call_count == 1


def test_attribute_bulk_translate_return_error_when_attr_id_and_external_ref(
    staff_api_client,
    color_attribute,
    permission_manage_translations,
    settings,
):
    # given
    assert color_attribute.translations.count() == 0
    color_attribute.external_reference = "color_attribute"
    color_attribute.save(update_fields=["external_reference"])
    attr_global_id = graphene.Node.to_global_id("Attribute", color_attribute.id)

    translations = [
        {
            "id": attr_global_id,
            "externalReference": color_attribute.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkTranslate"]

    # then
    assert color_attribute.translations.count() == 0
    assert data["count"] == 0
    message = "Argument 'id' cannot be combined with 'externalReference'"
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.INVALID.name
    assert error["message"] == message


def test_attribute_bulk_translate_return_error_when_invalid_attr_id(
    staff_api_client,
    permission_manage_translations,
    settings,
):
    # given

    translations = [
        {
            "id": graphene.Node.to_global_id("Attribute", -1),
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkTranslate"]

    # then
    assert data["count"] == 0
    message = "Couldn't resolve to an object."
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.NOT_FOUND.name
    assert error["message"] == message
    assert error["path"] == "id"


def test_attribute_bulk_translate_return_error_when_invalid_attr_external_ref(
    staff_api_client,
    permission_manage_translations,
    settings,
):
    # given

    translations = [
        {
            "externalReference": "invalid_reference",
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkTranslate"]

    # then
    assert data["count"] == 0
    message = "Couldn't resolve to an object."
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.NOT_FOUND.name
    assert error["message"] == message
    assert error["path"] == "externalReference"
