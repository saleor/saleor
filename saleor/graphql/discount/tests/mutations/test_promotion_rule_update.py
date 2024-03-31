from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
from django.test import override_settings

from .....discount import PromotionEvents, RewardValueType
from .....discount.error_codes import PromotionRuleUpdateErrorCode
from .....discount.models import PromotionEvent
from .....product.models import ProductChannelListing
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import RewardTypeEnum, RewardValueTypeEnum
from ...utils import get_variants_for_catalogue_predicate

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
                rewardType
                cataloguePredicate
                orderPredicate
                giftIds
            }
            errors {
                field
                code
                message
                channels
                giftsLimit
                giftsLimitExceedBy
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
    catalogue_promotion,
    product_list,
):
    # given
    promotion = catalogue_promotion
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
    rule.refresh_from_db()

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
    for listing in ProductChannelListing.objects.filter(
        channel__in=rule.channels.all(), product__in=[product_list[1], product_list[2]]
    ):
        assert listing.discounted_price_dirty is True


def test_promotion_rule_update_by_app(
    app_api_client,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
    catalogue_promotion,
    product,
):
    # given
    promotion = catalogue_promotion
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
    rule.refresh_from_db()

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
    for listing in ProductChannelListing.objects.filter(
        channel__in=rule.channels.all(), product=product
    ):
        assert listing.discounted_price_dirty is True


def test_promotion_rule_update_by_customer(
    api_client,
    channel_USD,
    channel_PLN,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
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
    for variant in get_variants_for_catalogue_predicate(rule.catalogue_predicate):
        assert variant.product.discounted_price_dirty is True


def test_promotion_rule_update_duplicates_channels_in_add_and_remove_field(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    collection,
    category,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
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
            "giftsLimit": None,
            "giftsLimitExceedBy": None,
        },
        {
            "code": PromotionRuleUpdateErrorCode.DUPLICATED_INPUT_ITEM.name,
            "field": "removeChannels",
            "message": ANY,
            "channels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)],
            "giftsLimit": None,
            "giftsLimitExceedBy": None,
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
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
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
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
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
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
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


def test_promotion_rule_update_remove_and_add_channel_with_the_same_currency(
    app_api_client,
    permission_manage_discounts,
    channel_USD,
    other_channel_USD,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    rule = promotion.rules.get(name="Fixed promotion rule")
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    add_channel_ids = [graphene.Node.to_global_id("Channel", other_channel_USD.pk)]
    reward_value = Decimal("10")

    variables = {
        "id": rule_id,
        "input": {
            "removeChannels": remove_channel_ids,
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
    assert data["promotionRule"]
    assert len(data["promotionRule"]["channels"]) == 1
    assert data["promotionRule"]["channels"][0]["slug"] == other_channel_USD.slug


def test_promotion_rule_update_change_reward_value_type_to_fixed_multiple_channels(
    app_api_client,
    permission_manage_discounts,
    channel_PLN,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
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
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
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
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
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
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
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
    rule.refresh_from_db()

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

    for listing in ProductChannelListing.objects.filter(
        channel__in=rule.channels.all(), product__in=[product_list[1], product_list[2]]
    ):
        assert listing.discounted_price_dirty is True


def test_promotion_rule_update_events(
    staff_api_client,
    permission_group_manage_discounts,
    channel_PLN,
    category,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
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


def test_promotion_rule_update_mix_predicates_invalid_order_predicate(
    app_api_client,
    permission_manage_discounts,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    rule = promotion.rules.get(name="Percentage promotion rule")
    assert rule.catalogue_predicate
    assert not rule.order_predicate
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }

    variables = {
        "id": rule_id,
        "input": {"orderPredicate": order_predicate},
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
    assert errors[0]["field"] == "orderPredicate"


def test_promotion_rule_update_mix_predicates_invalid_catalogue_predicate(
    app_api_client,
    permission_manage_discounts,
    order_promotion_with_rule,
    product,
):
    # given
    promotion = order_promotion_with_rule
    rule = promotion.rules.first()
    assert not rule.catalogue_predicate
    assert rule.order_predicate
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }

    variables = {
        "id": rule_id,
        "input": {"cataloguePredicate": catalogue_predicate},
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
    assert errors[0]["field"] == "cataloguePredicate"


def test_promotion_rule_update_mix_predicates_both_predicate_types_given(
    app_api_client,
    product,
    permission_manage_discounts,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    rule = promotion.rules.get(name="Percentage promotion rule")
    assert rule.catalogue_predicate
    assert not rule.order_predicate
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }

    variables = {
        "id": rule_id,
        "input": {
            "orderPredicate": order_predicate,
            "cataloguePredicate": catalogue_predicate,
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
    assert {
        "code": PromotionRuleUpdateErrorCode.INVALID.name,
        "field": "orderPredicate",
        "message": ANY,
        "channels": None,
        "giftsLimit": None,
        "giftsLimitExceedBy": None,
    } in errors


def test_promotion_rule_update_reward_type_with_catalogue_predicate(
    app_api_client,
    permission_manage_discounts,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    rule = promotion.rules.get(name="Percentage promotion rule")
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name

    variables = {
        "id": rule_id,
        "input": {"rewardType": reward_type},
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
    assert errors[0]["field"] == "rewardType"


def test_promotion_rule_update_clear_reward_type_for_order_predicate(
    app_api_client,
    permission_manage_discounts,
    order_promotion_with_rule,
):
    # given
    promotion = order_promotion_with_rule
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)
    variables = {
        "id": rule_id,
        "input": {"rewardType": None},
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
    assert errors[0]["code"] == PromotionRuleUpdateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "rewardType"


def test_promotion_rule_update_add_invalid_channels_for_order_rule(
    app_api_client,
    permission_manage_discounts,
    order_promotion_with_rule,
    channel_PLN,
):
    # given
    promotion = order_promotion_with_rule
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.pk)
    variables = {
        "id": rule_id,
        "input": {"addChannels": [channel_id]},
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


def test_promotion_rule_update_gift_promotion(
    app_api_client,
    permission_manage_discounts,
    gift_promotion_rule,
    product_variant_list,
):
    # given
    rule = gift_promotion_rule
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list
    ]
    current_gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in rule.gifts.all()
    ]
    variables = {
        "id": rule_id,
        "input": {
            "orderPredicate": order_predicate,
            "addGifts": gift_ids,
        },
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    gift_ids = set(gift_ids) | set(current_gift_ids)
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    assert not data["errors"]
    rule_data = data["promotionRule"]
    assert sorted(rule_data["giftIds"]) == sorted(gift_ids)
    assert rule_data["orderPredicate"] == order_predicate
    rule.refresh_from_db()
    assert rule.reward_type == RewardTypeEnum.GIFT.value
    assert rule.order_predicate == order_predicate


def test_promotion_rule_update_gift_promotion_wrong_gift_instance(
    app_api_client,
    permission_manage_discounts,
    gift_promotion_rule,
    product_list,
):
    # given
    rule = gift_promotion_rule
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)
    gift_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]
    variables = {
        "id": rule_id,
        "input": {
            "addGifts": gift_ids,
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
    assert errors[0]["code"] == PromotionRuleUpdateErrorCode.INVALID_GIFT_TYPE.name
    assert errors[0]["field"] == "addGifts"


def test_promotion_rule_update_gift_promotion_with_reward_value(
    app_api_client,
    permission_manage_discounts,
    gift_promotion_rule,
):
    # given
    rule = gift_promotion_rule
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)
    variables = {
        "id": rule_id,
        "input": {"rewardValue": Decimal(100)},
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


def test_promotion_rule_update_gift_promotion_with_reward_value_type(
    app_api_client,
    permission_manage_discounts,
    gift_promotion_rule,
):
    # given
    rule = gift_promotion_rule
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)
    variables = {
        "id": rule_id,
        "input": {"rewardValueType": RewardValueTypeEnum.PERCENTAGE.name},
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
    assert errors[0]["field"] == "rewardValueType"


def test_promotion_rule_update_gift_promotion_remove_gifts(
    app_api_client,
    permission_manage_discounts,
    gift_promotion_rule,
    product_list,
):
    # given
    rule = gift_promotion_rule
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", gift.id)
        for gift in gift_promotion_rule.gifts.all()
    ]
    variables = {
        "id": rule_id,
        "input": {
            "removeGifts": gift_ids,
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
    assert errors[0]["code"] == PromotionRuleUpdateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "gifts"


@override_settings(GIFTS_LIMIT_PER_RULE=1)
def test_promotion_rule_update_exceeds_gifts_number_limit(
    app_api_client,
    permission_manage_discounts,
    gift_promotion_rule,
    product_variant_list,
):
    # given
    gift_limit = 1
    rule = gift_promotion_rule
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list
    ]
    current_gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in rule.gifts.all()
    ]
    variables = {
        "id": rule_id,
        "input": {
            "addGifts": gift_ids,
        },
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    gift_ids = set(gift_ids) | set(current_gift_ids)
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleUpdateErrorCode.GIFTS_NUMBER_LIMIT.name
    assert errors[0]["field"] == "gifts"
    assert errors[0]["giftsLimit"] == gift_limit
    assert errors[0]["giftsLimitExceedBy"] == len(gift_ids) - gift_limit
