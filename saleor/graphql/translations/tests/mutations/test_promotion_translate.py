import json
from unittest.mock import ANY, patch

import graphene
import pytest
from freezegun import freeze_time

from .....core.error_codes import TranslationErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.transport.asynchronous.transport import WebhookPayloadData
from ....core.enums import LanguageCodeEnum
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

PROMOTION_TRANSLATE_MUTATION = """
    mutation (
        $id: ID!,
        $languageCode: LanguageCodeEnum!,
        $input: PromotionTranslationInput!
    ) {
        promotionTranslate(
            id: $id,
            languageCode: $languageCode,
            input: $input
        ) {
            promotion {
                translation(languageCode: $languageCode) {
                    name
                    description
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


@freeze_time("2023-06-01 10:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async_for_multiple_objects")
def test_promotion_create_translation(
    mocked_webhook_trigger_for_multiple_objects,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    catalogue_promotion,
    permission_manage_translations,
    settings,
    description_json,
):
    # given
    promotion = catalogue_promotion
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    variables = {
        "id": promotion_id,
        "languageCode": "PL",
        "input": {
            "name": "Polish promotion name",
            "description": description_json,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionTranslate"]
    assert not data["errors"]
    translation_data = data["promotion"]["translation"]

    assert translation_data["name"] == "Polish promotion name"
    assert json.loads(translation_data["description"]) == description_json
    assert translation_data["language"]["code"] == "PL"
    assert translation_data["__typename"] == "PromotionTranslation"

    translation = promotion.translations.first()
    mocked_webhook_trigger_for_multiple_objects.assert_called_once_with(
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        webhook_payloads_data=[
            WebhookPayloadData(
                subscribable_object=translation, legacy_data_generator=ANY, data=None
            )
        ],
        requestor=staff_api_client.user,
    )


def test_promotion_update_translation(
    staff_api_client,
    catalogue_promotion,
    promotion_translation_fr,
    permission_manage_translations,
):
    # given
    promotion = catalogue_promotion
    assert promotion.translations.first().name == "French promotion name"
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    updated_name = "Updated French promotion name."

    variables = {
        "id": promotion_id,
        "languageCode": "FR",
        "input": {
            "name": updated_name,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionTranslate"]
    assert not data["errors"]
    translation_data = data["promotion"]["translation"]

    assert translation_data["name"] == updated_name
    assert translation_data["language"]["code"] == "FR"
    assert promotion.translations.first().name == updated_name


def test_promotion_create_translation_no_permission(
    staff_api_client,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    variables = {
        "id": promotion_id,
        "languageCode": "PL",
        "input": {
            "name": "Polish promotion name",
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_TRANSLATE_MUTATION,
        variables,
    )

    # then
    assert_no_permission(response)


def test_promotion_create_translation_by_translatable_content_id(
    staff_api_client,
    catalogue_promotion,
    permission_manage_translations,
):
    # given
    promotion = catalogue_promotion
    translatable_content_id = graphene.Node.to_global_id(
        "PromotionTranslatableContent", promotion.id
    )
    variables = {
        "id": translatable_content_id,
        "languageCode": "PL",
        "input": {
            "name": "Polish promotion name",
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionTranslate"]
    assert not data["errors"]
    translation_data = data["promotion"]["translation"]
    assert translation_data["name"] == "Polish promotion name"
    assert translation_data["language"]["code"] == "PL"


def test_promotion_translate_clear_old_sale_id(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_translations,
):
    # given
    promotion = promotion_converted_from_sale
    assert promotion.old_sale_id
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    variables = {
        "id": promotion_id,
        "languageCode": "PL",
        "input": {
            "name": "Polish promotion name",
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionTranslate"]
    assert not data["errors"]
    translation_data = data["promotion"]["translation"]
    assert translation_data["name"] == "Polish promotion name"
    assert translation_data["language"]["code"] == "PL"
    assert translation_data["__typename"] == "PromotionTranslation"

    promotion.refresh_from_db()
    assert not promotion.old_sale_id


PROMOTION_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation (
        $id: ID,
        $externalReference: String,
        $languageCode: LanguageCodeEnum!,
        $input: PromotionTranslationInput!
    ) {
        promotionTranslate(
            id: $id,
            externalReference: $externalReference,
            languageCode: $languageCode,
            input: $input
        ) {
            promotion {
                externalReference
                translation(languageCode: $languageCode) {
                    name
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
    staff_api_client, catalogue_promotion, permission_manage_translations, mocker
):
    # given
    external_reference = "promotion-ext-ref"
    catalogue_promotion.external_reference = external_reference
    catalogue_promotion.save(update_fields=["external_reference"])
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    language_code = LanguageCodeEnum.PL
    name = "Polish promotion"
    variables = {
        "externalReference": external_reference,
        "languageCode": language_code.name,
        "input": {"name": name},
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["promotionTranslate"]
    assert data["errors"] == []
    assert data["promotion"] == {
        "externalReference": external_reference,
        "translation": {
            "name": name,
            "language": {"code": language_code.name},
        },
    }
    translation = catalogue_promotion.translations.get(
        language_code=language_code.value
    )
    assert translation.name == name
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
    catalogue_promotion,
    permission_manage_translations,
    mocker,
):
    # given
    catalogue_promotion.external_reference = "existing-reference"
    catalogue_promotion.save(update_fields=["external_reference"])
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id(
            "Promotion", catalogue_promotion.pk
        )
    variables["languageCode"] = LanguageCodeEnum.PL.name
    variables["input"] = {"name": "Polish promotion"}

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["promotionTranslate"]
    assert data["promotion"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    assert catalogue_promotion.translations.exists() is False
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
    catalogue_promotion,
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
    catalogue_promotion.external_reference = external_reference
    catalogue_promotion.save(update_fields=["external_reference"])
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    language_code = LanguageCodeEnum.PL
    name = "Polish promotion"
    variables = {
        "externalReference": external_reference,
        "languageCode": language_code.name,
        "input": {"name": name},
    }

    # when
    response = client.post_graphql(
        PROMOTION_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["promotionTranslate"]
        assert data["errors"] == []
        assert data["promotion"]["translation"]["name"] == name
        translation = catalogue_promotion.translations.get(
            language_code=language_code.value
        )
        assert translation.name == name
        mocked_translations_created.assert_called_once_with([translation])
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"promotionTranslate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["promotionTranslate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_TRANSLATIONS"
        )
        assert catalogue_promotion.translations.exists() is False
        mocked_translations_created.assert_not_called()
