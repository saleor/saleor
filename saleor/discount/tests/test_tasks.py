from datetime import timedelta
from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
import pytest
from django.db.models import Exists, OuterRef
from django.utils import timezone
from freezegun import freeze_time

from ...order.models import Order
from ...product.models import ProductChannelListing, ProductVariant
from .. import DiscountType, RewardValueType
from ..models import OrderDiscount, OrderLineDiscount, Promotion, PromotionRule
from ..tasks import (
    clear_promotion_rule_variants_task,
    decrease_voucher_codes_usage_task,
    disconnect_voucher_codes_from_draft_orders_task,
    fetch_promotion_variants_and_product_ids,
    handle_promotion_toggle,
    set_promotion_rule_variants_task,
)
from ..utils.promotion import mark_catalogue_promotion_rules_as_dirty


def test_fetch_promotion_variants_and_product_ids(
    promotion_list, product, collection, product_list
):
    # given
    promotions = Promotion.objects.all()

    collection.products.set(product_list[:2])

    product_variants = set(product.variants.values_list("id", flat=True))
    collection_variants = {
        id
        for product in product_list[:2]
        for id in product.variants.values_list("id", flat=True)
    }

    # when
    promotion_id_to_variants, product_ids = fetch_promotion_variants_and_product_ids(
        promotions
    )

    # then
    expected_product_ids = {product.id, product_list[0].id, product_list[1].id}
    assert set(product_ids) == expected_product_ids

    variants_promo_1 = promotion_id_to_variants[promotion_list[0].id]
    variants_promo_2 = promotion_id_to_variants[promotion_list[1].id]
    variants_promo_3 = promotion_id_to_variants[promotion_list[2].id]

    assert {variant.id for variant in variants_promo_1} == product_variants.union(
        collection_variants
    )
    assert {variant.id for variant in variants_promo_2} == product_variants
    assert {variant.id for variant in variants_promo_3} == collection_variants


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.discount.tasks.clear_promotion_rule_variants_task.delay")
@patch(
    "saleor.discount.tasks.mark_catalogue_promotion_rules_as_dirty",
    wraps=mark_catalogue_promotion_rules_as_dirty,
)
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.promotion_ended")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
def test_handle_promotion_toggle(
    promotion_started_mock,
    promotion_ended_mock,
    sale_toggle_mock,
    mock_mark_catalogue_promotion_rules_as_dirty,
    mock_clear_promotion_rule_variants_task,
    product_list,
):
    # given
    now = timezone.now()
    promotions = Promotion.objects.bulk_create(
        [Promotion(name=f"Promotion-{i}") for i in range(10)]
    )

    rules = []
    for promotion, product in zip(promotions, product_list):
        rules.append(
            PromotionRule(
                promotion=promotion,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=Decimal("5"),
            )
        )

    PromotionRule.objects.bulk_create(rules)

    # promotions with start date before current date
    # without notification sent day - should be sent for started
    promotions[0].start_date = now - timedelta(days=1)
    promotions[0].last_notification_scheduled_at = None

    # with notification sent day after the start date - shouldn't be sent
    promotions[1].start_date = now - timedelta(days=1)
    promotions[1].last_notification_scheduled_at = now - timedelta(minutes=2)

    # with notification sent day before the start date - should be sent for started
    promotions[2].start_date = now - timedelta(minutes=2)
    promotions[2].last_notification_scheduled_at = now - timedelta(minutes=5)

    # without notification sent day
    # promotions with start date after current date - shouldn't be sent
    promotions[3].start_date = now + timedelta(days=1)
    promotions[3].last_notification_scheduled_at = None

    # with notification sent day before the start date
    promotions[4].start_date = now + timedelta(days=1)
    promotions[4].last_notification_scheduled_at = now - timedelta(minutes=5)

    # promotions with end date before current date
    # without notification sent day - should be sent for ended
    promotions[5].start_date = now - timedelta(days=2)
    promotions[5].end_date = now - timedelta(days=1)
    promotions[5].last_notification_scheduled_at = None

    # with notification sent day after the start date - shouldn't be sent
    promotions[6].start_date = now - timedelta(days=2)
    promotions[6].end_date = now - timedelta(days=1)
    promotions[6].last_notification_scheduled_at = now - timedelta(minutes=2)

    # with notification sent day before the start date - should be sent for ended
    promotions[7].start_date = now - timedelta(days=2)
    promotions[7].end_date = now - timedelta(minutes=2)
    promotions[7].last_notification_scheduled_at = now - timedelta(minutes=5)

    # promotions with end date after current date
    # without notification sent day
    promotions[8].start_date = now + timedelta(days=2)
    promotions[8].end_date = now + timedelta(days=1)
    promotions[8].last_notification_scheduled_at = None

    # with notification sent day before the start date
    promotions[9].start_date = now + timedelta(days=2)
    promotions[9].end_date = now + timedelta(days=1)
    promotions[9].last_notification_scheduled_at = now - timedelta(minutes=5)

    Promotion.objects.bulk_update(
        promotions,
        [
            "start_date",
            "end_date",
            "last_notification_scheduled_at",
        ],
    )
    indexes_of_started_promotions = {0, 2, 5}
    indexes_of_ended_promotions = {5, 7}
    indexes_of_toggle_sales = indexes_of_started_promotions.union(
        indexes_of_ended_promotions
    )

    # when
    handle_promotion_toggle()

    # then
    assert promotion_started_mock.call_count == len(indexes_of_started_promotions)
    assert promotion_ended_mock.call_count == len(indexes_of_ended_promotions)
    assert sale_toggle_mock.call_count == len(indexes_of_toggle_sales)

    started_args_list = [args.args for args in promotion_started_mock.call_args_list]
    for index in indexes_of_started_promotions:
        assert (promotions[index],) in started_args_list

    ended_args_list = [args.args for args in promotion_ended_mock.call_args_list]
    for index in indexes_of_ended_promotions:
        assert (promotions[index],) in ended_args_list

    toggle_args_list = [args.args for args in sale_toggle_mock.call_args_list]
    for index in indexes_of_toggle_sales:
        assert (promotions[index], ANY) in toggle_args_list

    for index in indexes_of_started_promotions | indexes_of_ended_promotions:
        promotions[index].refresh_from_db()
        assert promotions[index].last_notification_scheduled_at == now

    assert PromotionRule.objects.filter(variants_dirty=True).count() == 2

    mock_mark_catalogue_promotion_rules_as_dirty.assert_called_once_with(
        set([promotions[index].id for index in indexes_of_toggle_sales])
    )

    mock_clear_promotion_rule_variants_task.assert_called_once()


def test_clear_promotion_rule_variants_task(promotion_list):
    # given
    expired_promotion = promotion_list[-1]
    expired_promotion.start_date = timezone.now() - timedelta(days=5)
    expired_promotion.end_date = timezone.now() - timedelta(days=1)
    expired_promotion.save(update_fields=["start_date", "end_date"])

    PromotionRuleVariant = PromotionRule.variants.through
    expired_rules = PromotionRule.objects.filter(promotion_id=expired_promotion.id)
    rule_variants_count = PromotionRuleVariant.objects.count()
    expired_rule_variants_count = PromotionRuleVariant.objects.filter(
        Exists(expired_rules.filter(pk=OuterRef("promotionrule_id")))
    ).count()
    assert expired_rule_variants_count > 0

    # when
    clear_promotion_rule_variants_task()

    # then
    assert (
        PromotionRuleVariant.objects.count()
        == rule_variants_count - expired_rule_variants_count
    )


def test_clear_promotion_rule_variants_task_marks_products_as_dirty(promotion_list):
    # given
    expired_promotion = promotion_list[-1]
    expired_promotion.start_date = timezone.now() - timedelta(days=5)
    expired_promotion.end_date = timezone.now() - timedelta(days=1)
    expired_promotion.save(update_fields=["start_date", "end_date"])

    PromotionRuleVariant = PromotionRule.variants.through
    expired_rules = PromotionRule.objects.filter(promotion_id=expired_promotion.id)
    assert not ProductChannelListing.objects.filter(discounted_price_dirty=True)

    # when
    clear_promotion_rule_variants_task()

    # then
    rule_variants = PromotionRuleVariant.objects.filter(
        Exists(expired_rules.filter(pk=OuterRef("promotionrule_id")))
    )
    variant_to_product_qs = ProductVariant.objects.filter(
        Exists(rule_variants.filter(productvariant_id=OuterRef("id")))
    ).values_list("id", "product_id")
    assert not ProductChannelListing.objects.filter(
        product_id__in=[product_id for _, product_id in variant_to_product_qs],
        discounted_price_dirty=False,
    )


def test_set_promotion_rule_variants_task(promotion_list):
    # given
    Promotion.objects.update(start_date=timezone.now() - timedelta(days=5))
    PromotionRuleVariant = PromotionRule.variants.through
    PromotionRuleVariant.objects.all().delete()

    # when
    set_promotion_rule_variants_task()

    # then
    assert set(
        PromotionRuleVariant.objects.values_list("promotionrule_id", flat=True)
    ) == set(PromotionRule.objects.values_list("id", flat=True))


def test_decrease_voucher_code_usage_task_multiple_use(
    draft_order_list_with_multiple_use_voucher, voucher_multiple_use
):
    # given
    order_list = draft_order_list_with_multiple_use_voucher
    voucher = voucher_multiple_use
    voucher_codes = voucher.codes.all()[: len(order_list)]
    assert all([voucher_code.used == 1 for voucher_code in voucher_codes])
    voucher_code_ids = [voucher_code.pk for voucher_code in voucher_codes]

    # when
    decrease_voucher_codes_usage_task(voucher_code_ids)

    # then
    voucher_codes = voucher.codes.all()[: len(order_list)]
    assert all([voucher_code.used == 0 for voucher_code in voucher_codes])


def test_decrease_voucher_code_usage_task_single_use(
    draft_order_list_with_single_use_voucher, voucher_single_use
):
    # given
    order_list = draft_order_list_with_single_use_voucher
    voucher = voucher_single_use
    voucher_codes = voucher.codes.all()[: len(order_list)]
    assert all([voucher_code.is_active is False for voucher_code in voucher_codes])
    voucher_code_ids = [voucher_code.pk for voucher_code in voucher_codes]

    # when
    decrease_voucher_codes_usage_task(voucher_code_ids)

    # then
    voucher_codes = voucher.codes.all()[: len(order_list)]
    assert all([voucher_code.is_active is True for voucher_code in voucher_codes])


def test_disconnect_voucher_codes_from_draft_orders(
    draft_order_list_with_multiple_use_voucher, order_line
):
    # given
    order_list = draft_order_list_with_multiple_use_voucher
    order = order_list[0]
    order.lines.add(order_line)

    order_list_ids = [order.id for order in order_list]
    assert all([order.voucher_code for order in order_list])
    for order in order_list:
        order.should_refresh_prices = False
    Order.objects.bulk_update(order_list, ["should_refresh_prices"])
    assert all([order.should_refresh_prices is False for order in order_list])

    voucher_code = order.voucher_code
    order_discount = OrderDiscount.objects.create(
        order=order, voucher_code=voucher_code, type=DiscountType.VOUCHER
    )
    line_discount = OrderLineDiscount.objects.create(
        line=order_line, type=DiscountType.VOUCHER
    )

    # when
    disconnect_voucher_codes_from_draft_orders_task(order_list_ids)

    # then
    order_list = Order.objects.filter(id__in=order_list_ids).all()
    assert all([order.voucher_code is None for order in order_list])
    assert all([order.should_refresh_prices is True for order in order_list])

    with pytest.raises(line_discount._meta.model.DoesNotExist):
        line_discount.refresh_from_db()
    with pytest.raises(order_discount._meta.model.DoesNotExist):
        order_discount.refresh_from_db()
