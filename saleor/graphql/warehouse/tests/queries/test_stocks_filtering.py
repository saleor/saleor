from .....warehouse.models import Stock
from ....tests.utils import get_graphql_content

QUERY_STOCKS_WITH_FILTERS = """
    query stocks($filter: StockFilterInput!) {
        stocks(first: 100, filter: $filter) {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
"""


def test_query_stocks_with_filters_quantity(
    staff_api_client, stock, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    quantities = Stock.objects.all().values_list("quantity", flat=True)
    sum_quantities = sum(quantities)
    variables = {"filter": {"quantity": sum_quantities}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS, variables=variables
    )

    # then
    content = get_graphql_content(response)
    total_count = content["data"]["stocks"]["totalCount"]
    assert total_count == 0

    variables = {"filter": {"quantity": max(quantities)}}
    response = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS, variables=variables
    )
    content = get_graphql_content(response)
    total_count = content["data"]["stocks"]["totalCount"]
    assert total_count == Stock.objects.filter(quantity=max(quantities)).count()


def test_query_stocks_with_filters_warehouse(
    staff_api_client, stock, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    warehouse = stock.warehouse

    # when
    response_name = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS, variables={"filter": {"search": warehouse.name}}
    )

    # then
    content = get_graphql_content(response_name)
    total_count = content["data"]["stocks"]["totalCount"]
    assert total_count == Stock.objects.filter(warehouse=warehouse).count()


def test_query_stocks_with_filters_product_variant(
    staff_api_client, stock, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product_variant = stock.product_variant

    # when
    response_name = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS,
        variables={"filter": {"search": product_variant.name}},
    )

    # then
    content = get_graphql_content(response_name)
    total_count = content["data"]["stocks"]["totalCount"]
    assert (
        total_count
        == Stock.objects.filter(product_variant__name=product_variant.name).count()
    )


def test_query_stocks_with_filters_product_variant__product(
    staff_api_client, stock, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product = stock.product_variant.product

    # when
    response_name = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS, variables={"filter": {"search": product.name}}
    )

    # then
    content = get_graphql_content(response_name)
    total_count = content["data"]["stocks"]["totalCount"]
    assert (
        total_count
        == Stock.objects.filter(product_variant__product__name=product.name).count()
    )
