import json
from unittest.mock import patch

import graphene

from .....tests.utils import dummy_editorjs
from ....core.enums import LanguageCodeEnum, TranslationErrorCode
from ....tests.utils import get_graphql_content

ATTRIBUTE_VALUE_BULK_TRANSLATE_MUTATION = """
    mutation AttributeValueBulkTranslate(
        $translations: [AttributeValueBulkTranslateInput!]!
    ) {
        attributeValueBulkTranslate(translations: $translations) {
            results {
                errors {
                    path
                    code
                    message
                }
                translation {
                    id
                    name
                    richText
                    plainText
                    language {
                        code
                    }
                }
            }
            count
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.translation_created")
def test_attribute_value_bulk_translate_creates_translations(
    created_webhook_mock,
    staff_api_client,
    color_attribute,
    permission_manage_translations,
    settings,
):
    # given
    value = color_attribute.values.first()
    value_global_id = graphene.Node.to_global_id("AttributeValue", value.id)
    expected_text = "Nowy Kolor"
    expected_rich_text = json.dumps(dummy_editorjs(expected_text))

    assert value.translations.count() == 0

    translations = [
        {
            "id": value_global_id,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
                "richText": expected_rich_text,
                "plainText": expected_text,
            },
        },
        {
            "id": value_global_id,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "Rot",
                "richText": expected_rich_text,
                "plainText": expected_text,
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueBulkTranslate"]

    # then
    assert value.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "Czerwony"
    assert data["results"][0]["translation"]["richText"] == expected_rich_text
    assert data["results"][0]["translation"]["plainText"] == expected_text
    assert data["results"][1]["translation"]["name"] == "Rot"
    assert data["results"][1]["translation"]["plainText"] == expected_text
    assert data["results"][1]["translation"]["richText"] == expected_rich_text
    assert created_webhook_mock.call_count == 2


@patch("saleor.plugins.manager.PluginsManager.translation_created")
def test_attribute_value_bulk_translate_creates_name_from_translations_long_text(
    created_webhook_mock,
    staff_api_client,
    plain_text_attribute,
    permission_manage_translations,
    settings,
):
    # given
    value = plain_text_attribute.values.first()
    value_global_id = graphene.Node.to_global_id("AttributeValue", value.id)
    expected_text = "Nowy Kolor" * 250

    assert value.translations.count() == 0

    translations = [
        {
            "id": value_global_id,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "plainText": expected_text,
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueBulkTranslate"]

    # then
    assert value.translations.count() == 1
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert data["results"][0]["translation"]["name"] == expected_text[:249] + "…"
    assert data["results"][0]["translation"]["plainText"] == expected_text
    assert created_webhook_mock.call_count == 1


@patch("saleor.plugins.manager.PluginsManager.translation_updated")
def test_attribute_value_bulk_translate_updates_translations(
    updated_webhook_mock,
    staff_api_client,
    color_attribute_with_translations,
    permission_manage_translations,
    settings,
):
    # given
    value = color_attribute_with_translations.values.first()
    value_global_id = graphene.Node.to_global_id("AttributeValue", value.id)
    expected_text = "Nowy Kolor"
    expected_rich_text = json.dumps(dummy_editorjs(expected_text))

    translations = [
        {
            "id": value_global_id,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
                "richText": expected_rich_text,
                "plainText": expected_text,
            },
        },
        {
            "id": value_global_id,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "Rot",
                "richText": expected_rich_text,
                "plainText": expected_text,
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueBulkTranslate"]

    # then

    assert color_attribute_with_translations.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "Czerwony"
    assert data["results"][0]["translation"]["richText"] == expected_rich_text
    assert data["results"][0]["translation"]["plainText"] == expected_text
    assert data["results"][1]["translation"]["name"] == "Rot"
    assert data["results"][1]["translation"]["plainText"] == expected_text
    assert data["results"][1]["translation"]["richText"] == expected_rich_text
    assert updated_webhook_mock.call_count == 2


@patch("saleor.plugins.manager.PluginsManager.translation_created")
def test_attribute_value_bulk_translate_creates_translations_using_value_external_ref(
    created_webhook_mock,
    staff_api_client,
    color_attribute,
    permission_manage_translations,
    settings,
):
    # given
    value = color_attribute.values.first()
    expected_text = "Nowy Kolor"
    expected_rich_text = json.dumps(dummy_editorjs(expected_text))

    assert value.translations.count() == 0
    value.external_reference = "color_attribute_value"
    value.save(update_fields=["external_reference"])

    translations = [
        {
            "externalReference": value.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
                "richText": expected_rich_text,
                "plainText": expected_text,
            },
        },
        {
            "externalReference": value.external_reference,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "Rot",
                "richText": expected_rich_text,
                "plainText": expected_text,
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueBulkTranslate"]

    # then
    assert value.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "Czerwony"
    assert data["results"][0]["translation"]["richText"] == expected_rich_text
    assert data["results"][0]["translation"]["plainText"] == expected_text
    assert data["results"][1]["translation"]["name"] == "Rot"
    assert data["results"][1]["translation"]["plainText"] == expected_text
    assert data["results"][1]["translation"]["richText"] == expected_rich_text
    assert created_webhook_mock.call_count == 2


@patch("saleor.plugins.manager.PluginsManager.translation_updated")
def test_attribute_value_bulk_translate_updates_translations_using_value_external_ref(
    updated_webhook_mock,
    staff_api_client,
    color_attribute_with_translations,
    permission_manage_translations,
    settings,
):
    # given
    value = color_attribute_with_translations.values.first()
    value.external_reference = "color_attribute"
    value.save(update_fields=["external_reference"])

    expected_text = "Nowy Kolor"
    expected_rich_text = json.dumps(dummy_editorjs(expected_text))
    assert value.translations.count() == 2

    translations = [
        {
            "externalReference": value.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
                "richText": expected_rich_text,
                "plainText": expected_text,
            },
        },
        {
            "externalReference": value.external_reference,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "Rot",
                "richText": expected_rich_text,
                "plainText": expected_text,
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueBulkTranslate"]

    # then
    assert value.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "Czerwony"
    assert data["results"][0]["translation"]["richText"] == expected_rich_text
    assert data["results"][0]["translation"]["plainText"] == expected_text
    assert data["results"][1]["translation"]["name"] == "Rot"
    assert data["results"][1]["translation"]["plainText"] == expected_text
    assert data["results"][1]["translation"]["richText"] == expected_rich_text
    assert updated_webhook_mock.call_count == 2


def test_attribute_value_bulk_translate_return_error_when_value_id_and_external_ref(
    staff_api_client,
    color_attribute,
    permission_manage_translations,
    settings,
):
    # given
    value = color_attribute.values.first()
    value_global_id = graphene.Node.to_global_id("AttributeValue", value.id)
    value.external_reference = "color_attribute_value"
    value.save(update_fields=["external_reference"])

    translations = [
        {
            "id": value_global_id,
            "externalReference": value.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueBulkTranslate"]

    # then
    assert value.translations.count() == 0
    assert data["count"] == 0
    message = "Argument 'id' cannot be combined with 'externalReference'"
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.INVALID.name
    assert error["message"] == message


def test_attribute_value_bulk_translate_return_error_when_invalid_value_id(
    staff_api_client,
    permission_manage_translations,
    settings,
):
    # given
    translations = [
        {
            "id": graphene.Node.to_global_id("AttributeValue", -1),
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueBulkTranslate"]

    # then
    assert data["count"] == 0
    message = "Couldn't resolve to an object."
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.NOT_FOUND.name
    assert error["message"] == message
    assert error["path"] == "id"


def test_attribute_value_bulk_translate_return_error_when_invalid_value_external_ref(
    staff_api_client,
    permission_manage_translations,
    settings,
):
    # given

    translations = [
        {
            "externalReference": "invalid_id",
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Czerwony",
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueBulkTranslate"]

    # then
    assert data["count"] == 0
    message = "Couldn't resolve to an object."
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.NOT_FOUND.name
    assert error["message"] == message
    assert error["path"] == "externalReference"
