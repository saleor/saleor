from unittest.mock import patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.db.models import Sum

from .....plugins.manager import get_plugins_manager
from .....tests.utils import flush_post_commit_hooks
from .....warehouse.error_codes import StockErrorCode
from .....warehouse.models import Stock, Warehouse
from ....tests.utils import get_graphql_content
from ...bulk_mutations.products import ProductVariantStocksUpdate
from ...utils import create_stocks

VARIANT_STOCKS_UPDATE_MUTATIONS = """
    mutation ProductVariantStocksUpdate($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksUpdate(variantId: $variantId, stocks: $stocks){
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


def test_product_variant_stocks_update(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

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
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksUpdate"]

    expected_result = [
        {
            "quantity": stocks[0]["quantity"],
            "quantityAllocated": 0,
            "warehouse": {"slug": warehouse.slug},
        },
        {
            "quantity": stocks[1]["quantity"],
            "quantityAllocated": 0,
            "warehouse": {"slug": second_warehouse.slug},
        },
    ]
    assert not data["errors"]
    assert len(data["productVariant"]["stocks"]) == len(stocks)
    result = []
    for stock in data["productVariant"]["stocks"]:
        stock.pop("id")
        result.append(stock)
    for res in result:
        assert res in expected_result


def test_product_variant_stocks_update_with_empty_stock_list(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = []
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksUpdate"]

    assert not data["errors"]
    assert len(data["productVariant"]["stocks"]) == len(stocks)


def test_variant_stocks_update_stock_duplicated_warehouse(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.pk),
            "quantity": 100,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 150,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksUpdate"]
    errors = data["errors"]

    assert errors
    assert errors[0]["code"] == StockErrorCode.UNIQUE.name
    assert errors[0]["field"] == "warehouse"
    assert errors[0]["index"] == 2


def test_product_variant_stocks_update_too_big_quantity_value(
    staff_api_client, variant, warehouse, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    quantity = 99999999999
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.id),
            "quantity": 99999999999,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(VARIANT_STOCKS_UPDATE_MUTATIONS, variables)
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == f"Int cannot represent non 32-bit signed integer value: {quantity}"
    )


def test_create_stocks(variant, warehouse):
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    assert variant.stocks.count() == 0

    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
        {"quantity": 10, "warehouse": "321"},
    ]
    warehouses = [warehouse, second_warehouse]
    create_stocks(variant, stocks_data, warehouses)

    assert variant.stocks.count() == len(stocks_data)
    assert {stock.warehouse.pk for stock in variant.stocks.all()} == {
        warehouse.pk for warehouse in warehouses
    }
    assert {stock.quantity for stock in variant.stocks.all()} == {
        data["quantity"] for data in stocks_data
    }


def test_create_stocks_failed(product_with_single_variant, warehouse):
    variant = product_with_single_variant.variants.first()

    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
        {"quantity": 10, "warehouse": "321"},
    ]
    warehouses = [warehouse, second_warehouse]
    with pytest.raises(ValidationError):
        create_stocks(variant, stocks_data, warehouses)


def test_update_or_create_variant_stocks(variant, warehouses):
    Stock.objects.create(
        product_variant=variant,
        warehouse=warehouses[0],
        quantity=5,
    )
    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
        {"quantity": 10, "warehouse": "321"},
    ]

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, stocks_data, warehouses, get_plugins_manager()
    )

    variant.refresh_from_db()
    assert variant.stocks.count() == 2
    assert {stock.warehouse.pk for stock in variant.stocks.all()} == {
        warehouse.pk for warehouse in warehouses
    }
    assert {stock.quantity for stock in variant.stocks.all()} == {
        data["quantity"] for data in stocks_data
    }


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_update_or_create_variant_stocks_when_stock_out_of_quantity(
    back_in_stock_webhook_trigger, variant, warehouses
):
    stock = Stock.objects.create(
        product_variant=variant,
        warehouse=warehouses[0],
        quantity=-5,
    )
    stocks_data = [{"quantity": 10, "warehouse": "321"}]

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, stocks_data, warehouses, get_plugins_manager()
    )

    variant.refresh_from_db()
    flush_post_commit_hooks()
    assert variant.stocks.count() == 1
    assert {stock.quantity for stock in variant.stocks.all()} == {
        data["quantity"] for data in stocks_data
    }
    back_in_stock_webhook_trigger.assert_called_once_with(stock)
    assert variant.stocks.all()[0].quantity == 10


def test_update_or_create_variant_stocks_empty_stocks_data(variant, warehouses):
    Stock.objects.create(
        product_variant=variant,
        warehouse=warehouses[0],
        quantity=5,
    )

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, [], warehouses, get_plugins_manager()
    )

    variant.refresh_from_db()
    assert variant.stocks.count() == 1
    stock = variant.stocks.first()
    assert stock.warehouse == warehouses[0]
    assert stock.quantity == 5


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_update_or_create_variant_with_back_in_stock_webhooks_only_success(
    product_variant_stock_out_of_stock_webhook,
    product_variant_back_in_stock_webhook,
    settings,
    variant,
    warehouses,
):

    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse)
            for warehouse in warehouses
        ]
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    plugins = get_plugins_manager()
    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
    ]
    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 0

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, stocks_data, warehouses, plugins
    )

    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 10

    flush_post_commit_hooks()
    product_variant_back_in_stock_webhook.assert_called_once_with(
        Stock.objects.all()[1]
    )
    product_variant_stock_out_of_stock_webhook.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_update_or_create_variant_with_back_in_stock_webhooks_only_failed(
    product_variant_stock_out_of_stock_webhook,
    product_variant_back_in_stock_webhook,
    settings,
    variant,
    warehouses,
):

    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse)
            for warehouse in warehouses
        ]
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    plugins = get_plugins_manager()
    stocks_data = [
        {"quantity": 0, "warehouse": "123"},
    ]
    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 0

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, stocks_data, warehouses, plugins
    )

    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 0

    flush_post_commit_hooks()
    product_variant_back_in_stock_webhook.assert_not_called()
    product_variant_stock_out_of_stock_webhook.assert_called_once_with(
        Stock.objects.all()[1]
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_update_or_create_variant_stocks_with_out_of_stock_webhook_only(
    product_variant_stock_out_of_stock_webhook,
    product_variant_back_in_stock_webhook,
    settings,
    variant,
    warehouses,
):

    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=5)
            for warehouse in warehouses
        ]
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    plugins = get_plugins_manager()

    stocks_data = [
        {"quantity": 0, "warehouse": "123"},
        {"quantity": 2, "warehouse": "321"},
    ]

    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 10

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, stocks_data, warehouses, plugins
    )

    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 2

    flush_post_commit_hooks()

    product_variant_stock_out_of_stock_webhook.assert_called_once_with(
        Stock.objects.last()
    )
    product_variant_back_in_stock_webhook.assert_not_called()


VARIANT_UPDATE_AND_STOCKS_UPDATE_MUTATION = """
  fragment ProductVariant on ProductVariant {
    id
    name
    stocks {
      quantity
      warehouse {
        id
        name
      }
    }
  }

  mutation VariantUpdate($id: ID!, $stocks: [StockInput!]!) {
    productVariantUpdate(id: $id, input: {}) {
      productVariant {
        ...ProductVariant
      }
    }
    productVariantStocksUpdate(variantId: $id, stocks: $stocks) {
      productVariant {
        ...ProductVariant
      }
    }
  }
"""


def test_invalidate_stocks_dataloader_on_update_stocks(
    staff_api_client, variant_with_many_stocks, permission_manage_products
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stock = variant.stocks.first()
    # keep only one stock record for test purposes
    variant.stocks.exclude(id=stock.id).delete()
    warehouse_id = graphene.Node.to_global_id("Warehouse", stock.warehouse.id)
    old_quantity = stock.quantity
    new_quantity = old_quantity + 500
    variables = {
        "id": variant_id,
        "stocks": [{"warehouse": warehouse_id, "quantity": new_quantity}],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_UPDATE_AND_STOCKS_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    variant_data = content["data"]["productVariantUpdate"]["productVariant"]
    update_stocks_data = content["data"]["productVariantStocksUpdate"]["productVariant"]

    # stocks is not updated in the first mutation
    assert variant_data["stocks"][0]["quantity"] == old_quantity

    # stock is updated in the second mutation
    assert update_stocks_data["stocks"][0]["quantity"] == new_quantity
