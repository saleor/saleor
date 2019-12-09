import graphene

from saleor.stock.models import Stock
from tests.api.utils import assert_no_permission, get_graphql_content

MUTATION_CREATE_STOCK = """
mutation createStock($input: StockInput!) {
    createStock(input: $input) {
        errors {
            field
            message
        }
        stock {
            id
            quantity
            quantityAllocated
        }
    }
}
"""


MUTATION_UPDATE_STOCK = """
mutation updateStock($id: ID!, $input: StockInput!) {
    updateStock(id: $id, input: $input) {
        errors {
            field
            message
        }
        stock {
            id
            quantity
            quantityAllocated
        }
    }
}
"""


MUTATION_DELETE_STOCK = """
mutation deleteStock($id: ID!) {
    deleteStock(id: $id){
        errors {
            field
            message
        }
    }
}
"""


MUTATION_BULK_DELETE_STOCK = """
mutation bulkDeleteStock($ids: [ID]!) {
    bulkDeleteStock(ids: $ids) {
        count
        errors {
            field
            message
        }
    }
}
"""


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
        available
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


def test_stock_cannot_be_created_without_permission(
    staff_api_client, variant, warehouse
):
    assert not staff_api_client.user.has_perm("stock.manage_stocks")
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {
        "input": {
            "warehouse": warehouse_id,
            "productVariant": variant_id,
            "quantity": 100,
            "quantityAllocated": 23,
        }
    }

    response = staff_api_client.post_graphql(MUTATION_CREATE_STOCK, variables=variables)
    assert_no_permission(response)


def test_create_stock_mutation(
    staff_api_client, variant, warehouse, permission_manage_stocks
):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    old_stock_count = Stock.objects.count()

    variables = {
        "input": {
            "productVariant": variant_id,
            "warehouse": warehouse_id,
            "quantity": 100,
            "quantityAllocated": 27,
        }
    }
    response = staff_api_client.post_graphql(MUTATION_CREATE_STOCK, variables)
    content = get_graphql_content(response)
    assert Stock.objects.count() == old_stock_count + 1
    content_errors = content["data"]["createStock"]["errors"]
    assert len(content_errors) == 0


def test_update_stock_required_permission(staff_api_client, stock):
    assert not staff_api_client.user.has_perm("stock.manage_stocks")
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", stock.product_variant.pk)
    warehouse_id = graphene.Node.to_global_id("Warehouse", stock.warehouse.pk)
    variables = {
        "id": stock_id,
        "input": {
            "productVariant": variant_id,
            "warehouse": warehouse_id,
            "quantity": 90,
        },
    }
    response = staff_api_client.post_graphql(MUTATION_UPDATE_STOCK, variables=variables)
    assert_no_permission(response)


def test_update_stock_mutation(staff_api_client, permission_manage_stocks, stock):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", stock.product_variant.pk)
    warehouse_id = graphene.Node.to_global_id("Warehouse", stock.warehouse.pk)
    old_stock_quantity = stock.quantity

    variables = {
        "id": stock_id,
        "input": {
            "productVariant": variant_id,
            "warehouse": warehouse_id,
            "quantity": old_stock_quantity + 12,
        },
    }
    response = staff_api_client.post_graphql(MUTATION_UPDATE_STOCK, variables=variables)
    content = get_graphql_content(response)
    content_errors = content["data"]["updateStock"]["errors"]
    assert len(content_errors) == 0
    stock.refresh_from_db()
    assert stock.quantity == old_stock_quantity + 12


def test_delete_stock_requires_permission(staff_api_client, stock):
    assert not staff_api_client.user.has_perm("stock.manage_stocks")
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)
    variables = {"id": stock_id}
    response = staff_api_client.post_graphql(MUTATION_DELETE_STOCK, variables=variables)
    assert_no_permission(response)


def test_delete_stock_mutation(staff_api_client, permission_manage_stocks, stock):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
    stock_pk = stock.pk
    stock_id = graphene.Node.to_global_id("Stock", stock_pk)
    initial_stock_count = Stock.objects.count()
    variables = {"id": stock_id}
    response = staff_api_client.post_graphql(MUTATION_DELETE_STOCK, variables=variables)
    assert Stock.objects.count() == initial_stock_count - 1
    content = get_graphql_content(response)
    content_errors = content["data"]["deleteStock"]["errors"]
    assert len(content_errors) == 0


def test_bulk_delete_stock_requires_permission(staff_api_client):
    assert not staff_api_client.user.has_perm("stock.manage_stocks")
    variables = {
        "ids": [
            graphene.Node.to_global_id("Stock", stock.pk)
            for stock in Stock.objects.all()
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_BULK_DELETE_STOCK, variables=variables
    )
    assert_no_permission(response)


def test_bulk_delete_bulk_stock_mutation(staff_api_client, permission_manage_stocks):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
    initial_stock_count = Stock.objects.count()
    variables = {
        "ids": [
            graphene.Node.to_global_id("Stock", stock.pk)
            for stock in Stock.objects.all()
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_BULK_DELETE_STOCK, variables=variables
    )
    content = get_graphql_content(response)
    content_errors = content["data"]["bulkDeleteStock"]["errors"]
    assert len(content_errors) == 0
    content_count = content["data"]["bulkDeleteStock"]["count"]
    assert content_count == initial_stock_count
    assert not Stock.objects.all().exists()


def test_query_stock_requires_permission(staff_api_client, stock):
    assert not staff_api_client.user.has_perm("stock.manage_stocks")
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)
    response = staff_api_client.post_graphql(QUERY_STOCK, variables={"id": stock_id})
    assert_no_permission(response)


def test_query_stock(staff_api_client, stock, permission_manage_stocks):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
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
    assert content_stock["quantityAllocated"] == stock.quantity_allocated


def test_query_stocks_requires_permissions(staff_api_client):
    assert not staff_api_client.user.has_perm("stock.manage_stocks")
    response = staff_api_client.post_graphql(QUERY_STOCKS)
    assert_no_permission(response)


def test_query_stocks(staff_api_client, stock, permission_manage_stocks):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
    response = staff_api_client.post_graphql(QUERY_STOCKS)
    content = get_graphql_content(response)
    total_count = content["data"]["stocks"]["totalCount"]
    assert total_count == Stock.objects.count()


def test_query_stocks_with_filters_quantity(
    staff_api_client, stock, permission_manage_stocks
):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
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


def test_query_stocks_with_filters_quantity_allocated(
    staff_api_client, stock, permission_manage_stocks
):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
    quantities = Stock.objects.all().values_list("quantity_allocated", flat=True)
    sum_quantities = sum(quantities)
    variables = {"filter": {"quantityAllocated": sum_quantities}}
    response = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS, variables=variables
    )
    content = get_graphql_content(response)
    total_count = content["data"]["stocks"]["totalCount"]
    assert total_count == 0

    variables = {"filter": {"quantityAllocated": max(quantities)}}
    response = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS, variables=variables
    )
    content = get_graphql_content(response)
    total_count = content["data"]["stocks"]["totalCount"]
    assert (
        total_count == Stock.objects.filter(quantity_allocated=max(quantities)).count()
    )


def test_query_stocks_with_filters_warehouse(
    staff_api_client, stock, permission_manage_stocks
):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
    warehouse = stock.warehouse
    response_name = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS, variables={"filter": {"warehouse": warehouse.name}}
    )
    content = get_graphql_content(response_name)
    total_count = content["data"]["stocks"]["totalCount"]
    assert total_count == Stock.objects.filter(warehouse=warehouse).count()


def test_query_stocks_with_filters_product_variant(
    staff_api_client, stock, permission_manage_stocks
):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
    product_variant = stock.product_variant
    response_name = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS,
        variables={"filter": {"productVariant": product_variant.name}},
    )
    content = get_graphql_content(response_name)
    total_count = content["data"]["stocks"]["totalCount"]
    assert (
        total_count
        == Stock.objects.filter(product_variant__name=product_variant.name).count()
    )


def test_query_stocks_with_filters_product_variant__product(
    staff_api_client, stock, permission_manage_stocks
):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
    product = stock.product_variant.product
    response_name = staff_api_client.post_graphql(
        QUERY_STOCKS_WITH_FILTERS,
        variables={"filter": {"productVariant": product.name}},
    )
    content = get_graphql_content(response_name)
    total_count = content["data"]["stocks"]["totalCount"]
    assert (
        total_count
        == Stock.objects.filter(product_variant__product__name=product.name).count()
    )


def test_query_available_stock_quantity(
    staff_api_client, permission_manage_stocks, stock, settings
):
    staff_api_client.user.user_permissions.add(permission_manage_stocks)
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)

    available_quantity = stock.quantity - stock.quantity_allocated
    # set MAX_CHECKOUT_LINE_QUANTITY smaller than available quantity
    settings.MAX_CHECKOUT_LINE_QUANTITY = available_quantity - 1

    response = staff_api_client.post_graphql(QUERY_STOCK, variables={"id": stock_id})
    content = get_graphql_content(response)
    content_quantity_available = content["data"]["stock"]["available"]
    assert content_quantity_available == settings.MAX_CHECKOUT_LINE_QUANTITY

    # set MAX_CHECKOUT_LINE_QUANTITY larger than available quantity
    settings.MAX_CHECKOUT_LINE_QUANTITY = available_quantity + 1

    response = staff_api_client.post_graphql(QUERY_STOCK, variables={"id": stock_id})
    content = get_graphql_content(response)
    content_quantity_available = content["data"]["stock"]["available"]
    assert content_quantity_available == available_quantity
