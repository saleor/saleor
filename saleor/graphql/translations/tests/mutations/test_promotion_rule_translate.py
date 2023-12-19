import json
from unittest.mock import ANY, patch

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import assert_no_permission, get_graphql_content

PROMOTION_RULE_TRANSLATE_MUTATION = """
    mutation (
        $id: ID!,
        $languageCode: LanguageCodeEnum!,
        $input: PromotionRuleTranslationInput!
    ) {
        promotionRuleTranslate(
            id: $id,
            languageCode: $languageCode,
            input: $input
        ) {
            promotionRule {
                translation(languageCode: $languageCode) {
                    name
                    description
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


@freeze_time("2023-06-01 10:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_promotion_rule_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    promotion_rule,
    permission_manage_translations,
    settings,
    description_json,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    rule_id = graphene.Node.to_global_id("PromotionRule", promotion_rule.id)

    variables = {
        "id": rule_id,
        "languageCode": "PL",
        "input": {
            "name": "Polish rule name",
            "description": description_json,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_RULE_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleTranslate"]
    assert not data["errors"]
    translation_data = data["promotionRule"]["translation"]

    assert translation_data["name"] == "Polish rule name"
    assert translation_data["description"] == json.dumps(description_json)
    assert translation_data["language"]["code"] == "PL"

    translation = promotion_rule.translations.first()
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
        legacy_data_generator=ANY,
        allow_replica=False,
    )


def test_promotion_rule_update_translation(
    staff_api_client,
    promotion_rule,
    promotion_rule_translation_fr,
    permission_manage_translations,
):
    # given
    assert promotion_rule.translations.first().name == "French promotion rule name"
    rule_id = graphene.Node.to_global_id("PromotionRule", promotion_rule.id)
    updated_name = "Updated French rule name"

    variables = {
        "id": rule_id,
        "languageCode": "FR",
        "input": {
            "name": updated_name,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_RULE_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleTranslate"]
    assert not data["errors"]
    translation_data = data["promotionRule"]["translation"]

    assert translation_data["name"] == updated_name
    assert translation_data["language"]["code"] == "FR"
    assert promotion_rule.translations.first().name == updated_name


def test_promotion_rule_create_translation_no_permission(
    staff_api_client,
    promotion_rule,
):
    # given
    rule_id = graphene.Node.to_global_id("PromotionRule", promotion_rule.id)
    variables = {
        "id": rule_id,
        "languageCode": "PL",
        "input": {
            "name": "Polish rule name",
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_RULE_TRANSLATE_MUTATION,
        variables,
    )

    # then
    assert_no_permission(response)


def test_promotion_rule_create_translation_by_translatable_content_id(
    staff_api_client,
    promotion_rule,
    permission_manage_translations,
):
    # given
    translatable_content_id = graphene.Node.to_global_id(
        "PromotionRuleTranslatableContent", promotion_rule.id
    )
    variables = {
        "id": translatable_content_id,
        "languageCode": "PL",
        "input": {
            "name": "Polish rule name",
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_RULE_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleTranslate"]
    assert not data["errors"]
    translation_data = data["promotionRule"]["translation"]
    assert translation_data["name"] == "Polish rule name"
    assert translation_data["language"]["code"] == "PL"


def test_promotion_rule_create_translation_clear_old_sale_id(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_translations,
):
    promotion = promotion_converted_from_sale
    assert promotion.old_sale_id
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    variables = {
        "id": rule_id,
        "languageCode": "PL",
        "input": {
            "name": "Polish rule name",
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_RULE_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleTranslate"]
    assert not data["errors"]
    translation_data = data["promotionRule"]["translation"]

    assert translation_data["name"] == "Polish rule name"
    assert translation_data["language"]["code"] == "PL"

    promotion.refresh_from_db()
    assert not promotion.old_sale_id
