from unittest.mock import patch

import graphene
import pytest

from ....core.enums import LanguageCodeEnum, TranslationErrorCode
from ....tests.utils import get_graphql_content
from ...mutations import ProductVariantBulkTranslate

PRODUCT_VARIANT_BULK_TRANSLATE_MUTATION = """
    mutation ProductVariantBulkTranslate(
        $translations: [ProductVariantBulkTranslateInput!]!
    ) {
        productVariantBulkTranslate(translations: $translations) {
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


def test_product_variant_bulk_translate_get_translations_returns_valid_translations(
    product_list,
):
    # given
    first_variant = product_list[0].variants.first()
    first_variant.translations.create(language_code="pl", name="name-in-pl")
    first_variant.translations.create(language_code="de", name="name-in-de")

    second_variant = product_list[1].variants.first()
    second_variant.translations.create(language_code="pl", name="name-in-pl")
    second_variant.translations.create(language_code="de", name="name-in-de")

    requested_language_code = LanguageCodeEnum.PL.value

    translations = {
        0: {
            "id": first_variant.id,
            "languageCode": requested_language_code,
            "translationFields": {"name": "Product PL"},
        }
    }

    # when
    translations = ProductVariantBulkTranslate.get_translations(
        cleaned_inputs_map=translations, base_objects=[first_variant.id]
    )

    # then
    for translation in translations:
        assert translation.product_variant_id == first_variant.id
        assert translation.language_code == requested_language_code


@pytest.mark.parametrize("identifier_field", ["external_reference", "id"])
def test_product_variant_bulk_translate_get_base_objects_returns_valid_objects(
    identifier_field,
    product_list,
):
    # given
    first_variant = product_list[0].variants.first()
    first_variant.translations.create(language_code="pl", name="name-in-pl")
    first_variant.translations.create(language_code="de", name="name-in-de")

    second_variant = product_list[1].variants.first()
    second_variant.translations.create(language_code="pl", name="name-in-pl")
    second_variant.translations.create(language_code="de", name="name-in-de")

    first_variant.external_reference = "ext_ref"
    first_variant.save()

    requested_language_code = LanguageCodeEnum.PL.value

    translations = {
        0: {
            identifier_field: getattr(first_variant, identifier_field),
            "languageCode": requested_language_code,
            "translationFields": {"name": "Product PL"},
        }
    }

    # when
    base_objects = ProductVariantBulkTranslate.get_base_objects(translations)

    # then
    assert base_objects == [first_variant]


@patch("saleor.plugins.manager.PluginsManager.translations_created")
def test_product_variant_variant_bulk_translate_creates_translations(
    created_webhook_mock,
    staff_api_client,
    variant,
    permission_manage_translations,
    settings,
):
    # given
    assert variant.translations.count() == 0

    variant_global_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    translations = [
        {
            "id": variant_global_id,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {"name": "Product PL"},
        },
        {
            "id": variant_global_id,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {"name": "Product DE"},
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkTranslate"]

    # then

    assert variant.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "Product PL"
    assert data["results"][1]["translation"]["name"] == "Product DE"
    assert created_webhook_mock.call_count == 1


@patch("saleor.plugins.manager.PluginsManager.translations_updated")
def test_product_variant_bulk_translate_updates_translations(
    updated_webhook_mock,
    staff_api_client,
    variant_with_translations,
    permission_manage_translations,
    settings,
):
    # given
    assert variant_with_translations.translations.count() == 2

    variant_global_id = graphene.Node.to_global_id(
        "ProductVariant", variant_with_translations.id
    )
    translations = [
        {
            "id": variant_global_id,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "NewVariant PL",
            },
        },
        {
            "id": variant_global_id,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "NewVariant DE",
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkTranslate"]

    # then

    assert variant_with_translations.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "NewVariant PL"
    assert data["results"][1]["translation"]["name"] == "NewVariant DE"
    assert updated_webhook_mock.call_count == 1


@patch("saleor.plugins.manager.PluginsManager.translations_created")
def test_product_variant_bulk_translate_creates_translations_using_attr_external_ref(
    created_webhook_mock,
    staff_api_client,
    variant,
    permission_manage_translations,
    settings,
):
    # given
    assert variant.translations.count() == 0
    variant.external_reference = "variant-external-reference"
    variant.save(update_fields=["external_reference"])

    translations = [
        {
            "externalReference": variant.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Variant PL",
            },
        },
        {
            "externalReference": variant.external_reference,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "Variant DE",
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkTranslate"]

    # then
    assert variant.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "Variant PL"
    assert data["results"][1]["translation"]["name"] == "Variant DE"
    assert created_webhook_mock.call_count == 1


@patch("saleor.plugins.manager.PluginsManager.translations_updated")
def test_product_variant_bulk_translate_updates_translations_using_attr_external_ref(
    updated_webhook_mock,
    staff_api_client,
    variant_with_translations,
    permission_manage_translations,
    settings,
):
    # given
    assert variant_with_translations.translations.count() == 2
    variant_with_translations.external_reference = "variant-external-reference"
    variant_with_translations.save(update_fields=["external_reference"])

    translations = [
        {
            "externalReference": variant_with_translations.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "NewVariant PL",
            },
        },
        {
            "externalReference": variant_with_translations.external_reference,
            "languageCode": LanguageCodeEnum.DE.name,
            "translationFields": {
                "name": "NewVariant DE",
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkTranslate"]

    # then

    assert variant_with_translations.translations.count() == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["translation"]["name"] == "NewVariant PL"
    assert data["results"][1]["translation"]["name"] == "NewVariant DE"
    assert updated_webhook_mock.call_count == 1


def test_product_variant_bulk_translate_return_error_when_attr_id_and_external_ref(
    staff_api_client,
    variant,
    permission_manage_translations,
    settings,
):
    # given
    assert variant.translations.count() == 0
    variant.external_reference = "variant-external-reference"
    variant.save(update_fields=["external_reference"])
    variant_global_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    translations = [
        {
            "id": variant_global_id,
            "externalReference": variant.external_reference,
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Variant PL",
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkTranslate"]

    # then
    assert variant.translations.count() == 0
    assert data["count"] == 0
    message = "Argument 'id' cannot be combined with 'externalReference'"
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.INVALID.name
    assert error["message"] == message


def test_product_variant_bulk_translate_return_error_when_invalid_attr_id(
    staff_api_client,
    permission_manage_translations,
    settings,
):
    # given
    translations = [
        {
            "id": graphene.Node.to_global_id("ProductVariant", -1),
            "languageCode": LanguageCodeEnum.PL.name,
            "translationFields": {
                "name": "Variant PL",
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkTranslate"]

    # then
    assert data["count"] == 0
    message = "Couldn't resolve to an object."
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.NOT_FOUND.name
    assert error["message"] == message
    assert error["path"] == "id"


def test_product_variant_bulk_translate_return_error_when_invalid_attr_external_ref(
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
        PRODUCT_VARIANT_BULK_TRANSLATE_MUTATION,
        {"translations": translations},
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkTranslate"]

    # then
    assert data["count"] == 0
    message = "Couldn't resolve to an object."
    error = data["results"][0]["errors"][0]
    assert error["code"] == TranslationErrorCode.NOT_FOUND.name
    assert error["message"] == message
    assert error["path"] == "externalReference"
