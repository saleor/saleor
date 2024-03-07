from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
from django.test import override_settings

from .....discount import PromotionEvents
from .....discount.error_codes import PromotionRuleCreateErrorCode
from .....discount.models import PromotionEvent
from .....product.models import ProductChannelListing
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import RewardTypeEnum, RewardValueTypeEnum

PROMOTION_RULE_CREATE_MUTATION = """
    mutation promotionRuleCreate($input: PromotionRuleCreateInput!) {
        promotionRuleCreate(input: $input) {
            promotionRule {
                id
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
                    id
                }
                rewardValueType
                rewardValue
                rewardType
                predicateType
                cataloguePredicate
                orderPredicate
                giftIds
            }
            errors {
                field
                code
                message
                rulesLimit
                rulesLimitExceedBy
                giftsLimit
                giftsLimitExceedBy
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.promotion_rule_created")
def test_promotion_rule_create_by_staff_user(
    promotion_rule_created_mock,
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    collection,
    category,
    catalogue_promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion = catalogue_promotion

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            },
            {
                "productPredicate": {
                    "ids": [graphene.Node.to_global_id("Product", product.id)]
                }
            },
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
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
            "gifts": None,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]
    product.refresh_from_db()
    listings = ProductChannelListing.objects.filter(
        channel__in=[channel_USD, channel_PLN], product=product
    )

    assert not data["errors"]
    assert rule_data["name"] == name
    assert rule_data["description"] == description_json
    assert {channel["id"] for channel in rule_data["channels"]} == set(channel_ids)
    assert rule_data["predicateType"] == promotion.type.upper()
    assert rule_data["cataloguePredicate"] == catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count + 1
    rule = promotion.rules.last()
    promotion_rule_created_mock.assert_called_once_with(rule)
    for listing in listings:
        assert listing.discounted_price_dirty is True


def test_promotion_rule_create_by_app(
    app_api_client,
    permission_manage_discounts,
    description_json,
    channel_PLN,
    collection,
    category,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
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
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_CREATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == name
    assert rule_data["description"] == description_json
    assert {channel["id"] for channel in rule_data["channels"]} == set(channel_ids)
    assert rule_data["predicateType"] == promotion.type.upper()
    assert rule_data["cataloguePredicate"] == catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count + 1


def test_promotion_rule_create_by_customer(
    api_client,
    description_json,
    channel_USD,
    category,
    collection,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
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
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)
    assert_no_permission(response)

    # then
    product = category.products.first()
    listing = ProductChannelListing.objects.get(channel=channel_USD, product=product)
    assert listing.discounted_price_dirty is False


def test_promotion_rule_create_missing_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    order_promotion_with_rule,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion = order_promotion_with_rule

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert {
        "code": PromotionRuleCreateErrorCode.REQUIRED.name,
        "field": "orderPredicate",
        "message": ANY,
        "rulesLimit": None,
        "rulesLimitExceedBy": None,
        "giftsLimit": None,
        "giftsLimitExceedBy": None,
    } in errors
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_missing_reward_value(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    name = "test promotion rule"
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "rewardValue"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_missing_reward_value_type(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "rewardValueType"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_multiple_errors(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    name = "test promotion rule"
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert len(errors) == 2
    expected_errors = [
        {
            "code": PromotionRuleCreateErrorCode.REQUIRED.name,
            "field": "rewardValue",
            "message": ANY,
            "rulesLimit": None,
            "rulesLimitExceedBy": None,
            "giftsLimit": None,
            "giftsLimitExceedBy": None,
        },
        {
            "code": PromotionRuleCreateErrorCode.REQUIRED.name,
            "field": "rewardValueType",
            "message": ANY,
            "rulesLimit": None,
            "rulesLimitExceedBy": None,
            "giftsLimit": None,
            "giftsLimitExceedBy": None,
        },
    ]
    for error in expected_errors:
        assert error in errors

    assert promotion.rules.count() == rules_count


def test_promotion_rule_invalid_catalogue_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    collection,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                },
                "AND": [
                    {
                        "productPredicate": {
                            "ids": [graphene.Node.to_global_id("Product", product.id)]
                        }
                    }
                ],
            }
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "cataloguePredicate"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_invalid_order_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_PLN,
    order_promotion_without_rules,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    order_predicate = {
        "OR": [
            {
                "discountedObjectPredicate": {
                    "baseSubtotalPrice": {"range": {"gte": 100}}
                },
                "AND": [
                    {
                        "discountedObjectPredicate": {
                            "baseSubtotalPrice": {"range": {"lte": 500}}
                        }
                    }
                ],
            }
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardType": RewardTypeEnum.SUBTOTAL_DISCOUNT.name,
            "rewardValue": reward_value,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "orderPredicate"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_invalid_price_precision(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    collection,
    category,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
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
    name = "test promotion rule"
    reward_value = Decimal("10.12345")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID_PRECISION.name
    assert errors[0]["field"] == "rewardValue"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_fixed_reward_value_multiple_currencies(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    collection,
    category,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
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
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == PromotionRuleCreateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.name
    )
    assert errors[0]["field"] == "rewardValueType"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_fixed_reward_no_channels(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    collection,
    category,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

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
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.MISSING_CHANNELS.name
    assert errors[0]["field"] == "channels"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_percentage_value_above_100(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    collection,
    category,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
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
    name = "test promotion rule"
    reward_value = Decimal("110")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "rewardValue"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_clears_old_sale_id(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    promotion_converted_from_sale,
):
    # given
    promotion = promotion_converted_from_sale
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    assert promotion.old_sale_id
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            }
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]
    product.refresh_from_db()
    listings = ProductChannelListing.objects.filter(
        channel__in=[channel_USD, channel_PLN], product=product
    )
    assert not data["errors"]
    assert rule_data["name"] == name
    assert rule_data["description"] == description_json
    assert {channel["id"] for channel in rule_data["channels"]} == set(channel_ids)
    assert rule_data["predicateType"] == promotion.type.upper()
    assert rule_data["cataloguePredicate"] == catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count + 1

    for listing in listings:
        assert listing.discounted_price_dirty is True

    promotion.refresh_from_db()
    assert promotion.old_sale_id is None


def test_promotion_rule_create_events(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    variant,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            },
        ]
    }
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    variables = {
        "input": {
            "name": "test promotion rule",
            "promotion": promotion_id,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }
    event_count = PromotionEvent.objects.count()

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    assert not data["errors"]

    events = data["promotionRule"]["promotion"]["events"]
    assert len(events) == 1
    assert PromotionEvent.objects.count() == event_count + 1
    assert PromotionEvents.RULE_CREATED.upper() == events[0]["type"]

    assert events[0]["ruleId"] == data["promotionRule"]["id"]


@patch("saleor.plugins.manager.PluginsManager.promotion_rule_created")
def test_promotion_rule_create_serializable_decimal_in_predicate(
    promotion_rule_created_mock,
    staff_api_client,
    permission_group_manage_discounts,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    catalogue_predicate = {
        "productPredicate": {"minimalPrice": {"range": {"gte": "25"}}}
    }
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    variables = {
        "input": {
            "promotion": promotion_id,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    assert not data["errors"]
    assert data["promotionRule"]["cataloguePredicate"] == catalogue_predicate


def test_promotion_rule_create_multiple_predicates(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    product,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert {
        "code": PromotionRuleCreateErrorCode.INVALID.name,
        "field": "orderPredicate",
        "message": ANY,
        "rulesLimit": None,
        "rulesLimitExceedBy": None,
        "giftsLimit": None,
        "giftsLimitExceedBy": None,
    } in errors
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_mixed_predicates_order(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    product,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "orderPredicate"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_mixed_predicates_catalogue(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    product,
    order_promotion_without_rules,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "orderPredicate": order_predicate,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "cataloguePredicate"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_missing_reward_type(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    product,
    order_promotion_without_rules,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "rewardType"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_reward_type_with_catalogue_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    product,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "rewardType": reward_type,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "rewardType"
    assert promotion.rules.count() == rules_count


@patch("saleor.plugins.manager.PluginsManager.promotion_rule_created")
def test_promotion_rule_create_order_predicate(
    promotion_rule_created_mock,
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    order_promotion_without_rules,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }

    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == name
    assert rule_data["description"] == description_json
    assert rule_data["channels"][0]["id"] == channel_id
    assert rule_data["orderPredicate"] == order_predicate
    assert rule_data["predicateType"] == promotion.type.upper()
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["rewardType"] == reward_type.upper()
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count + 1
    rule = promotion.rules.last()
    assert not rule.variants_dirty
    promotion_rule_created_mock.assert_called_once_with(rule)


def test_promotion_rule_create_mixed_currencies_for_price_based_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    order_promotion_without_rules,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]

    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == PromotionRuleCreateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.name
    )
    assert errors[0]["field"] == "channels"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_with_metadata(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    collection,
    category,
    catalogue_promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [{"variantPredicate": {"metadata": [{"key": "test", "value": "test"}]}}]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", catalogue_promotion.id)

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]

    assert not data["errors"]
    assert data["promotionRule"]


@override_settings(ORDER_RULES_LIMIT=1)
def test_promotion_rule_create_exceeds_rules_number_limit(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    order_promotion_without_rules,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)

    promotion.rules.create(
        name="existing promotion rule",
        promotion=promotion,
        order_predicate=order_predicate,
        reward_value_type=reward_value_type,
        reward_value=reward_value,
        reward_type=reward_type,
    )

    rules_count = promotion.rules.count()
    assert rules_count == 1

    variables = {
        "input": {
            "promotion": promotion_id,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.RULES_NUMBER_LIMIT.name
    assert errors[0]["field"] == "orderPredicate"
    assert errors[0]["rulesLimit"] == 1
    assert errors[0]["rulesLimitExceedBy"] == 1
    assert promotion.rules.count() == rules_count


@override_settings(GIFTS_LIMIT_PER_RULE=1)
def test_promotion_rule_create_exceeds_gifts_number_limit(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    order_promotion_without_rules,
    product_variant_list,
):
    # given
    gift_limit = 1
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    reward_type = RewardTypeEnum.GIFT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list
    ]

    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "promotion": promotion_id,
            "channels": [channel_id],
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
            "gifts": gift_ids,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.GIFTS_NUMBER_LIMIT.name
    assert errors[0]["field"] == "gifts"
    assert errors[0]["giftsLimit"] == gift_limit
    assert errors[0]["giftsLimitExceedBy"] == len(gift_ids) - gift_limit
    assert errors[0]["rulesLimit"] is None
    assert errors[0]["rulesLimitExceedBy"] is None
    assert promotion.rules.count() == rules_count


@patch("saleor.plugins.manager.PluginsManager.promotion_rule_created")
def test_promotion_rule_create_gift_promotion(
    promotion_rule_created_mock,
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    order_promotion_without_rules,
    product_variant_list,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rules_count = promotion.rules.count()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_type = RewardTypeEnum.GIFT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list
    ]

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "channels": [channel_id],
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
            "gifts": gift_ids,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == name
    assert rule_data["channels"][0]["id"] == channel_id
    assert rule_data["orderPredicate"] == order_predicate
    assert rule_data["predicateType"] == promotion.type.upper()
    assert rule_data["promotion"]["id"] == promotion_id
    assert rule_data["rewardType"] == reward_type
    assert sorted(rule_data["giftIds"]) == sorted(gift_ids)
    assert promotion.rules.count() == rules_count + 1
    rule = promotion.rules.last()
    assert all([gift in product_variant_list for gift in rule.gifts.all()])
    assert rule.reward_type == RewardTypeEnum.GIFT.value
    promotion_rule_created_mock.assert_called_once_with(rule)


def test_promotion_rule_create_gift_promotion_wrong_gift_instance(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    order_promotion_without_rules,
    product_list,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rules_count = promotion.rules.count()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_type = RewardTypeEnum.GIFT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    gift_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "channels": [channel_id],
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
            "gifts": gift_ids,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID_GIFT_TYPE.name
    assert errors[0]["field"] == "gifts"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_gift_promotion_no_gifts(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    order_promotion_without_rules,
    product_list,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rules_count = promotion.rules.count()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_type = RewardTypeEnum.GIFT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "channels": [channel_id],
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
            "gifts": None,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "gifts"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_gift_promotion_with_reward_value(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    order_promotion_without_rules,
    product_variant_list,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rules_count = promotion.rules.count()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_type = RewardTypeEnum.GIFT.name
    reward_value = Decimal("10")
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list
    ]

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "channels": [channel_id],
            "rewardType": reward_type,
            "rewardValue": reward_value,
            "orderPredicate": order_predicate,
            "gifts": gift_ids,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "rewardValue"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_gift_promotion_with_reward_value_type(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    order_promotion_without_rules,
    product_variant_list,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rules_count = promotion.rules.count()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_type = RewardTypeEnum.GIFT.name
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list
    ]

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "channels": [channel_id],
            "rewardType": reward_type,
            "rewardValueType": reward_value_type,
            "orderPredicate": order_predicate,
            "gifts": gift_ids,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "rewardValueType"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_gift_promotion_missing_gifts(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    order_promotion_without_rules,
    product_variant_list,
):
    # given
    promotion = order_promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rules_count = promotion.rules.count()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_type = RewardTypeEnum.GIFT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "channels": [channel_id],
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "gifts"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_invalid_promotion_id(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    variant,
    catalogue_promotion,
    promotion_rule,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    catalogue_predicate = {
        "variantPredicate": {
            "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
        }
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    invalid_promotion_id = graphene.Node.to_global_id(
        "PromotionRule", promotion_rule.id
    )

    variables = {
        "input": {
            "name": name,
            "promotion": invalid_promotion_id,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]

    assert not rule_data
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "promotion"
    assert data["errors"][0]["code"] == PromotionRuleCreateErrorCode.GRAPHQL_ERROR.name
