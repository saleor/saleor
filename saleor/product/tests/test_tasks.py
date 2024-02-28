import logging
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from django.utils import timezone

from ...discount import RewardValueType
from ...discount.models import Promotion, PromotionRule
from ..models import ProductChannelListing, ProductVariantChannelListing
from ..tasks import (
    _get_preorder_variants_to_clean,
    update_discounted_prices_task,
    update_products_discounted_prices_for_promotion_task,
    update_products_discounted_prices_of_promotion_task,
    update_products_search_vector_task,
    update_variants_names,
)


@patch("saleor.product.tasks.update_discounted_prices_task.delay")
def test_update_products_discounted_prices_of_promotion_task(
    update_discounted_prices_task_mock,
    product,
):
    # given
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("5.0"),
    )

    # when
    update_products_discounted_prices_of_promotion_task(promotion.id)

    # then
    update_discounted_prices_task_mock.assert_called_once()
    args, kwargs = update_discounted_prices_task_mock.call_args

    assert len(args[0]) == 1
    assert {id for id in args[0]} == {product.id}


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_update_products_discounted_prices_of_promotion_task_discount_does_not_exist(
    update_product_prices_mock, caplog
):
    # given
    caplog.set_level(logging.WARNING)
    promotion_id = uuid.uuid4()

    # when
    update_products_discounted_prices_of_promotion_task(promotion_id)

    # then
    update_product_prices_mock.assert_not_called()
    assert f"Cannot find promotion with id: {promotion_id}" in caplog.text


@patch("saleor.product.tasks.PROMOTION_RULE_BATCH_SIZE", 1)
@patch("saleor.product.tasks.update_discounted_prices_task.delay")
def test_update_products_discounted_prices_for_promotion_task(
    update_discounted_prices_task_mock,
    promotion_list,
    product_list,
    collection,
):
    # given
    Promotion.objects.update(start_date=timezone.now() - timedelta(days=1))
    product_ids = [product.id for product in product_list]
    PromotionRuleVariant = PromotionRule.variants.through
    PromotionRuleVariant.objects.all().delete()

    collection.products.add(*product_list[1:])

    # when
    update_products_discounted_prices_for_promotion_task(product_ids)

    # then
    update_discounted_prices_task_mock.assert_called_once_with(product_ids)
    assert set(
        PromotionRuleVariant.objects.values_list("promotionrule_id", flat=True)
    ) == set(PromotionRule.objects.values_list("id", flat=True))


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
@patch("saleor.product.tasks.PROMOTION_RULE_BATCH_SIZE", 1)
@patch("saleor.product.tasks.update_discounted_prices_task.delay")
def test_update_products_discounted_prices_for_promotion_task_with_order_predicate(
    update_discounted_prices_task_mock,
    update_products_discounted_prices_for_promotion_task_delay_mocked,
    promotion_list,
    product_list,
):
    # given
    Promotion.objects.update(start_date=timezone.now() - timedelta(days=1))
    product_ids = [product.id for product in product_list]
    PromotionRule.objects.update(catalogue_predicate={})
    PromotionRuleVariant = PromotionRule.variants.through

    # when
    update_products_discounted_prices_for_promotion_task(product_ids)

    # then
    assert not update_products_discounted_prices_for_promotion_task_delay_mocked.called
    update_discounted_prices_task_mock.assert_called_once_with(product_ids)
    assert set(
        PromotionRuleVariant.objects.values_list("promotionrule_id", flat=True)
    ) == set(PromotionRule.objects.values_list("id", flat=True))


@patch("saleor.product.tasks.PROMOTION_RULE_BATCH_SIZE", 1)
@patch("saleor.product.tasks.update_discounted_prices_task.delay")
@patch("saleor.product.utils.variants.fetch_variants_for_promotion_rules")
def test_update_products_discounted_prices_for_promotion_task_with_rules_id(
    fetch_variants_for_promotion_rules_mock,
    update_discounted_prices_task_mock,
    promotion_list,
    collection,
    product_list,
):
    # given
    Promotion.objects.update(start_date=timezone.now() - timedelta(days=1))
    PromotionRuleVariant = PromotionRule.variants.through
    PromotionRuleVariant.objects.all().delete()

    collection.products.add(*product_list[1:])

    rule_id = PromotionRule.objects.first().id
    product_ids = [product.id for product in product_list]

    # when
    update_products_discounted_prices_for_promotion_task(
        product_ids, rule_ids=[rule_id]
    )

    # then
    update_discounted_prices_task_mock.assert_called_once_with(product_ids)
    assert set(
        PromotionRuleVariant.objects.values_list("promotionrule_id", flat=True)
    ) == {rule_id}


@pytest.mark.parametrize("reward_value", [None, 0])
@patch("saleor.product.tasks.PROMOTION_RULE_BATCH_SIZE", 1)
@patch("saleor.product.tasks.update_discounted_prices_task.delay")
@patch("saleor.product.utils.variants.fetch_variants_for_promotion_rules")
def test_update_products_discounted_prices_for_promotion_task_with_empty_reward_value(
    fetch_variants_for_promotion_rules_mock,
    update_discounted_prices_task_mock,
    reward_value,
    promotion_list,
    collection,
    product_list,
):
    # given
    Promotion.objects.update(start_date=timezone.now() - timedelta(days=1))
    PromotionRuleVariant = PromotionRule.variants.through
    PromotionRuleVariant.objects.all().delete()

    collection.products.add(*product_list[1:])

    rule = PromotionRule.objects.first()
    rule.reward_value = reward_value
    rule.save(update_fields=["reward_value"])
    rule_id = PromotionRule.objects.first().id
    product_ids = [product.id for product in product_list]

    # when
    update_products_discounted_prices_for_promotion_task(
        product_ids, rule_ids=[rule_id]
    )

    # then
    update_discounted_prices_task_mock.assert_called_once_with(product_ids)
    assert (
        set(PromotionRuleVariant.objects.values_list("promotionrule_id", flat=True))
        == set()
    )


@patch("saleor.product.tasks.DISCOUNTED_PRODUCT_BATCH", 1)
def test_update_discounted_prices_task(
    product_list,
):
    # given
    ids = [product.id for product in product_list]
    ProductChannelListing.objects.update(discounted_price_amount=0)
    ProductVariantChannelListing.objects.update(discounted_price_amount=0)

    # when
    update_discounted_prices_task(ids)

    # then
    assert not ProductChannelListing.objects.filter(discounted_price_amount=0).exists()
    assert not ProductVariantChannelListing.objects.filter(
        discounted_price_amount=0
    ).exists()


@patch("saleor.product.tasks._update_variants_names")
def test_update_variants_names(
    update_variants_names_mock, product_type, size_attribute
):
    # when
    update_variants_names(product_type.id, [size_attribute.id])

    # then
    args, _ = update_variants_names_mock.call_args
    assert args[0] == product_type
    assert {arg.pk for arg in args[1]} == {size_attribute.pk}


def test_update_variants_names_product_type_does_not_exist(caplog):
    # given
    caplog.set_level(logging.WARNING)
    product_type_id = -1

    # when
    update_variants_names(product_type_id, [])

    # then
    assert f"Cannot find product type with id: {product_type_id}" in caplog.text


def test_get_preorder_variants_to_clean(
    variant,
    preorder_variant_global_threshold,
    preorder_variant_channel_threshold,
    preorder_variant_global_and_channel_threshold,
):
    preorder_variant_before_end_date = preorder_variant_channel_threshold
    preorder_variant_before_end_date.preorder_end_date = timezone.now() + timedelta(
        days=1
    )
    preorder_variant_before_end_date.save(update_fields=["preorder_end_date"])

    preorder_variant_after_end_date = preorder_variant_global_and_channel_threshold
    preorder_variant_after_end_date.preorder_end_date = timezone.now() - timedelta(
        days=1
    )
    preorder_variant_after_end_date.save(update_fields=["preorder_end_date"])

    variants_to_clean = _get_preorder_variants_to_clean()
    assert len(variants_to_clean) == 1
    assert variants_to_clean[0] == preorder_variant_after_end_date


def test_update_products_search_vector_task(product):
    # given
    product.search_index_dirty = True
    product.save(update_fields=["search_index_dirty"])

    # when
    update_products_search_vector_task()
    product.refresh_from_db(fields=["search_index_dirty"])

    # then
    assert product.search_index_dirty is False


@pytest.mark.parametrize("dirty_products_number", [0, 1, 2, 3])
def test_update_products_search_vector_task_with_static_number_of_queries(
    product, product_list, dirty_products_number, django_assert_num_queries
):
    # given
    product.search_index_dirty = True
    product.save()
    for i in range(dirty_products_number):
        product_list[i].search_index_dirty = True
        product_list[i].save(update_fields=["search_index_dirty"])

    # when & # then
    with django_assert_num_queries(12):
        update_products_search_vector_task()


@pytest.mark.slow
@pytest.mark.limit_memory("50 MB")
def test_mem_usage_update_products_discounted_prices(lots_of_products_with_variants):
    update_products_discounted_prices_for_promotion_task(
        lots_of_products_with_variants.values_list("pk", flat=True)
    )
