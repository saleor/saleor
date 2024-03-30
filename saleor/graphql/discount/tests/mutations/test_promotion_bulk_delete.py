from unittest import mock

import graphene

from .....discount.models import Promotion, PromotionRule
from .....product.models import ProductChannelListing, ProductVariant
from ....tests.utils import get_graphql_content

PROMOTION_BULK_DELETE_MUTATION = """
    mutation promotionBulkDelete($ids: [ID!]!) {
        promotionBulkDelete(ids: $ids) {
            count
            errors {
                field
                code
            }
        }
    }
    """


def test_delete_promotions_by_staff(
    staff_api_client,
    promotion_list,
    permission_manage_discounts,
):
    # given
    variables = {
        "ids": [
            graphene.Node.to_global_id("Promotion", promotion.id)
            for promotion in promotion_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        PROMOTION_BULK_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["promotionBulkDelete"]["errors"]
    assert content["data"]["promotionBulkDelete"]["count"] == 3
    assert not Promotion.objects.filter(
        pk__in=[promotion.id for promotion in promotion_list]
    ).exists()


def test_delete_promotions_by_app(
    app_api_client,
    promotion_list,
    permission_manage_discounts,
):
    # given
    variables = {
        "ids": [
            graphene.Node.to_global_id("Promotion", promotion.id)
            for promotion in promotion_list
        ]
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_BULK_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["promotionBulkDelete"]["errors"]
    assert content["data"]["promotionBulkDelete"]["count"] == 3
    assert not Promotion.objects.filter(
        pk__in=[promotion.id for promotion in promotion_list]
    ).exists()


@mock.patch("saleor.plugins.manager.PluginsManager.promotion_deleted")
def test_delete_promotions_trigger_webhooks(
    deleted_webhook_mock,
    staff_api_client,
    promotion_list,
    permission_manage_discounts,
):
    # given
    variables = {
        "ids": [
            graphene.Node.to_global_id("Promotion", promotion.id)
            for promotion in promotion_list
        ]
    }

    # when
    staff_api_client.post_graphql(
        PROMOTION_BULK_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    assert deleted_webhook_mock.call_count == len(promotion_list)


def test_delete_promotions_marks_product_to_recalculate(
    staff_api_client, promotion_list, permission_manage_discounts, channel_USD
):
    # given
    rules = PromotionRule.objects.filter(promotion__in=promotion_list)
    PromotionRuleVariant = PromotionRule.variants.through
    variant_ids = PromotionRuleVariant.objects.filter(
        promotionrule_id__in=rules
    ).values_list("productvariant_id", flat=True)
    product_ids = ProductVariant.objects.filter(id__in=variant_ids).values_list(
        "product_id", flat=True
    )
    assert ProductChannelListing.objects.filter(
        product_id__in=product_ids, channel=channel_USD, discounted_price_dirty=False
    ).exists()

    variables = {
        "ids": [
            graphene.Node.to_global_id("Promotion", promotion.id)
            for promotion in promotion_list
        ]
    }

    # when
    staff_api_client.post_graphql(
        PROMOTION_BULK_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    assert not ProductChannelListing.objects.filter(
        product_id__in=product_ids, channel=channel_USD, discounted_price_dirty=False
    ).exists()
