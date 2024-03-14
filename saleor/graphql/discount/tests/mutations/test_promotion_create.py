from datetime import timedelta
from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from .....discount import PromotionEvents
from .....discount.error_codes import PromotionCreateErrorCode
from .....discount.models import Promotion, PromotionEvent
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import PromotionTypeEnum, RewardTypeEnum, RewardValueTypeEnum

PROMOTION_CREATE_MUTATION = """
    mutation promotionCreate($input: PromotionCreateInput!) {
        promotionCreate(input: $input) {
            promotion {
                id
                name
                type
                description
                startDate
                endDate
                createdAt
                updatedAt
                rules {
                    name
                    description
                    promotion {
                        id
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
            }
            errors {
                field
                code
                index
                message
                rulesLimit
                rulesLimitExceedBy
                giftsLimit
                giftsLimitExceedBy
            }
        }
    }
"""


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
@patch("saleor.plugins.manager.PluginsManager.promotion_created")
def test_promotion_create_by_staff_user(
    promotion_created_mock,
    promotion_started_mock,
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    collection,
    category,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    promotion_name = "test promotion"
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
    rule_1_name = "test promotion rule 1"
    rule_2_name = "test promotion rule 2"
    reward_value = Decimal("10")
    reward_value_type_1 = RewardValueTypeEnum.FIXED.name
    reward_value_type_2 = RewardValueTypeEnum.PERCENTAGE.name
    promotion_type = PromotionTypeEnum.CATALOGUE.name

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": promotion_type,
            "rules": [
                {
                    "name": rule_1_name,
                    "description": description_json,
                    "channels": rule_1_channel_ids,
                    "rewardValueType": reward_value_type_1,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
                {
                    "name": rule_2_name,
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValueType": reward_value_type_2,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    promotion_data = data["promotion"]

    assert not data["errors"]
    assert promotion_data["name"] == promotion_name
    assert promotion_data["type"] == promotion_type
    assert promotion_data["description"] == description_json
    assert promotion_data["startDate"] == start_date.isoformat()
    assert promotion_data["endDate"] == end_date.isoformat()
    assert promotion_data["createdAt"] == timezone.now().isoformat()
    assert promotion_data["updatedAt"] == timezone.now().isoformat()

    assert len(promotion_data["rules"]) == 2
    for rule_data in variables["input"]["rules"]:
        rule_data["orderPredicate"] = {}
        rule_data["promotion"] = {"id": promotion_data["id"]}
        rule_data["predicateType"] = promotion_type
        rule_data["channels"] = [
            {"id": channel_id} for channel_id in rule_data["channels"]
        ]
        rule_data["giftIds"] = []
        rule_data["rewardType"] = None
        assert rule_data in promotion_data["rules"]

    promotion = Promotion.objects.filter(name=promotion_name).get()
    assert promotion.last_notification_scheduled_at == timezone.now()

    promotion_created_mock.assert_called_once_with(promotion)
    promotion_started_mock.assert_called_once_with(promotion)
    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
@patch("saleor.plugins.manager.PluginsManager.promotion_created")
def test_promotion_create_by_app(
    promotion_created_mock,
    promotion_started_mock,
    app_api_client,
    permission_manage_discounts,
    description_json,
    channel_USD,
    variant,
    product,
):
    # given
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    promotion_name = "test promotion"
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
        ]
    }

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "rules": [
                {
                    "name": "test promotion rule",
                    "description": description_json,
                    "channels": channel_ids,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": Decimal("10"),
                    "cataloguePredicate": catalogue_predicate,
                }
            ],
        }
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_CREATE_MUTATION, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    promotion_data = data["promotion"]

    assert not data["errors"]
    assert promotion_data["name"] == promotion_name
    assert promotion_data["description"] == description_json
    assert promotion_data["startDate"] == start_date.isoformat()
    assert promotion_data["endDate"] == end_date.isoformat()

    promotion = Promotion.objects.filter(name=promotion_name).get()
    assert promotion.last_notification_scheduled_at == timezone.now()

    promotion_created_mock.assert_called_once_with(promotion)
    promotion_started_mock.assert_called_once_with(promotion)
    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.product.tasks.update_products_discounted_prices_of_promotion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
@patch("saleor.plugins.manager.PluginsManager.promotion_created")
def test_promotion_create_by_customer(
    promotion_created_mock,
    promotion_started_mock,
    update_products_discounted_prices_of_promotion_task_mock,
    api_client,
    description_json,
    channel_USD,
    variant,
    product,
    collection,
    category,
):
    # given
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    promotion_name = "test promotion"
    catalogue_predicate = {
        "variantPredicate": {
            "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
        }
    }

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": "test promotion rule",
                    "description": description_json,
                    "channels": channel_ids,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": Decimal("10"),
                    "cataloguePredicate": catalogue_predicate,
                }
            ],
        }
    }

    # when
    response = api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    assert_no_permission(response)

    promotion_created_mock.assert_not_called()
    promotion_started_mock.assert_not_called()
    update_products_discounted_prices_of_promotion_task_mock.assert_not_called()


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_with_order_rule(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    promotion_name = "test promotion"
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    rule_name = "test promotion rule 1"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.ORDER.name,
            "rules": [
                {
                    "name": rule_name,
                    "description": description_json,
                    "channels": channel_ids,
                    "rewardValueType": reward_value_type,
                    "rewardValue": reward_value,
                    "rewardType": reward_type,
                    "orderPredicate": order_predicate,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    promotion_data = data["promotion"]

    assert not data["errors"]
    assert promotion_data["name"] == promotion_name
    assert promotion_data["description"] == description_json
    assert promotion_data["startDate"] == start_date.isoformat()
    assert promotion_data["endDate"] == end_date.isoformat()

    promotion = Promotion.objects.filter(name=promotion_name).get()
    assert promotion.last_notification_scheduled_at == timezone.now()


def test_promotion_create_fixed_reward_value_multiple_currencies(
    staff_api_client,
    permission_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
):
    # given
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    promotion_name = "test promotion"
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
        ]
    }

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": "test promotion rule",
                    "description": description_json,
                    "channels": channel_ids,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": Decimal("10"),
                    "cataloguePredicate": catalogue_predicate,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_CREATE_MUTATION, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == PromotionCreateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.name
    )
    assert errors[0]["field"] == "rewardValueType"
    assert errors[0]["index"] == 0


def test_promotion_create_invalid_price_precision(
    staff_api_client,
    permission_manage_discounts,
    description_json,
    channel_USD,
    variant,
    product,
):
    # given
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]

    promotion_name = "test promotion"
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
        ]
    }

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": "test promotion rule",
                    "description": description_json,
                    "channels": channel_ids,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": Decimal("10.12345"),
                    "cataloguePredicate": catalogue_predicate,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_CREATE_MUTATION, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.INVALID_PRECISION.name
    assert errors[0]["field"] == "rewardValue"
    assert errors[0]["index"] == 0


def test_promotion_create_invalid_percentage_value(
    staff_api_client,
    permission_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
):
    # given
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    promotion_name = "test promotion"
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
        ]
    }

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": "test promotion rule",
                    "description": description_json,
                    "channels": channel_ids,
                    "rewardValueType": RewardValueTypeEnum.PERCENTAGE.name,
                    "rewardValue": Decimal("101"),
                    "cataloguePredicate": catalogue_predicate,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_CREATE_MUTATION, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "rewardValue"
    assert errors[0]["index"] == 0


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
@patch("saleor.plugins.manager.PluginsManager.promotion_created")
def test_promotion_create_only_name_and_end_date(
    promotion_created_mock,
    promotion_started_mock,
    app_api_client,
    permission_manage_discounts,
    description_json,
    channel_USD,
    variant,
    product,
):
    # given
    end_date = timezone.now() + timedelta(days=30)
    promotion_name = "test promotion"

    variables = {
        "input": {
            "name": promotion_name,
            "endDate": end_date.isoformat(),
        }
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_CREATE_MUTATION, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    promotion_data = data["promotion"]

    assert not data["errors"]
    assert promotion_data["name"] == promotion_name
    assert promotion_data["endDate"] == end_date.isoformat()

    promotion = Promotion.objects.filter(name=promotion_name).get()
    assert promotion.last_notification_scheduled_at == timezone.now()

    promotion_created_mock.assert_called_once_with(promotion)
    promotion_started_mock.assert_called_once_with(promotion)
    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
@patch("saleor.plugins.manager.PluginsManager.promotion_created")
def test_promotion_create_start_date_and_end_date_after_current_date(
    promotion_created_mock,
    promotion_started_mock,
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    collection,
    category,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() + timedelta(days=10)
    end_date = timezone.now() + timedelta(days=30)

    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    promotion_name = "test promotion"
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
    rule_1_name = "test promotion rule 1"
    rule_2_name = "test promotion rule 2"
    reward_value = Decimal("10")
    reward_value_type_1 = RewardValueTypeEnum.FIXED.name
    reward_value_type_2 = RewardValueTypeEnum.PERCENTAGE.name
    promotion_type = PromotionTypeEnum.CATALOGUE.name

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": promotion_type,
            "rules": [
                {
                    "name": rule_1_name,
                    "description": description_json,
                    "channels": rule_1_channel_ids,
                    "rewardValueType": reward_value_type_1,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
                {
                    "name": rule_2_name,
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValueType": reward_value_type_2,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    promotion_data = data["promotion"]

    assert not data["errors"]
    assert promotion_data["name"] == promotion_name
    assert promotion_data["type"] == promotion_type
    assert promotion_data["description"] == description_json
    assert promotion_data["startDate"] == start_date.isoformat()
    assert promotion_data["endDate"] == end_date.isoformat()
    assert promotion_data["createdAt"] == timezone.now().isoformat()
    assert promotion_data["updatedAt"] == timezone.now().isoformat()

    assert len(promotion_data["rules"]) == 2
    for rule_data in variables["input"]["rules"]:
        rule_data["orderPredicate"] = {}
        rule_data["promotion"] = {"id": promotion_data["id"]}
        rule_data["predicateType"] = promotion_type
        rule_data["channels"] = [
            {"id": channel_id} for channel_id in rule_data["channels"]
        ]
        rule_data["giftIds"] = []
        rule_data["rewardType"] = None
        assert rule_data in promotion_data["rules"]

    promotion = Promotion.objects.filter(name=promotion_name).get()
    assert promotion.last_notification_scheduled_at is None

    promotion_created_mock.assert_called_once_with(promotion)
    promotion_started_mock.assert_not_called()
    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_missing_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    promotion_name = "test promotion"
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }

    rule_1_name = "test promotion rule 1"
    rule_2_name = "test promotion rule 2"
    reward_value = Decimal("10")
    reward_value_type_1 = RewardValueTypeEnum.FIXED.name
    reward_value_type_2 = RewardValueTypeEnum.PERCENTAGE.name
    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": rule_1_name,
                    "description": description_json,
                    "channels": rule_1_channel_ids,
                    "rewardValueType": reward_value_type_1,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
                {
                    "name": rule_2_name,
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValueType": reward_value_type_2,
                    "rewardValue": reward_value,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert {
        "code": PromotionCreateErrorCode.REQUIRED.name,
        "field": "cataloguePredicate",
        "index": 1,
        "message": ANY,
        "rulesLimit": None,
        "rulesLimitExceedBy": None,
        "giftsLimit": None,
        "giftsLimitExceedBy": None,
    } in errors


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_missing_reward_value(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    promotion_name = "test promotion"
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }

    rule_1_name = "test promotion rule 1"
    rule_2_name = "test promotion rule 2"
    reward_value = Decimal("10")
    reward_value_type_1 = RewardValueTypeEnum.FIXED.name
    reward_value_type_2 = RewardValueTypeEnum.PERCENTAGE.name
    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": rule_1_name,
                    "description": description_json,
                    "channels": rule_1_channel_ids,
                    "rewardValueType": reward_value_type_1,
                    "cataloguePredicate": catalogue_predicate,
                },
                {
                    "name": rule_2_name,
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValueType": reward_value_type_2,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "rewardValue"
    assert errors[0]["index"] == 0


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_missing_reward_value_type(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    promotion_name = "test promotion"
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }

    rule_1_name = "test promotion rule 1"
    rule_2_name = "test promotion rule 2"
    reward_value = Decimal("10")
    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": rule_1_name,
                    "description": description_json,
                    "channels": rule_1_channel_ids,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
                {
                    "name": rule_2_name,
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
            ],
        }
    }
    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 2
    error_fields = set([error["field"] for error in errors])
    assert len(error_fields) == 1
    assert "rewardValueType" in error_fields
    error_codes = set([error["code"] for error in errors])
    assert len(error_codes) == 1
    assert PromotionCreateErrorCode.REQUIRED.name in error_codes


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_invalid_channel_id(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    promotion_name = "test promotion"
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }

    rule_1_name = "test promotion rule 1"
    rule_2_name = "test promotion rule 2"
    reward_value = Decimal("10")
    reward_value_type_1 = RewardValueTypeEnum.FIXED.name
    reward_value_type_2 = RewardValueTypeEnum.PERCENTAGE.name
    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", -1)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": rule_1_name,
                    "description": description_json,
                    "channels": rule_1_channel_ids,
                    "rewardValueType": reward_value_type_1,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
                {
                    "name": rule_2_name,
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValueType": reward_value_type_2,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.GRAPHQL_ERROR.name
    assert errors[0]["field"] == "channels"
    assert errors[0]["index"] == 0


def test_promotion_create_mixed_catalogue_and_order_rules(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    collection,
    category,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    promotion_name = "test promotion"
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    rule_1_name = "test promotion rule 1"
    rule_2_name = "test promotion rule 2"
    reward_value = Decimal("10")
    reward_value_type_1 = RewardValueTypeEnum.FIXED.name
    reward_value_type_2 = RewardValueTypeEnum.PERCENTAGE.name

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": rule_1_name,
                    "description": description_json,
                    "channels": rule_1_channel_ids,
                    "rewardValueType": reward_value_type_1,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
                {
                    "name": rule_2_name,
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValueType": reward_value_type_2,
                    "rewardValue": reward_value,
                    "orderPredicate": order_predicate,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 2
    assert {
        "code": PromotionCreateErrorCode.REQUIRED.name,
        "field": "cataloguePredicate",
        "index": 1,
        "rulesLimit": None,
        "rulesLimitExceedBy": None,
        "giftsLimit": None,
        "giftsLimitExceedBy": None,
        "message": ANY,
    } in errors
    assert {
        "code": PromotionCreateErrorCode.INVALID.name,
        "field": "orderPredicate",
        "index": 1,
        "rulesLimit": None,
        "rulesLimitExceedBy": None,
        "giftsLimit": None,
        "giftsLimitExceedBy": None,
        "message": ANY,
    } in errors


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_mixed_currencies_for_price_based_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    promotion_name = "test promotion"
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    rule_name = "test promotion rule 1"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.ORDER.name,
            "rules": [
                {
                    "name": rule_name,
                    "description": description_json,
                    "channels": channel_ids,
                    "rewardValueType": reward_value_type,
                    "rewardValue": reward_value,
                    "rewardType": reward_type,
                    "orderPredicate": order_predicate,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == PromotionCreateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.name
    )
    assert errors[0]["field"] == "channels"
    assert errors[0]["index"] == 0


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_multiple_errors(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    channel_ids = [graphene.Node.to_global_id("Channel", -1)]
    promotion_name = "test promotion"
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": "test promotion rule 1",
                    "description": description_json,
                    "channels": channel_ids,
                    "cataloguePredicate": catalogue_predicate,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 3
    expected_errors = [
        {
            "code": PromotionCreateErrorCode.REQUIRED.name,
            "field": "rewardValue",
            "index": 0,
            "message": ANY,
            "rulesLimit": None,
            "rulesLimitExceedBy": None,
            "giftsLimit": None,
            "giftsLimitExceedBy": None,
        },
        {
            "code": PromotionCreateErrorCode.REQUIRED.name,
            "field": "rewardValueType",
            "index": 0,
            "message": ANY,
            "rulesLimit": None,
            "rulesLimitExceedBy": None,
            "giftsLimit": None,
            "giftsLimitExceedBy": None,
        },
        {
            "code": PromotionCreateErrorCode.GRAPHQL_ERROR.name,
            "field": "channels",
            "index": 0,
            "message": ANY,
            "rulesLimit": None,
            "rulesLimitExceedBy": None,
            "giftsLimit": None,
            "giftsLimitExceedBy": None,
        },
    ]
    for error in expected_errors:
        assert error in errors


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_end_date_before_start_date(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() + timedelta(days=30)
    end_date = timezone.now() - timedelta(days=30)

    promotion_name = "test promotion"
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }

    rule_1_name = "test promotion rule 1"
    rule_2_name = "test promotion rule 2"
    reward_value = Decimal("10")
    reward_value_type_1 = RewardValueTypeEnum.FIXED.name
    reward_value_type_2 = RewardValueTypeEnum.PERCENTAGE.name
    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": rule_1_name,
                    "description": description_json,
                    "channels": rule_1_channel_ids,
                    "rewardValueType": reward_value_type_1,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
                {
                    "name": rule_2_name,
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValueType": reward_value_type_2,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "endDate"
    assert errors[0]["index"] is None


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_invalid_catalogue_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    promotion_name = "test promotion"
    catalogue_predicate_1 = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            },
        ]
    }
    catalogue_predicate_2 = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            },
        ],
        "AND": [
            {
                "productPredicate": {
                    "ids": [graphene.Node.to_global_id("Product", product.id)]
                }
            },
        ],
    }
    rule_1_name = "test promotion rule 1"
    rule_2_name = "test promotion rule 2"
    reward_value = Decimal("10")
    reward_value_type_1 = RewardValueTypeEnum.FIXED.name
    reward_value_type_2 = RewardValueTypeEnum.PERCENTAGE.name

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": rule_1_name,
                    "description": description_json,
                    "channels": rule_1_channel_ids,
                    "rewardValueType": reward_value_type_1,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate_1,
                },
                {
                    "name": rule_2_name,
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValueType": reward_value_type_2,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate_2,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "cataloguePredicate"
    assert errors[0]["index"] == 1


@override_settings(ORDER_RULES_LIMIT=1)
def test_promotion_create_exceeds_rules_number_limit(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    product,
    order_promotion_with_rule,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    promotion_name = "test promotion"
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    rule_name = "test promotion rule 1"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)

    variables = {
        "input": {
            "name": promotion_name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.ORDER.name,
            "rules": [
                {
                    "name": rule_name,
                    "channels": [channel_id],
                    "rewardValueType": reward_value_type,
                    "rewardValue": reward_value,
                    "rewardType": reward_type,
                    "orderPredicate": order_predicate,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.RULES_NUMBER_LIMIT.name
    assert errors[0]["field"] == "rules"
    assert errors[0]["rulesLimit"] == 1
    assert errors[0]["rulesLimitExceedBy"] == 1
    assert errors[0]["giftsLimit"] is None
    assert errors[0]["giftsLimitExceedBy"] is None


@override_settings(GIFTS_LIMIT_PER_RULE=1)
def test_promotion_create_exceeds_gifts_number_limit(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    product_variant_list,
):
    # given
    gift_limit = 1
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    promotion_name = "test promotion"
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    rule_name = "test promotion rule 1"
    reward_type = RewardTypeEnum.GIFT.name
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list
    ]

    variables = {
        "input": {
            "name": promotion_name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.ORDER.name,
            "rules": [
                {
                    "name": rule_name,
                    "channels": [channel_id],
                    "rewardType": reward_type,
                    "orderPredicate": order_predicate,
                    "gifts": gift_ids,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.GIFTS_NUMBER_LIMIT.name
    assert errors[0]["field"] == "gifts"
    assert errors[0]["index"] == 0
    assert errors[0]["giftsLimit"] == gift_limit
    assert errors[0]["giftsLimitExceedBy"] == len(gift_ids) - gift_limit


@patch("saleor.product.tasks.update_products_discounted_prices_of_promotion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
@patch("saleor.plugins.manager.PluginsManager.promotion_created")
def test_promotion_create_rules_without_channels_and_percentage_reward(
    promotion_created_mock,
    promotion_started_mock,
    update_products_discounted_prices_of_promotion_task_mock,
    staff_api_client,
    permission_group_manage_discounts,
    variant,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    catalogue_predicate = {
        "variantPredicate": {
            "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
        }
    }
    variables = {
        "input": {
            "name": "test promotion",
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "rules": [
                {
                    "name": "test promotion rule 1",
                    "rewardValueType": RewardValueTypeEnum.PERCENTAGE.name,
                    "rewardValue": Decimal("10"),
                    "cataloguePredicate": catalogue_predicate,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]

    assert not data["errors"]
    assert data["promotion"]["rules"]


PROMOTION_CREATE_WITH_EVENTS = """
    mutation promotionCreate($input: PromotionCreateInput!) {
        promotionCreate(input: $input) {
            promotion {
                id
                events {
                    ... on PromotionEventInterface {
                        type
                        createdBy {
                            ... on User {
                                id
                            }
                            ... on App {
                                id
                            }
                        }
                    }
                    ... on PromotionRuleEventInterface {
                        ruleId
                    }
                }
                rules {
                    id
                }
            }
            errors {
                field
                code
                index
                message
            }
        }
    }
"""


def test_promotion_create_events_by_staff_user(
    staff_api_client,
    permission_manage_discounts,
    permission_manage_staff,
    channel_USD,
    channel_PLN,
    variant,
):
    # given
    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            },
        ]
    }

    variables = {
        "input": {
            "name": "test promotion",
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "channels": rule_1_channel_ids,
                    "cataloguePredicate": catalogue_predicate,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": Decimal("1"),
                },
                {
                    "channels": rule_2_channel_ids,
                    "cataloguePredicate": catalogue_predicate,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": Decimal("1"),
                },
            ],
        }
    }
    event_count = PromotionEvent.objects.count()

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_CREATE_WITH_EVENTS,
        variables,
        permissions=[permission_manage_discounts, permission_manage_staff],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    assert not data["errors"]

    events = data["promotion"]["events"]
    event_types = {event["type"] for event in events}
    assert len(events) == 4
    assert PromotionEvent.objects.count() == event_count + 4
    assert PromotionEvents.PROMOTION_CREATED.upper() in event_types
    assert PromotionEvents.PROMOTION_STARTED.upper() in event_types
    assert PromotionEvents.RULE_CREATED.upper() in event_types

    users = list({event["createdBy"]["id"] for event in events})
    user_id = graphene.Node.to_global_id("User", staff_api_client.user.id)
    assert len(users) == 1
    assert users[0] == user_id

    rule_ids = [event["ruleId"] for event in events if event.get("ruleId")]
    rules = data["promotion"]["rules"]
    assert all([rule["id"] in rule_ids for rule in rules])


def test_promotion_create_events_by_app(
    app_api_client,
    permission_manage_discounts,
    permission_manage_apps,
    channel_USD,
    channel_PLN,
    variant,
):
    # given
    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            },
        ]
    }

    variables = {
        "input": {
            "name": "test promotion",
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "channels": rule_1_channel_ids,
                    "cataloguePredicate": catalogue_predicate,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": Decimal("1"),
                },
                {
                    "channels": rule_2_channel_ids,
                    "cataloguePredicate": catalogue_predicate,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": Decimal("1"),
                },
            ],
        }
    }
    event_count = PromotionEvent.objects.count()

    # when
    response = app_api_client.post_graphql(
        PROMOTION_CREATE_WITH_EVENTS,
        variables,
        permissions=[permission_manage_discounts, permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    assert not data["errors"]

    events = data["promotion"]["events"]
    event_types = {event["type"] for event in events}
    assert len(events) == 4
    assert PromotionEvent.objects.count() == event_count + 4
    assert PromotionEvents.PROMOTION_CREATED.upper() in event_types
    assert PromotionEvents.PROMOTION_STARTED.upper() in event_types
    assert PromotionEvents.RULE_CREATED.upper() in event_types

    apps = list({event["createdBy"]["id"] for event in events})
    app_id = graphene.Node.to_global_id("App", app_api_client.app.id)
    assert len(apps) == 1
    assert apps[0] == app_id

    rule_ids = [event["ruleId"] for event in events if event.get("ruleId")]
    rules = data["promotion"]["rules"]
    assert all([rule["id"] in rule_ids for rule in rules])


@patch("saleor.product.tasks.update_products_discounted_prices_of_promotion_task.delay")
def test_promotion_create_gift_promotion(
    _,
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    product_variant_list,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion_name = "test gift promotion"
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    rule_name = "test gift promotion rule"
    reward_type = RewardTypeEnum.GIFT.name
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list
    ]

    variables = {
        "input": {
            "name": promotion_name,
            "type": PromotionTypeEnum.ORDER.name,
            "rules": [
                {
                    "name": rule_name,
                    "channels": channel_ids,
                    "rewardType": reward_type,
                    "orderPredicate": order_predicate,
                    "gifts": gift_ids,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    assert not data["errors"]

    assert data["promotion"]["type"] == PromotionTypeEnum.ORDER.name
    rules_data = data["promotion"]["rules"]
    assert len(rules_data) == 1
    assert rules_data[0]["orderPredicate"] == order_predicate
    assert rules_data[0]["predicateType"] == PromotionTypeEnum.ORDER.name
    assert rules_data[0]["rewardType"] == RewardTypeEnum.GIFT.name
    assert sorted(rules_data[0]["giftIds"]) == sorted(gift_ids)

    promotion = Promotion.objects.filter(name=promotion_name).get()
    rules = promotion.rules.all()
    assert len(rules) == 1
    assert all([gift in product_variant_list for gift in rules[0].gifts.all()])
    assert rules[0].reward_type == RewardTypeEnum.GIFT.value


def test_promotion_create_gift_promotion_wrong_gift_instance(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    product_list,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion_name = "test gift promotion"
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    rule_name = "test gift promotion rule"
    reward_type = RewardTypeEnum.GIFT.name
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    gift_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]

    variables = {
        "input": {
            "name": promotion_name,
            "type": PromotionTypeEnum.ORDER.name,
            "rules": [
                {
                    "name": rule_name,
                    "channels": channel_ids,
                    "rewardType": reward_type,
                    "orderPredicate": order_predicate,
                    "gifts": gift_ids,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.INVALID_GIFT_TYPE.name
    assert errors[0]["field"] == "gifts"
    assert errors[0]["index"] == 0


def test_promotion_create_gift_promotion_with_reward_value(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    product_variant_list,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion_name = "test gift promotion"
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    rule_name = "test gift promotion rule"
    reward_type = RewardTypeEnum.GIFT.name
    reward_value = Decimal("10")
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list
    ]

    variables = {
        "input": {
            "name": promotion_name,
            "type": PromotionTypeEnum.ORDER.name,
            "rules": [
                {
                    "name": rule_name,
                    "channels": channel_ids,
                    "rewardType": reward_type,
                    "rewardValue": reward_value,
                    "orderPredicate": order_predicate,
                    "gifts": gift_ids,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "rewardValue"
    assert errors[0]["index"] == 0


def test_promotion_create_gift_promotion_with_reward_value_type(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    product_variant_list,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion_name = "test gift promotion"
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    rule_name = "test gift promotion rule"
    reward_type = RewardTypeEnum.GIFT.name
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list
    ]

    variables = {
        "input": {
            "name": promotion_name,
            "type": PromotionTypeEnum.ORDER.name,
            "rules": [
                {
                    "name": rule_name,
                    "channels": channel_ids,
                    "rewardType": reward_type,
                    "rewardValueType": reward_value_type,
                    "orderPredicate": order_predicate,
                    "gifts": gift_ids,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "rewardValueType"
    assert errors[0]["index"] == 0


def test_promotion_create_gift_promotion_missing_gifts(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion_name = "test gift promotion"
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    rule_name = "test gift promotion rule"
    reward_type = RewardTypeEnum.GIFT.name
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]

    variables = {
        "input": {
            "name": promotion_name,
            "type": PromotionTypeEnum.ORDER.name,
            "rules": [
                {
                    "name": rule_name,
                    "channels": channel_ids,
                    "rewardType": reward_type,
                    "orderPredicate": order_predicate,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "gifts"
    assert errors[0]["index"] == 0


def test_promotion_create_without_catalogue_predicate(
    staff_api_client,
    permission_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
):
    # given
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    promotion_name = "test promotion"
    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "rules": [
                {
                    "name": "test promotion rule",
                    "description": description_json,
                    "channels": channel_ids,
                    "rewardValueType": RewardValueTypeEnum.PERCENTAGE.name,
                    "rewardValue": Decimal("50"),
                    "cataloguePredicate": None,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_CREATE_MUTATION, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    assert not data["promotion"]
    assert data["errors"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["code"] == PromotionCreateErrorCode.REQUIRED.name
    assert error["field"] == "cataloguePredicate"
    assert error["rulesLimit"] is None
    assert error["rulesLimitExceedBy"] is None
    assert error["giftsLimit"] is None
    assert error["giftsLimitExceedBy"] is None
