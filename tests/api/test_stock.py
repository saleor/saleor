import graphene

from saleor.core.permissions import ProductPermissions
from saleor.warehouse.models import Stock

from ..utils import get_quantity_allocated_for_stock
from .utils import assert_no_permission, get_graphql_content

QUERY_STOCK = """
query stock($id: ID!) {
    stock(id: $id) {
        warehouse {
            name
        }
        productVariant {
            product {
                name
            }
        }
        quantity
        quantityAllocated
        stockQuantity
    }
}
"""


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
                }
            }
        }
    }
"""

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


def test_query_stock_requires_permission(staff_api_client, stock):
    assert not staff_api_client.user.has_perm(ProductPermissions.MANAGE_PRODUCTS)
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)
    response = staff_api_client.post_graphql(QUERY_STOCK, variables={"id": stock_id})
    assert_no_permission(response)


def test_query_stock(staff_api_client, stock, permission_manage_products):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)
    response = staff_api_client.post_graphql(QUERY_STOCK, variables={"id": stock_id})
    content = get_graphql_content(response)
    content_stock = content["data"]["stock"]
    assert (
        content_stock["productVariant"]["product"]["name"]
        == stock.product_variant.product.name
    )
    assert content_stock["warehouse"]["name"] == stock.warehouse.name
    assert content_stock["quantity"] == stock.quantity
    assert content_stock["quantityAllocated"] == get_quantity_allocated_for_stock(stock)


def test_query_stocks_requires_permissions(staff_api_client):
    assert not staff_api_client.user.has_perm(ProductPermissions.MANAGE_PRODUCTS)
    response = staff_api_client.post_graphql(QUERY_STOCKS)
    assert_no_permission(response)


def test_query_stocks(staff_api_client, stock, permission_manage_products):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_STOCKS)
    content = get_graphql_content(response)
    total_count = content["data"]["stocks"]["totalCount"]
    assert total_count == Stock.objects.count()


def test_query_stocks_with_filters_quantity(
    staff_api_client, stock, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    quantities = Stock.objects.all().values_list("quantity", flat=True)
    sum_quantities = sum(quantities)
    variables = {"filter": {"quantity": sum_quantities}}
    response = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS, variables=variables
    )
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
    staff_api_client.user.user_permissions.add(permission_manage_products)
    warehouse = stock.warehouse
    response_name = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS, variables={"filter": {"search": warehouse.name}}
    )
    content = get_graphql_content(response_name)
    total_count = content["data"]["stocks"]["totalCount"]
    assert total_count == Stock.objects.filter(warehouse=warehouse).count()


def test_query_stocks_with_filters_product_variant(
    staff_api_client, stock, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product_variant = stock.product_variant
    response_name = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS,
        variables={"filter": {"search": product_variant.name}},
    )
    content = get_graphql_content(response_name)
    total_count = content["data"]["stocks"]["totalCount"]
    assert (
        total_count
        == Stock.objects.filter(product_variant__name=product_variant.name).count()
    )


def test_query_stocks_with_filters_product_variant__product(
    staff_api_client, stock, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product = stock.product_variant.product
    response_name = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS, variables={"filter": {"search": product.name}}
    )
    content = get_graphql_content(response_name)
    total_count = content["data"]["stocks"]["totalCount"]
    assert (
        total_count
        == Stock.objects.filter(product_variant__product__name=product.name).count()
    )


def test_query_available_stock_quantity(
    staff_api_client, permission_manage_products, stock, settings
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)

    available_quantity = stock.quantity - get_quantity_allocated_for_stock(stock)
    # set MAX_CHECKOUT_LINE_QUANTITY smaller than available quantity
    settings.MAX_CHECKOUT_LINE_QUANTITY = available_quantity - 1

    response = staff_api_client.post_graphql(QUERY_STOCK, variables={"id": stock_id})
    content = get_graphql_content(response)
    content_quantity_available = content["data"]["stock"]["stockQuantity"]
    assert content_quantity_available == settings.MAX_CHECKOUT_LINE_QUANTITY

    # set MAX_CHECKOUT_LINE_QUANTITY larger than available quantity
    settings.MAX_CHECKOUT_LINE_QUANTITY = available_quantity + 1

    response = staff_api_client.post_graphql(QUERY_STOCK, variables={"id": stock_id})
    content = get_graphql_content(response)
    content_quantity_available = content["data"]["stock"]["stockQuantity"]
    assert content_quantity_available == available_quantity
