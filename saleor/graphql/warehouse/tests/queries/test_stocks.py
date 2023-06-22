from .....permission.enums import ProductPermissions
from .....warehouse.models import Stock
from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_STOCKS = """
    query {
        stocks(first:100) {
            totalCount
            edges {
                node {
                    id
                    warehouse {
                        name
                        id
                    }
                    productVariant {
                        name
                        id
                    }
                    quantity
                    quantityAllocated
                    quantityReserved
                }
            }
        }
    }
"""


def test_query_stocks_requires_permissions(staff_api_client):
    # given
    assert not staff_api_client.user.has_perm(ProductPermissions.MANAGE_PRODUCTS)

    # when
    response = staff_api_client.post_graphql(QUERY_STOCKS)

    # then
    assert_no_permission(response)


def test_query_stocks(staff_api_client, stock, permission_manage_products):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(QUERY_STOCKS)

    # then
    content = get_graphql_content(response)
    total_count = content["data"]["stocks"]["totalCount"]
    assert total_count == Stock.objects.count()
