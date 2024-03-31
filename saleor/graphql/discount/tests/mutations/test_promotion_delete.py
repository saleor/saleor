from unittest.mock import patch

import graphene
import pytest

from .....discount.models import PromotionRule
from .....product.models import ProductChannelListing
from ....tests.utils import assert_no_permission, get_graphql_content
from ...utils import get_products_for_promotion

PROMOTION_DELETE_MUTATION = """
    mutation promotionDelete($id: ID!) {
        promotionDelete(id: $id) {
            promotion {
                name
                id
            }
            errors {
                field
                code
                message
            }
            }
        }
"""


@patch("saleor.plugins.manager.PluginsManager.promotion_deleted")
def test_promotion_delete_by_staff_user(
    promotion_deleted_mock,
    staff_api_client,
    permission_group_manage_discounts,
    catalogue_promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion = catalogue_promotion
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}
    PromotionRuleChannel = PromotionRule.channels.through
    channels_ids = set(
        PromotionRuleChannel.objects.filter(
            promotionrule__in=promotion.rules.all()
        ).values_list("channel_id", flat=True)
    )
    products_ids = list(
        get_products_for_promotion(promotion).values_list("id", flat=True)
    )

    # when
    response = staff_api_client.post_graphql(PROMOTION_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionDelete"]
    assert data["promotion"]["name"] == promotion.name

    promotion_deleted_mock.assert_called_once_with(promotion)

    with pytest.raises(promotion._meta.model.DoesNotExist):
        promotion.refresh_from_db()

    for listing in ProductChannelListing.objects.filter(
        channel_id__in=channels_ids, product_id__in=products_ids
    ):
        assert listing.discounted_price_dirty is True


@patch("saleor.plugins.manager.PluginsManager.promotion_deleted")
def test_promotion_delete_by_staff_app(
    promotion_deleted_mock,
    app_api_client,
    permission_manage_discounts,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}
    PromotionRuleChannel = PromotionRule.channels.through
    channels_ids = set(
        PromotionRuleChannel.objects.filter(
            promotionrule__in=promotion.rules.all()
        ).values_list("channel_id", flat=True)
    )
    products_ids = list(
        get_products_for_promotion(promotion).values_list("id", flat=True)
    )

    # when
    response = app_api_client.post_graphql(
        PROMOTION_DELETE_MUTATION, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionDelete"]
    assert data["promotion"]["name"] == promotion.name

    promotion_deleted_mock.assert_called_once_with(promotion)

    with pytest.raises(promotion._meta.model.DoesNotExist):
        promotion.refresh_from_db()

    for listing in ProductChannelListing.objects.filter(
        channel_id__in=channels_ids, product_id__in=products_ids
    ):
        assert listing.discounted_price_dirty is True


@patch("saleor.plugins.manager.PluginsManager.promotion_deleted")
def test_promotion_delete_by_customer(
    promotion_deleted_mock,
    api_client,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}
    PromotionRuleChannel = PromotionRule.channels.through
    channels_ids = set(
        PromotionRuleChannel.objects.filter(
            promotionrule__in=promotion.rules.all()
        ).values_list("channel_id", flat=True)
    )
    products_ids = list(
        get_products_for_promotion(promotion).values_list("id", flat=True)
    )

    # when
    response = api_client.post_graphql(PROMOTION_DELETE_MUTATION, variables)

    # then
    assert_no_permission(response)

    promotion_deleted_mock.assert_not_called()
    for listing in ProductChannelListing.objects.filter(
        channel_id__in=channels_ids, product_id__in=products_ids
    ):
        assert listing.discounted_price_dirty is False
