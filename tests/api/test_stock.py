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
