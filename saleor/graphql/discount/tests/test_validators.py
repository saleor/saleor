from collections import defaultdict

import graphene
import pytest
from django.core.exceptions import ValidationError

from ....discount import PromotionType, RewardType, RewardValueType
from ..enums import PromotionCreateErrorCode
from ..mutations.promotion.validators import (
    _clean_catalogue_predicate,
    _clean_gift_rule,
    _clean_order_predicate,
    _clean_predicates,
    _clean_reward,
    _clean_reward_value,
    clean_predicate,
)


def test_clean_predicate(variant, product):
    # given
    variant_ids = [graphene.Node.to_global_id("ProductVariant", variant.id)]
    product_ids = [graphene.Node.to_global_id("Product", product.id)]
    predicate = {
        "OR": [
            {"variant_predicate": {"ids": variant_ids}},
            {"product_predicate": {"ids": product_ids}},
        ]
    }

    # when
    response = clean_predicate(predicate, PromotionCreateErrorCode)

    # then
    assert response == {
        "OR": [
            {"variantPredicate": {"ids": variant_ids}},
            {"productPredicate": {"ids": product_ids}},
        ]
    }


@pytest.mark.parametrize(
    "predicate",
    [
        {
            "AND": [{"productPredicate": {"ids": ["ABC"]}}],
            "OR": [{"productPredicate": {"ids": ["ABC"]}}],
        },
        {
            "AND": [
                {
                    "productPredicate": {"ids": ["ABC"]},
                    "OR": [{"productPredicate": {"ids": ["ABC"]}}],
                }
            ]
        },
    ],
)
def test_clean_predicate_invalid_predicate(predicate):
    # when
    with pytest.raises(ValidationError) as validation_error:
        clean_predicate(predicate, PromotionCreateErrorCode)

    # then
    assert validation_error.value.code == PromotionCreateErrorCode.INVALID.value


def test_clean_predicates_invalid_order_predicate(product):
    # given
    order_predicate = {
        "discounted_object_predicate": {"base_subtotal_price": {"range": {"gte": 100}}}
    }
    catalogue_predicate = {
        "product_predicate": {
            "ids": [graphene.Node.to_global_id("Product", product.id)]
        }
    }
    errors = defaultdict(list)

    # when
    _clean_predicates(
        catalogue_predicate,
        order_predicate,
        errors,
        PromotionCreateErrorCode,
        None,
        PromotionType.CATALOGUE,
    )

    # then
    assert len(errors) == 1
    assert len(errors["order_predicate"]) == 1
    assert errors["order_predicate"][0].code == PromotionCreateErrorCode.INVALID.value


def test_clean_predicates_invalid_catalogue_predicate(product):
    # given
    checkout_and_order_predicate = {
        "discounted_object_predicate": {"subtotal_price": {"range": {"gte": 100}}}
    }
    catalogue_predicate = {
        "product_predicate": {
            "ids": [graphene.Node.to_global_id("Product", product.id)]
        }
    }
    errors = defaultdict(list)

    # when
    _clean_predicates(
        catalogue_predicate,
        checkout_and_order_predicate,
        errors,
        PromotionCreateErrorCode,
        None,
        PromotionType.ORDER,
    )

    # then
    assert len(errors) == 1
    assert len(errors["catalogue_predicate"]) == 1
    assert (
        errors["catalogue_predicate"][0].code == PromotionCreateErrorCode.INVALID.value
    )


def test_clean_predicates_missing_catalogue_predicate(product):
    # given
    errors = defaultdict(list)

    # when
    _clean_predicates(
        None,
        None,
        errors,
        PromotionCreateErrorCode,
        None,
        PromotionType.CATALOGUE,
    )

    # then
    assert len(errors) == 1
    assert len(errors["catalogue_predicate"]) == 1
    assert (
        errors["catalogue_predicate"][0].code == PromotionCreateErrorCode.REQUIRED.value
    )


def test_clean_predicates_missing_order_predicate(product):
    # given
    errors = defaultdict(list)

    # when
    _clean_predicates(
        None,
        None,
        errors,
        PromotionCreateErrorCode,
        None,
        PromotionType.ORDER,
    )

    # then
    assert len(errors) == 1
    assert len(errors["order_predicate"]) == 1
    assert errors["order_predicate"][0].code == PromotionCreateErrorCode.REQUIRED.value


def test_clean_predicates_mixed_promotion_predicates_invalid_catalogue_predicate(
    product,
):
    # given
    catalogue_predicate = {
        "product_predicate": {
            "ids": [graphene.Node.to_global_id("Product", product.id)]
        }
    }
    errors = defaultdict(list)

    # when
    _clean_predicates(
        catalogue_predicate,
        {},
        errors,
        PromotionCreateErrorCode,
        None,
        PromotionType.ORDER,
    )

    # then
    assert len(errors) == 1
    assert len(errors["catalogue_predicate"]) == 1
    assert (
        errors["catalogue_predicate"][0].code == PromotionCreateErrorCode.INVALID.value
    )


def test_clean_predicates_mixed_promotion_predicates_invalid_order(
    product,
):
    # given
    order_predicate = {
        "discounted_object_predicate": {"base_subtotal_price": {"range": {"gte": 100}}}
    }
    errors = defaultdict(list)

    # when
    _clean_predicates(
        {},
        order_predicate,
        errors,
        PromotionCreateErrorCode,
        None,
        PromotionType.CATALOGUE,
    )

    # then
    assert len(errors) == 1
    assert len(errors["order_predicate"]) == 1
    assert errors["order_predicate"][0].code == PromotionCreateErrorCode.INVALID.value


def test_clean_catalogue_predicate_reward_type_provided():
    # given
    catalogue_predicate = {
        "productPredicate": {"ids": ["ABC"]},
        "categoryPredicate": {"ids": ["ABC"]},
    }
    cleaned_input = {
        "catalogue_predicate": catalogue_predicate,
        "reward_type": RewardType.SUBTOTAL_DISCOUNT,
    }
    errors = defaultdict(list)

    # when
    _clean_catalogue_predicate(
        cleaned_input,
        catalogue_predicate,
        errors,
        PromotionCreateErrorCode,
        None,
        None,
    )

    # then
    assert len(errors) == 1
    assert len(errors["reward_type"]) == 1
    assert errors["reward_type"][0].code == PromotionCreateErrorCode.INVALID.value


def test_clean_order_predicate_missing_reward_type():
    # given
    order_predicate = {
        "discounted_object_predicate": {"base_subtotal_price": {"range": {"gte": 100}}}
    }
    cleaned_input = {
        "order_predicate": order_predicate,
    }
    errors = defaultdict(list)

    # when
    _clean_order_predicate(
        cleaned_input,
        order_predicate,
        {},
        set(),
        errors,
        PromotionCreateErrorCode,
        None,
        None,
    )

    # then
    assert len(errors) == 1
    assert len(errors["reward_type"]) == 1
    assert errors["reward_type"][0].code == PromotionCreateErrorCode.REQUIRED.value


def test_clean_order_predicate_reward_type_in_instance(
    order_promotion_with_rule,
):
    # given
    rule = order_promotion_with_rule.rules.first()
    order_predicate = {
        "discounted_object_predicate": {"base_subtotal_price": {"range": {"gte": 100}}}
    }
    cleaned_input = {
        "order_predicate": order_predicate,
    }
    errors = defaultdict(list)

    # when
    _clean_order_predicate(
        cleaned_input,
        order_predicate,
        {},
        set(),
        errors,
        PromotionCreateErrorCode,
        None,
        rule,
    )

    # then
    assert not errors


def test_clean_order_predicate_price_based_predicate_mixed_currencies():
    # given
    order_predicate = {
        "discounted_object_predicate": {"base_subtotal_price": {"range": {"gte": 100}}}
    }
    cleaned_input = {
        "order_predicate": order_predicate,
        "reward_type": RewardType.SUBTOTAL_DISCOUNT,
    }
    currencies = {"USD", "PLN"}
    errors = defaultdict(list)

    # when
    _clean_order_predicate(
        cleaned_input,
        order_predicate,
        currencies,
        set(),
        errors,
        PromotionCreateErrorCode,
        None,
        None,
    )

    # then
    assert len(errors) == 1
    assert len(errors["channels"]) == 1
    assert (
        errors["channels"][0].code
        == PromotionCreateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.value
    )


def test_clean_order_mixed_currencies_instance_given_invalid_predicate(
    order_promotion_with_rule,
):
    # given
    rule = order_promotion_with_rule.rules.first()
    order_predicate = {
        "discounted_object_predicate": {"base_subtotal_price": {"range": {"gte": 100}}}
    }
    cleaned_input = {
        "order_predicate": order_predicate,
    }
    currencies = {"USD", "PLN"}
    errors = defaultdict(list)

    # when
    _clean_order_predicate(
        cleaned_input,
        order_predicate,
        currencies,
        set(),
        errors,
        PromotionCreateErrorCode,
        None,
        rule,
    )

    # then
    assert len(errors) == 1
    assert len(errors["order_predicate"]) == 1
    assert (
        errors["order_predicate"][0].code
        == PromotionCreateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.value
    )


def test_clean_order_mixed_currencies_instance_given_invalid_channels(
    order_promotion_with_rule,
):
    # given
    rule = order_promotion_with_rule.rules.first()
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    cleaned_input = {
        "add_channels": ["AB", "CD"],
    }
    currencies = {"USD", "PLN"}
    errors = defaultdict(list)

    # when
    _clean_order_predicate(
        cleaned_input,
        order_predicate,
        currencies,
        set(),
        errors,
        PromotionCreateErrorCode,
        None,
        rule,
    )

    # then
    assert len(errors) == 1
    assert len(errors["add_channels"]) == 1
    assert (
        errors["add_channels"][0].code
        == PromotionCreateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.value
    )


def test_clean_reward_lack_of_reward_value_type():
    # given
    order_predicate = {
        "discounted_object_predicate": {"base_subtotal_price": {"range": {"gte": 100}}}
    }
    cleaned_input = {
        "order_predicate": order_predicate,
        "reward_value": 10,
    }
    errors = defaultdict(list)

    # when
    _clean_reward(
        cleaned_input,
        {},
        order_predicate,
        {},
        errors,
        PromotionCreateErrorCode,
        None,
        None,
    )

    # then
    assert len(errors) == 1
    assert len(errors["reward_value_type"]) == 1
    assert (
        errors["reward_value_type"][0].code == PromotionCreateErrorCode.REQUIRED.value
    )


def test_clean_reward_no_reward_value():
    # given
    order_predicate = {
        "discounted_object_predicate": {"base_subtotal_price": {"range": {"gte": 100}}}
    }
    cleaned_input = {
        "order_predicate": order_predicate,
        "reward_value_type": RewardValueType.FIXED,
    }
    errors = defaultdict(list)

    # when
    _clean_reward(
        cleaned_input,
        {},
        order_predicate,
        {},
        errors,
        PromotionCreateErrorCode,
        None,
        None,
    )

    # then
    assert len(errors) == 1
    assert len(errors["reward_value"]) == 1
    assert errors["reward_value"][0].code == PromotionCreateErrorCode.REQUIRED.value


def test_clean_reward_lack_of_reward_value_and_reward_value_type():
    # given
    order_predicate = {
        "discounted_object_predicate": {"base_subtotal_price": {"range": {"gte": 100}}}
    }
    cleaned_input = {
        "order_predicate": order_predicate,
    }
    errors = defaultdict(list)

    # when
    _clean_reward(
        cleaned_input,
        {},
        order_predicate,
        {},
        errors,
        PromotionCreateErrorCode,
        None,
        None,
    )

    # then
    assert len(errors) == 2
    assert len(errors["reward_value_type"]) == 1
    assert (
        errors["reward_value_type"][0].code == PromotionCreateErrorCode.REQUIRED.value
    )
    assert len(errors["reward_value"]) == 1
    assert errors["reward_value"][0].code == PromotionCreateErrorCode.REQUIRED.value


def test_clean_reward_value_missing_channels():
    # given
    reward_type = RewardType.SUBTOTAL_DISCOUNT
    reward_value = 10
    reward_value_type = RewardValueType.FIXED
    channel_currencies = {}
    cleaned_input = {
        "reward_value": reward_value,
        "reward_type": reward_type,
        "reward_value_type": reward_value_type,
    }
    errors = defaultdict(list)

    # when
    _clean_reward_value(
        cleaned_input,
        reward_value,
        reward_value_type,
        channel_currencies,
        errors,
        PromotionCreateErrorCode,
        None,
        None,
    )

    # then
    assert len(errors) == 1
    assert len(errors["channels"]) == 1
    assert errors["channels"][0].code == PromotionCreateErrorCode.MISSING_CHANNELS.value


def test_clean_reward_value_multiple_currencies():
    # given
    reward_type = RewardType.SUBTOTAL_DISCOUNT
    reward_value = 10
    reward_value_type = RewardValueType.FIXED
    channel_currencies = {"USD", "PLN"}
    cleaned_input = {
        "reward_value": reward_value,
        "reward_type": reward_type,
        "reward_value_type": reward_value_type,
    }
    errors = defaultdict(list)

    # when
    _clean_reward_value(
        cleaned_input,
        reward_value,
        reward_value_type,
        channel_currencies,
        errors,
        PromotionCreateErrorCode,
        None,
        None,
    )

    # then
    assert len(errors) == 1
    assert len(errors["reward_value_type"]) == 1
    assert (
        errors["reward_value_type"][0].code
        == PromotionCreateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.value
    )


def test_clean_reward_value_multiple_currencies_error_not_raised_for_percentage_disc():
    # given
    reward_type = RewardType.SUBTOTAL_DISCOUNT
    reward_value = 10
    reward_value_type = RewardValueType.PERCENTAGE
    channel_currencies = {"USD", "PLN"}
    cleaned_input = {
        "reward_value": reward_value,
        "reward_type": reward_type,
        "reward_value_type": reward_value_type,
    }
    errors = defaultdict(list)

    # when
    _clean_reward_value(
        cleaned_input,
        reward_value,
        reward_value_type,
        channel_currencies,
        errors,
        PromotionCreateErrorCode,
        None,
        None,
    )

    # then
    assert not errors


def test_clean_gift_rule(product_variant_list):
    # given
    cleaned_input = {
        "reward_type": RewardType.GIFT,
        "reward_value": None,
        "reward_value_type": None,
    }
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]
    errors = defaultdict(list)

    # when
    _clean_gift_rule(
        cleaned_input, gift_ids, errors, PromotionCreateErrorCode, None, None
    )

    # then
    assert not errors


@pytest.mark.parametrize("index", [None, 1, 0])
def test_clean_gift_rule_no_gifts(index):
    # given
    cleaned_input = {
        "reward_type": RewardType.GIFT,
        "reward_value": None,
        "reward_value_type": None,
    }
    gift_ids = []
    errors = defaultdict(list)
    index = 1

    # when
    _clean_gift_rule(
        cleaned_input, gift_ids, errors, PromotionCreateErrorCode, index, None
    )

    # then
    assert len(errors) == 1
    assert len(errors["gifts"]) == 1
    assert errors["gifts"][0].code == PromotionCreateErrorCode.REQUIRED.value
    assert errors["gifts"][0].params["index"] == index


@pytest.mark.parametrize("field", ["gifts", "add_gifts", "remove_gifts"])
def test_clean_gift_rule_invalid_gift_type(field, product_variant_list):
    # given
    gift_ids = [
        graphene.Node.to_global_id("Product", variant.id)
        for variant in product_variant_list
    ]
    cleaned_input = {
        "reward_type": RewardType.GIFT,
        "reward_value": None,
        "reward_value_type": None,
        field: gift_ids,
    }

    errors = defaultdict(list)
    index = 1

    # when
    _clean_gift_rule(
        cleaned_input, gift_ids, errors, PromotionCreateErrorCode, index, None
    )

    # then
    assert len(errors) == 1
    assert len(errors[field]) == 1
    assert errors[field][0].code == PromotionCreateErrorCode.INVALID_GIFT_TYPE.value
    assert errors[field][0].params["index"] == index
