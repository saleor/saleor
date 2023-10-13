from unittest import mock

import graphene

from .....discount.models import Promotion
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
@mock.patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_delete_promotions_trigger_webhooks(
    update_products_discounted_prices_for_promotion_task,
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
    update_products_discounted_prices_for_promotion_task.called_once()
    assert deleted_webhook_mock.call_count == len(promotion_list)
