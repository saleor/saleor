from unittest.mock import patch

import graphene

from .....tests.utils import dummy_editorjs
from ....core.enums import LanguageCodeEnum, TranslationErrorCode
from ....tests.utils import get_graphql_content

PRODUCT_BULK_TRANSLATE_MUTATION = """
    mutation ProductBulkTranslate(
        $translations: [ProductBulkTranslateInput!]!
    ) {
        productBulkTranslate(translations: $translations) {
            results {
                errors {
                    path
                    code
                    message
                }
                translation {
                    id
                    name
                    description
                    language {
                        code
                    }
                }
            }
            count
        }
    }
"""

description_pl = dummy_editorjs("description PL", True)
description_de = dummy_editorjs("description DE", True)


@patch("saleor.plugins.manager.PluginsManager.translation_created")
def test_product_bulk_translate_creates_translations(
    created_webhook_mock,
    staff_api_client,
    product,
    permission_manage_translations,
    settings,
):
    # given
    assert product.translations.count() == 0

    product_global_id = graphene.Node.to_global_id("Product", product.id)
    translations = [
        {
            "id": product_global_id,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {"name": "Product PL", "description": description_pl},
        },
        {
            "id": product_global_id,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {"name": "Product DE", "description": description_de},
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkTranslate"]

    # then

    assert product.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "Product PL"
    assert data["results"][0]["translation"]["description"] == description_pl
    assert data["results"][1]["translation"]["name"] == "Product DE"
    assert data["results"][1]["translation"]["description"] == description_de
    assert created_webhook_mock.call_count == 2


@patch("saleor.plugins.manager.PluginsManager.translation_updated")
def test_product_bulk_translate_updates_translations(
    updated_webhook_mock,
    staff_api_client,
    product_with_translations,
    permission_manage_translations,
    settings,
):
    # given
    assert product_with_translations.translations.count() == 2

    product_global_id = graphene.Node.to_global_id(
        "Product", product_with_translations.id
    )
    translations = [
        {
            "id": product_global_id,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "NewProduct PL",
            },
        },
        {
            "id": product_global_id,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "NewProduct DE",
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkTranslate"]

    # then

    assert product_with_translations.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "NewProduct PL"
    assert data["results"][1]["translation"]["name"] == "NewProduct DE"
    assert updated_webhook_mock.call_count == 2


@patch("saleor.plugins.manager.PluginsManager.translation_created")
def test_product_bulk_translate_creates_translations_using_attr_external_ref(
    created_webhook_mock,
    staff_api_client,
    product,
    permission_manage_translations,
    settings,
):
    # given
    assert product.translations.count() == 0
    product.external_reference = "product-external-reference"
    product.save(update_fields=["external_reference"])

    translations = [
        {
            "externalReference": product.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {"name": "Product PL", "description": description_pl},
        },
        {
            "externalReference": product.external_reference,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {"name": "Product DE", "description": description_de},
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkTranslate"]

    # then
    assert product.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "Product PL"
    assert data["results"][0]["translation"]["description"] == description_pl
    assert data["results"][1]["translation"]["name"] == "Product DE"
    assert data["results"][1]["translation"]["description"] == description_de
    assert created_webhook_mock.call_count == 2


@patch("saleor.plugins.manager.PluginsManager.translation_updated")
def test_product_bulk_translate_updates_translations_using_attr_external_ref(
    updated_webhook_mock,
    staff_api_client,
    product_with_translations,
    permission_manage_translations,
    settings,
):
    # given
    assert product_with_translations.translations.count() == 2
    product_with_translations.external_reference = "product-external-reference"
    product_with_translations.save(update_fields=["external_reference"])

    translations = [
        {
            "externalReference": product_with_translations.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "NewProduct PL",
                "description": description_pl,
            },
        },
        {
            "externalReference": product_with_translations.external_reference,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "NewProduct DE",
                "description": description_de,
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkTranslate"]

    # then

    assert product_with_translations.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "NewProduct PL"
    assert data["results"][0]["translation"]["description"] == description_pl
    assert data["results"][1]["translation"]["name"] == "NewProduct DE"
    assert data["results"][1]["translation"]["description"] == description_de
    assert updated_webhook_mock.call_count == 2


def test_product_bulk_translate_return_error_when_attr_id_and_external_ref(
    staff_api_client,
    product,
    permission_manage_translations,
    settings,
):
    # given
    assert product.translations.count() == 0
    product.external_reference = "product_pl"
    product.save(update_fields=["external_reference"])
    product_global_id = graphene.Node.to_global_id("Product", product.id)

    translations = [
        {
            "id": product_global_id,
            "externalReference": product.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Product PL",
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkTranslate"]

    # then
    assert product.translations.count() == 0
    assert data["count"] == 0
    message = "Argument 'id' cannot be combined with 'externalReference'"
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.INVALID.name
    assert error["message"] == message


def test_product_bulk_translate_return_error_when_invalid_attr_id(
    staff_api_client,
    permission_manage_translations,
    settings,
):
    # given
    translations = [
        {
            "id": graphene.Node.to_global_id("Product", -1),
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Product PL",
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkTranslate"]

    # then
    assert data["count"] == 0
    message = "Couldn't resolve to an object."
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.NOT_FOUND.name
    assert error["message"] == message
    assert error["path"] == "id"


def test_product_bulk_translate_return_error_when_invalid_attr_external_ref(
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
                "name": "Product PL",
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkTranslate"]

    # then
    assert data["count"] == 0
    message = "Couldn't resolve to an object."
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.NOT_FOUND.name
    assert error["message"] == message
    assert error["path"] == "externalReference"
