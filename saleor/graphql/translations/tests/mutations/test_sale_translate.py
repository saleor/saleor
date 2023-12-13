from unittest.mock import ANY, patch

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....discount.error_codes import DiscountErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import get_graphql_content

SALE_TRANSLATE_MUTATION = """
    mutation (
        $id: ID!,
        $languageCode: LanguageCodeEnum!,
        $input: NameTranslationInput!
    ) {
        saleTranslate(
            id: $id,
            languageCode: $languageCode,
            input: $input
        ) {
            sale {
                translation(languageCode: $languageCode) {
                    name
                    language {
                        code
                    }
                    id
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
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_sale_translate(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_translations,
    settings,
    description_json,
):
    # given
    promotion = promotion_converted_from_sale
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    promotion_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)

    variables = {
        "id": promotion_id,
        "languageCode": "PL",
        "input": {
            "name": "Polish sale name",
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleTranslate"]
    assert not data["errors"]
    translation_data = data["sale"]["translation"]

    assert translation_data["name"] == "Polish sale name"
    assert translation_data["language"]["code"] == "PL"
    assert translation_data["__typename"] == "SaleTranslation"

    type, _ = graphene.Node.from_global_id(translation_data["id"])
    assert type == "SaleTranslation"

    translation = promotion.translations.first()
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
        legacy_data_generator=ANY,
        allow_replica=False,
    )


def test_sale_translate_by_translatable_content_id(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_translations,
):
    # given
    promotion = promotion_converted_from_sale
    translatable_content_id = graphene.Node.to_global_id(
        "SaleTranslatableContent", promotion.old_sale_id
    )
    variables = {
        "id": translatable_content_id,
        "languageCode": "PL",
        "input": {
            "name": "Polish sale name",
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleTranslate"]
    assert not data["errors"]
    translation_data = data["sale"]["translation"]
    assert translation_data["name"] == "Polish sale name"
    assert translation_data["language"]["code"] == "PL"


def test_sale_translate_not_found_error(
    staff_api_client, permission_manage_translations
):
    # given
    query = SALE_TRANSLATE_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Sale", "0"),
        "languageCode": "PL",
        "input": {
            "name": "Polish sale name",
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_translations]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleTranslate"]["sale"]
    errors = content["data"]["saleTranslate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == DiscountErrorCode.NOT_FOUND.name
