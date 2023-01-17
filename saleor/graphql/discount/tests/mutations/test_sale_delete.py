from unittest.mock import patch

import graphene
import pytest

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


@patch("saleor.plugins.manager.PluginsManager.sale_deleted")
def test_sale_delete_mutation(
    deleted_webhook_mock, staff_api_client, sale, permission_manage_discounts
):
    query = SALE_DELETE_MUTATION
    variables = {"id": graphene.Node.to_global_id("Sale", sale.id)}
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["saleDelete"]
    assert data["sale"]["name"] == sale.name
    deleted_webhook_mock.assert_called_once_with(sale, previous_catalogue)
    with pytest.raises(sale._meta.model.DoesNotExist):
        sale.refresh_from_db()
