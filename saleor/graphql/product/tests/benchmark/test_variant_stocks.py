from unittest.mock import patch

import graphene
import pytest

from .....warehouse.models import Stock, Warehouse
from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_product_variants_stocks_create(
    product_variant_back_in_stock_webhook_mock,
    staff_api_client,
    variant,
    warehouse,
    permission_manage_products,
    count_queries,
):
    query = """
    mutation ProductVariantStocksCreate($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksCreate(variantId: $variantId, stocks: $stocks){
            productVariant{
                stocks {
                    quantity
                    quantityAllocated
                    id
                    warehouse{
                        slug
                    }
                }
            }
            errors{
                code
                field
                message
                index
            }
        }
    }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    stocks_count = variant.stocks.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.id),
            "quantity": 100,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    assert not data["errors"]
    assert (
        len(data["productVariant"]["stocks"])
        == variant.stocks.count()
        == stocks_count + len(stocks)
    )
    assert product_variant_back_in_stock_webhook_mock.call_count == 2
    product_variant_back_in_stock_webhook_mock.assert_called_with(Stock.objects.last())


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_product_variants_stocks_create_with_single_webhook_called(
    product_variant_back_in_stock_webhook_mock,
    staff_api_client,
    variant,
    warehouse,
    permission_manage_products,
    count_queries,
):
    query = """
    mutation ProductVariantStocksCreate($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksCreate(variantId: $variantId, stocks: $stocks){
            productVariant{
                stocks {
                    quantity
                    quantityAllocated
                    id
                    warehouse{
                        slug
                    }
                }
            }
            errors{
                code
                field
                message
                index
            }
        }
    }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    stocks_count = variant.stocks.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    assert not data["errors"]
    assert (
        len(data["productVariant"]["stocks"])
        == variant.stocks.count()
        == stocks_count + len(stocks)
    )
    product_variant_back_in_stock_webhook_mock.assert_called_with(Stock.objects.last())


PRODUCT_VARIANT_STOCKS_UPDATE_MUTATION = """
mutation ProductVariantStocksUpdate(
    $variantId: ID, $sku: String, $stocks: [StockInput!]!){
        productVariantStocksUpdate(variantId: $variantId, sku: $sku, stocks: $stocks){
            productVariant{
                stocks{
                    quantity
                    quantityAllocated
                    id
                    warehouse{
                        slug
                    }
                }
            }
            errors{
                code
                field
                message
                index
            }
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_product_variants_stocks_update_byid(
    staff_api_client, variant, warehouse, permission_manage_products, count_queries
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    stocks_count = variant.stocks.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.id),
            "quantity": 100,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_STOCKS_UPDATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksUpdate"]

    assert not data["errors"]
    assert len(data["productVariant"]["stocks"]) == len(stocks)
    assert variant.stocks.count() == stocks_count + 1


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_product_variants_stocks_update_by_sku(
    staff_api_client, variant, warehouse, permission_manage_products, count_queries
):
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    stocks_count = variant.stocks.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.id),
            "quantity": 100,
        },
    ]
    variables = {"sku": variant.sku, "stocks": stocks}
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_STOCKS_UPDATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksUpdate"]

    assert not data["errors"]
    assert len(data["productVariant"]["stocks"]) == len(stocks)
    assert variant.stocks.count() == stocks_count + 1


PRODUCT_VARIANT_STOCKS_DELETE_MUTATION = """
    mutation ProductVariantStocksDelete(
        $variantId: ID, $sku: String, $warehouseIds: [ID!]!){
            productVariantStocksDelete(
                variantId: $variantId, sku: $sku, warehouseIds: $warehouseIds
            ){
                productVariant{
                    stocks{
                        id
                        quantity
                        warehouse{
                            slug
                        }
                    }
                }
                stockErrors{
                    field
                    code
                    message
                }
            }
        }
    """


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_product_variants_stocks_delete_by_id(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    variant,
    warehouse,
    permission_manage_products,
    count_queries,
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=10),
            Stock(product_variant=variant, warehouse=second_warehouse, quantity=140),
        ]
    )
    stock_to_delete = Stock.objects.last()
    stocks_count = variant.stocks.count()

    warehouse_ids = [graphene.Node.to_global_id("Warehouse", second_warehouse.id)]

    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_STOCKS_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    assert not data["stockErrors"]
    assert (
        len(data["productVariant"]["stocks"])
        == variant.stocks.count()
        == stocks_count - 1
    )
    assert stock_to_delete not in Stock.objects.all()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(stock_to_delete)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_product_variants_stocks_delete_by_sku(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    variant,
    warehouse,
    permission_manage_products,
    count_queries,
):
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=10),
            Stock(product_variant=variant, warehouse=second_warehouse, quantity=140),
        ]
    )
    stock_to_delete = Stock.objects.last()
    stocks_count = variant.stocks.count()

    warehouse_ids = [graphene.Node.to_global_id("Warehouse", second_warehouse.id)]

    variables = {"sku": variant.sku, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_STOCKS_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    assert not data["stockErrors"]
    assert (
        len(data["productVariant"]["stocks"])
        == variant.stocks.count()
        == stocks_count - 1
    )
    assert stock_to_delete not in Stock.objects.all()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(stock_to_delete)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_product_variants_stocks_delete_with_out_of_stock_webhook_many_calls(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    variant,
    warehouse,
    permission_manage_products,
    count_queries,
):
    query = """
    mutation ProductVariantStocksDelete($variantId: ID!, $warehouseIds: [ID!]!){
            productVariantStocksDelete(
                variantId: $variantId, warehouseIds: $warehouseIds
            ){
                productVariant{
                    stocks{
                        id
                        quantity
                        warehouse{
                            slug
                        }
                    }
                }
                stockErrors{
                    field
                    code
                    message
                }
            }
        }
    """

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()
    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=10),
            Stock(product_variant=variant, warehouse=second_warehouse, quantity=140),
        ]
    )

    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", warehouse_id)
        for warehouse_id in Warehouse.objects.values_list("id", flat=True)
    ]

    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    assert not data["stockErrors"]

    assert product_variant_out_of_stock_webhook_mock.call_count == 2


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_product_variants_stocks(
    staff_api_client, variant, warehouse, permission_manage_products, count_queries
):
    query = """
    query getStocks($id: ID!){
        productVariant(id: $id){
            id
            stocks{
                quantity
            }
        }
    }
    """

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=10),
            Stock(product_variant=variant, warehouse=second_warehouse, quantity=140),
        ]
    )

    variables = {"id": variant_id}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert len(data["stocks"]) == variant.stocks.count()
