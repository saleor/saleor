from datetime import timedelta
from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
from django.utils import timezone
from freezegun import freeze_time

from .. import RewardValueType
from ..models import Promotion, PromotionRule
from ..tasks import fetch_promotion_variants_and_product_ids, handle_promotion_toggle


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
@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.promotion_ended")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
def test_handle_promotion_toggle(
    promotion_started_mock,
    promotion_ended_mock,
    sale_toggle_mock,
    mock_update_products_discounted_prices_for_promotion_task,
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

    mock_update_products_discounted_prices_for_promotion_task.assert_called_once()
    args, kwargs = mock_update_products_discounted_prices_for_promotion_task.call_args
    # get ids of instances assigned to promotions that toggle
    assert {product_id for product_id in args[0]} == {
        product_list[0].id,
        product_list[2].id,
    }
