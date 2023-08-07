from unittest.mock import patch

import graphene
import pytest

from .....discount.models import Promotion, PromotionRule
from .....discount.sale_converter import convert_sales_to_promotions
from .....discount.utils import fetch_catalogue_info
from ....tests.utils import get_graphql_content
from ...mutations.utils import convert_catalogue_info_to_global_ids

SALE_DELETE_MUTATION = """
    mutation DeleteSale($id: ID!) {
        saleDelete(id: $id) {
            sale {
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


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_deleted")
def test_sale_delete_mutation(
    deleted_webhook_mock,
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    # given
    query = SALE_DELETE_MUTATION
    variables = {"id": graphene.Node.to_global_id("Sale", sale.id)}
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    convert_sales_to_promotions()

    promotion = Promotion.objects.get(old_sale_id=sale.id)
    assert promotion
    rules = promotion.rules.all()
    assert len(rules) == 1

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleDelete"]["errors"]
    data = content["data"]["saleDelete"]["sale"]
    assert data["name"] == sale.name
    assert data["id"] == graphene.Node.to_global_id("Sale", sale.id)

    assert not Promotion.objects.filter(id=promotion.id).first()
    assert not PromotionRule.objects.filter(id=rules[0].id).first()
    with pytest.raises(promotion._meta.model.DoesNotExist):
        promotion.refresh_from_db()

    deleted_webhook_mock.assert_called_once_with(promotion, previous_catalogue)
    update_products_discounted_prices_for_promotion_task_mock.assert_called_once()
