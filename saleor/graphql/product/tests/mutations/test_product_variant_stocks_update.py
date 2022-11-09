from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db.models import Sum

from .....plugins.manager import get_plugins_manager
from .....tests.utils import flush_post_commit_hooks
from .....warehouse.models import Stock, Warehouse
from ...bulk_mutations.products import ProductVariantStocksUpdate
from ...utils import create_stocks


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
