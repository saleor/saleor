from decimal import Decimal
from unittest.mock import ANY, patch

import graphene

from .....discount import PromotionEvents, RewardValueType
from .....discount.error_codes import PromotionRuleUpdateErrorCode
from .....discount.models import PromotionEvent
from .....product.models import Product
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import RewardValueTypeEnum
from ...utils import get_variants_for_predicate

PROMOTION_RULE_UPDATE_MUTATION = """
    mutation promotionRuleUpdate($id: ID!, $input: PromotionRuleUpdateInput!) {
        promotionRuleUpdate(id: $id, input: $input) {
            promotionRule {
                name
                description
                promotion {
                    id
                    events {
                        ... on PromotionEventInterface {
                            type
                        }
                        ... on PromotionRuleEventInterface {
                            ruleId
                        }
                    }
                }
                channels {
                    slug
                }
                rewardValueType
                rewardValue
                cataloguePredicate
            }
            errors {
                field
                code
                message
                channels
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.promotion_rule_updated")
def test_promotion_rule_update_by_staff_user(
    promotion_rule_updated_mock,
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    collection,
    category,
    promotion,
    product_list,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion.rules.create(
        name="Rule",
        promotion=promotion,
        description=None,
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product_list[0].id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("5"),
    )
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [
                        graphene.Node.to_global_id(
                            "ProductVariant", product_list[1].variants.first().id
                        )
                    ]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    collection.products.add(product_list[2])
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == rule.name
    assert rule_data["description"] == rule.description
    assert len(rule_data["channels"]) == 1
    assert rule_data["channels"][0]["slug"] == channel_PLN.slug
    assert rule_data["cataloguePredicate"] == catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count
    promotion_rule_updated_mock.assert_called_once_with(rule)
    for product in Product.objects.filter(
        id__in=[product_list[1].id, product_list[2].id]
    ):
        assert product.discounted_price_dirty is True


def test_promotion_rule_update_by_app(
    app_api_client,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
    promotion,
    product,
):
    # given
    rule = promotion.rules.get(name="Percentage promotion rule")
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
        },
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    product.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == rule.name
    assert rule_data["description"] == rule.description
    assert len(rule_data["channels"]) == 1
    assert rule_data["channels"][0]["slug"] == channel_PLN.slug
    assert rule_data["cataloguePredicate"] == rule.catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count
    assert product.discounted_price_dirty is True


def test_promotion_rule_update_by_customer(
    api_client,
    channel_USD,
    channel_PLN,
    promotion,
):
    # given
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
        },
    }

    # when
    response = api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)
    for variant in get_variants_for_predicate(rule.catalogue_predicate):
        assert variant.product.discounted_price_dirty is True


def test_promotion_rule_update_duplicates_channels_in_add_and_remove_field(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    collection,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_PLN, channel_USD]
    ]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 2
    expected_errors = [
        {
            "code": PromotionRuleUpdateErrorCode.DUPLICATED_INPUT_ITEM.name,
            "field": "addChannels",
            "message": ANY,
            "channels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)],
        },
        {
            "code": PromotionRuleUpdateErrorCode.DUPLICATED_INPUT_ITEM.name,
            "field": "removeChannels",
            "message": ANY,
            "channels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)],
        },
    ]
    for error in expected_errors:
        assert error in errors


def test_promotion_rule_update_invalid_catalogue_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    collection,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
        ],
        "AND": [
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ],
    }
    reward_value = Decimal("10")

    variables = {
        "id": rule_id,
        "input": {
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleUpdateErrorCode.INVALID.name
    assert errors[0]["field"] == "cataloguePredicate"


def test_promotion_rule_update_add_channel_with_different_currency_to_fixed_discount(
    app_api_client,
    permission_manage_discounts,
    channel_PLN,
    promotion,
):
    # given
    rule = promotion.rules.get(name="Fixed promotion rule")
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    reward_value = Decimal("10")

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "rewardValue": reward_value,
        },
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == PromotionRuleUpdateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.name
    )
    assert errors[0]["field"] == "addChannels"


def test_promotion_rule_update_remove_last_channel_from_fixed_discount(
    app_api_client,
    permission_manage_discounts,
    channel_USD,
    promotion,
):
    # given
    rule = promotion.rules.get(name="Fixed promotion rule")
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    reward_value = Decimal("10")

    variables = {
        "id": rule_id,
        "input": {
            "removeChannels": remove_channel_ids,
            "rewardValue": reward_value,
        },
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleUpdateErrorCode.MISSING_CHANNELS.name
    assert errors[0]["field"] == "removeChannels"


def test_promotion_rule_update_change_reward_value_type_to_fixed_multiple_channels(
    app_api_client,
    permission_manage_discounts,
    channel_PLN,
    promotion,
):
    # given
    rule = promotion.rules.get(name="Percentage promotion rule")
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    rule.channels.add(channel_PLN)

    reward_value_type = RewardValueTypeEnum.FIXED.name

    variables = {
        "id": rule_id,
        "input": {
            "rewardValueType": reward_value_type,
        },
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == PromotionRuleUpdateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.name
    )
    assert errors[0]["field"] == "rewardValueType"


def test_promotion_rule_update_change_reward_value_type_to_fixed_no_channels(
    app_api_client,
    permission_manage_discounts,
    promotion,
):
    # given
    rule = promotion.rules.get(name="Percentage promotion rule")
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    rule.channels.clear()

    reward_value_type = RewardValueTypeEnum.FIXED.name

    variables = {
        "id": rule_id,
        "input": {
            "rewardValueType": reward_value_type,
        },
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleUpdateErrorCode.MISSING_CHANNELS.name
    assert errors[0]["field"] == "rewardValueType"


def test_promotion_rule_update_reward_value_invalid_precision(
    app_api_client,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
    promotion,
):
    # given
    rule = promotion.rules.get(name="Fixed promotion rule")
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    reward_value = Decimal("10.12212")

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValue": reward_value,
        },
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleUpdateErrorCode.INVALID_PRECISION.name
    assert errors[0]["field"] == "rewardValue"


def test_promotion_rule_update_reward_value_invalid_percentage_value(
    app_api_client,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
    promotion,
):
    # given
    rule = promotion.rules.get(name="Percentage promotion rule")
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    reward_value = Decimal("101")

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValue": reward_value,
        },
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleUpdateErrorCode.INVALID.name
    assert errors[0]["field"] == "rewardValue"


def test_promotion_rule_update_clears_old_sale_id(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    collection,
    promotion_converted_from_sale,
    product_list,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion = promotion_converted_from_sale

    assert promotion.old_sale_id

    rule = promotion.rules.create(
        name="Rule",
        promotion=promotion,
        description=None,
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product_list[0].id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("5"),
    )
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [
                        graphene.Node.to_global_id(
                            "ProductVariant", product_list[1].variants.first().id
                        )
                    ]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    collection.products.add(product_list[2])
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == rule.name
    assert rule_data["description"] == rule.description
    assert len(rule_data["channels"]) == 1
    assert rule_data["channels"][0]["slug"] == channel_PLN.slug
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count

    promotion.refresh_from_db()
    assert promotion.old_sale_id is None

    for product in Product.objects.filter(
        id__in=[product_list[1].id, product_list[2].id]
    ):
        assert product.discounted_price_dirty is True


def test_promotion_rule_update_events(
    staff_api_client,
    permission_group_manage_discounts,
    channel_PLN,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
        ]
    }
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        },
    }
    event_count = PromotionEvent.objects.count()

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    assert not data["errors"]

    events = data["promotionRule"]["promotion"]["events"]
    assert len(events) == 1
    assert PromotionEvent.objects.count() == event_count + 1
    assert PromotionEvents.RULE_UPDATED.upper() == events[0]["type"]

    assert events[0]["ruleId"] == rule_id
