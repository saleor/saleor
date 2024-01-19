import json

import pytest

from ..product.utils.preparing_product import prepare_product
from ..promotions.utils import (
    create_promotion,
    create_promotion_rule,
    translate_promotion,
    translate_promotion_rule,
)
from ..shop.utils.preparing_shop import prepare_default_shop
from ..translations.utils import get_translations
from ..utils import assign_permissions


def prepare_promotion(
    e2e_staff_api_client,
    discount_value,
    discount_type,
    promotion_name="Promotion Test",
    promotion_rule_name="Test rule",
    product_ids=None,
    channel_id=None,
):
    promotion_description = {
        "blocks": [{"data": {"text": "promotion description"}, "type": "paragraph"}],
        "version": "1.0.0",
    }
    promotion_type = "CATALOGUE"
    promotion_data = create_promotion(
        e2e_staff_api_client,
        promotion_name,
        promotion_type,
        description=promotion_description,
    )
    promotion_id = promotion_data["id"]

    predicate_input = {"productPredicate": {"ids": product_ids}}
    rule_description = {
        "blocks": [{"data": {"text": "rule description"}, "type": "paragraph"}],
        "version": "1.0.0",
    }
    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": promotion_rule_name,
        "cataloguePredicate": predicate_input,
        "rewardValue": discount_value,
        "rewardValueType": discount_type,
        "description": rule_description,
    }
    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        input,
    )
    promotion_rule_id = promotion_rule["id"]
    discount_value = promotion_rule["rewardValue"]

    return promotion_id, promotion_rule_id


@pytest.mark.e2e
def test_staff_translate_promotions_core_2119(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_translations,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_translations,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    warehouse_id = shop_data["warehouse"]["id"]

    product_id, _product_variant_id, _ = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, "37.99"
    )

    promotion_id, promotion_rule_id = prepare_promotion(
        e2e_staff_api_client,
        5,
        "FIXED",
        product_ids=[product_id],
        channel_id=channel_id,
    )
    # Step 1 - Get list of promotions translations
    translations_data = get_translations(
        e2e_staff_api_client, "PROMOTION", language="PL"
    )
    promotion_translation_list = translations_data["translations"]["edges"]
    assert len(promotion_translation_list) == 1
    assert promotion_translation_list[0]["node"]["name"] == "Promotion Test"

    # Step 2 - Translate promotion name and description
    promotion_translated_description = {
        "blocks": [{"data": {"text": "Opis promocji"}, "type": "paragraph"}],
        "version": "1.0.0",
    }
    promotion_translate_input = {
        "name": "Promocja Testowa",
        "description": promotion_translated_description,
    }
    promotion_translation_data = translate_promotion(
        e2e_staff_api_client, promotion_id, "PL", promotion_translate_input
    )

    assert promotion_translation_data["language"]["code"] == "PL"
    assert promotion_translation_data["name"] == "Promocja Testowa"
    assert promotion_translation_data["description"] == json.dumps(
        promotion_translated_description
    )

    # Step 3 - Get list of promotions rules translations
    translations_data = get_translations(
        e2e_staff_api_client, "PROMOTION_RULE", language="PL"
    )
    rules_translation_list = translations_data["translations"]["edges"]
    assert len(rules_translation_list) == 1
    assert rules_translation_list[0]["node"]["id"] is not None

    # Step 4 - Translate promotion rule name and description
    rule_translated_description = {
        "blocks": [{"data": {"text": "Opis reguły"}, "type": "paragraph"}],
        "version": "1.0.0",
    }
    promotion_rule_translate_input = {
        "name": "Testowa Reguła",
        "description": rule_translated_description,
    }
    promotion_rule_translation_data = translate_promotion_rule(
        e2e_staff_api_client, promotion_rule_id, "PL", promotion_rule_translate_input
    )

    assert promotion_rule_translation_data["language"]["code"] == "PL"
    assert promotion_rule_translation_data["name"] == "Testowa Reguła"
    assert promotion_rule_translation_data["description"] == json.dumps(
        rule_translated_description
    )
