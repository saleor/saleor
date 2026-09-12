from unittest.mock import ANY, patch

import graphene
import pytest

from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.transport.asynchronous.transport import WebhookPayloadData
from ....core.enums import LanguageCodeEnum, ProductMediaTranslateErrorCode
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

PRODUCT_MEDIA_TRANSLATE_MUTATION = """
    mutation ProductMediaTranslate(
        $id: ID!, $languageCode: LanguageCodeEnum!,
        $input: ProductMediaTranslationInput!
    ) {
        productMediaTranslate(
            id: $id, languageCode: $languageCode, input: $input
        ) {
            productMedia {
                id
                translation(languageCode: $languageCode) {
                    id
                    alt
                    language {
                        code
                    }
                }
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async_for_multiple_objects")
def test_create_translation(
    mocked_webhook_trigger_for_multiple_objects,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    product_media_image,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    translated_alt = "Polish alt text"
    product_media_id = graphene.Node.to_global_id(
        "ProductMedia", product_media_image.pk
    )
    variables = {
        "id": product_media_id,
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {"alt": translated_alt},
    }

    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    data = get_graphql_content(response)["data"]["productMediaTranslate"]
    translation = product_media_image.translations.get(language_code="pl")
    translation_id = graphene.Node.to_global_id(
        "ProductMediaTranslation", translation.pk
    )
    assert data == {
        "productMedia": {
            "id": product_media_id,
            "translation": {
                "id": translation_id,
                "alt": translated_alt,
                "language": {"code": LanguageCodeEnum.PL.name},
            },
        },
        "errors": [],
    }
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


@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async_for_multiple_objects")
def test_update_translation(
    mocked_webhook_trigger_for_multiple_objects,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    product_media_image,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    translation = product_media_image.translations.create(
        language_code="pl", alt="Old alt text"
    )
    translated_alt = "Updated Polish alt text"
    variables = {
        "id": graphene.Node.to_global_id("ProductMedia", product_media_image.pk),
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {"alt": translated_alt},
    }

    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    data = get_graphql_content(response)["data"]["productMediaTranslate"]
    assert data["errors"] == []
    assert data["productMedia"]["translation"]["alt"] == translated_alt
    translation.refresh_from_db(fields=("alt",))
    assert translation.alt == translated_alt
    assert product_media_image.translations.count() == 1
    mocked_webhook_trigger_for_multiple_objects.assert_called_once_with(
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        webhook_payloads_data=[
            WebhookPayloadData(
                subscribable_object=translation, legacy_data_generator=ANY, data=None
            )
        ],
        requestor=staff_api_client.user,
    )


@pytest.mark.parametrize(
    ("_case", "client_fixture", "permission_fixture", "is_allowed"),
    [
        ("unauthenticated", "api_client", None, False),
        ("unprivileged_user", "user_api_client", None, False),
        ("staff_without_permission", "staff_api_client", None, False),
        (
            "staff_with_manage_translations",
            "staff_api_client",
            "permission_manage_translations",
            True,
        ),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.translations_created")
def test_authorization(
    mocked_translations_created,
    request,
    _case,
    client_fixture,
    permission_fixture,
    is_allowed,
    product_media_image,
):
    client = request.getfixturevalue(client_fixture)
    if permission_fixture:
        client.user.user_permissions.add(request.getfixturevalue(permission_fixture))
    translated_alt = "Polish alt text"
    variables = {
        "id": graphene.Node.to_global_id("ProductMedia", product_media_image.pk),
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {"alt": translated_alt},
    }

    response = client.post_graphql(PRODUCT_MEDIA_TRANSLATE_MUTATION, variables)

    if is_allowed:
        data = get_graphql_content(response)["data"]["productMediaTranslate"]
        assert data["errors"] == []
        assert data["productMedia"]["translation"]["alt"] == translated_alt
        translation = product_media_image.translations.get(language_code="pl")
        mocked_translations_created.assert_called_once_with([translation])
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["productMediaTranslate"] is None
        assert product_media_image.translations.exists() is False
        mocked_translations_created.assert_not_called()


def test_create_translation_by_translatable_content_id(
    staff_api_client,
    product_media_image,
    permission_manage_translations,
):
    translated_alt = "Polish alt text"
    variables = {
        "id": graphene.Node.to_global_id(
            "ProductMediaTranslatableContent", product_media_image.pk
        ),
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {"alt": translated_alt},
    }

    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    data = get_graphql_content(response)["data"]["productMediaTranslate"]
    assert data["errors"] == []
    assert data["productMedia"]["translation"]["alt"] == translated_alt
    translation = product_media_image.translations.get(language_code="pl")
    assert translation.alt == translated_alt


@pytest.mark.parametrize(
    ("_case", "translation_input"),
    [
        ("omitted", {}),
        ("explicit_null", {"alt": None}),
    ],
)
def test_null_alt_is_treated_as_omitted(
    _case,
    translation_input,
    staff_api_client,
    product_media_image,
    permission_manage_translations,
):
    variables = {
        "id": graphene.Node.to_global_id("ProductMedia", product_media_image.pk),
        "languageCode": LanguageCodeEnum.PL.name,
        "input": translation_input,
    }

    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    data = get_graphql_content(response)["data"]["productMediaTranslate"]
    assert data["errors"] == []
    assert data["productMedia"]["translation"]["alt"] == ""
    translation = product_media_image.translations.get(language_code="pl")
    assert translation.alt == ""


def test_rejects_alt_above_character_limit(
    staff_api_client,
    product_media_image,
    permission_manage_translations,
):
    character_limit = 250
    translated_alt = "a" * (character_limit + 1)
    variables = {
        "id": graphene.Node.to_global_id("ProductMedia", product_media_image.pk),
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {"alt": translated_alt},
    }

    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    data = get_graphql_content(response)["data"]["productMediaTranslate"]
    assert data["productMedia"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": "alt",
        "code": ProductMediaTranslateErrorCode.INVALID.name,
        "message": (
            f"Ensure this value has at most {character_limit} characters "
            f"(it has {len(translated_alt)})."
        ),
    }
    assert product_media_image.translations.exists() is False


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_media_updated")
def test_does_not_trigger_product_or_product_media_updated_events(
    mocked_product_media_updated,
    mocked_product_updated,
    staff_api_client,
    product_media_image,
    permission_manage_translations,
):
    variables = {
        "id": graphene.Node.to_global_id("ProductMedia", product_media_image.pk),
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {"alt": "Polish alt text"},
    }

    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    data = get_graphql_content(response)["data"]["productMediaTranslate"]
    assert data["errors"] == []
    mocked_product_media_updated.assert_not_called()
    mocked_product_updated.assert_not_called()
