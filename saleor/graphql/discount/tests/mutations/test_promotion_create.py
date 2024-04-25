from datetime import timedelta
from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
from django.utils import timezone
from freezegun import freeze_time

from .....discount import PromotionEvents
from .....discount.error_codes import PromotionCreateErrorCode
from .....discount.models import Promotion, PromotionEvent
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import RewardValueTypeEnum

PROMOTION_CREATE_MUTATION = """
    mutation promotionCreate($input: PromotionCreateInput!) {
        promotionCreate(input: $input) {
            promotion {
                id
                name
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
                    cataloguePredicate
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

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
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
    assert promotion_data["description"] == description_json
    assert promotion_data["startDate"] == start_date.isoformat()
    assert promotion_data["endDate"] == end_date.isoformat()
    assert promotion_data["createdAt"] == timezone.now().isoformat()
    assert promotion_data["updatedAt"] == timezone.now().isoformat()

    assert len(promotion_data["rules"]) == 2
    for rule_data in variables["input"]["rules"]:
        rule_data["promotion"] = {"id": promotion_data["id"]}
        rule_data["channels"] = [
            {"id": channel_id} for channel_id in rule_data["channels"]
        ]
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

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
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
    assert promotion_data["description"] == description_json
    assert promotion_data["startDate"] == start_date.isoformat()
    assert promotion_data["endDate"] == end_date.isoformat()
    assert promotion_data["createdAt"] == timezone.now().isoformat()
    assert promotion_data["updatedAt"] == timezone.now().isoformat()

    assert len(promotion_data["rules"]) == 2
    for rule_data in variables["input"]["rules"]:
        rule_data["promotion"] = {"id": promotion_data["id"]}
        rule_data["channels"] = [
            {"id": channel_id} for channel_id in rule_data["channels"]
        ]
        assert rule_data in promotion_data["rules"]

    promotion = Promotion.objects.filter(name=promotion_name).get()
    assert promotion.last_notification_scheduled_at is None

    promotion_created_mock.assert_called_once_with(promotion)
    promotion_started_mock.assert_not_called()
    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_missing_catalogue_predicate(
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
    assert errors[0]["code"] == PromotionCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "cataloguePredicate"
    assert errors[0]["index"] == 1


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
    expected_errors = [
        {
            "code": PromotionCreateErrorCode.REQUIRED.name,
            "field": "rewardValueType",
            "index": 0,
            "message": ANY,
        },
        {
            "code": PromotionCreateErrorCode.REQUIRED.name,
            "field": "rewardValueType",
            "index": 1,
            "message": ANY,
        },
    ]
    for error in expected_errors:
        assert error in errors


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
        },
        {
            "code": PromotionCreateErrorCode.REQUIRED.name,
            "field": "rewardValueType",
            "index": 0,
            "message": ANY,
        },
        {
            "code": PromotionCreateErrorCode.GRAPHQL_ERROR.name,
            "field": "channels",
            "index": 0,
            "message": ANY,
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
    assert not data["errors"]
    assert data["promotion"]
    assert len(data["promotion"]["rules"]) == 1
    assert data["promotion"]["rules"][0]["cataloguePredicate"] == {}
