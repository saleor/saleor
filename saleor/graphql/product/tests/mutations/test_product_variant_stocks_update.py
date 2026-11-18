from unittest.mock import ANY, patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.db.models import Sum

from .....product.error_codes import ProductErrorCode
from .....warehouse.error_codes import StockErrorCode
from .....warehouse.models import Stock, Warehouse
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...bulk_mutations import ProductVariantStocksUpdate
from ...utils import create_stocks

VARIANT_STOCKS_UPDATE_MUTATIONS = """
    mutation ProductVariantStocksUpdate($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksUpdate(variantId: $variantId, stocks: $stocks){
            productVariant {
                quantityAvailable
                stocks {
                    quantity
                    quantityAllocated
                    id
                    warehouse {
                        slug
                    }
                }
            }
            errors {
                code
                field
                message
                index
            }
        }
    }
"""


def test_product_variant_stocks_update(
    staff_api_client,
    preorder_variant_global_threshold,
    warehouse,
    permission_manage_products,
):
    variant = preorder_variant_global_threshold
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


def test_update_or_create_variant_stocks(variant, warehouses, site_settings):
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
        variant,
        stocks_data,
        warehouses,
        site_settings,
        None,
    )

    variant.refresh_from_db()
    assert variant.stocks.count() == 2
    assert {stock.warehouse.pk for stock in variant.stocks.all()} == {
        warehouse.pk for warehouse in warehouses
    }
    assert {stock.quantity for stock in variant.stocks.all()} == {
        data["quantity"] for data in stocks_data
    }


@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.get_webhooks_for_event"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_stocks_updated"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_back_in_stock"
)
def test_update_or_create_variant_stocks_when_stock_out_of_quantity(
    back_in_stock_webhook_trigger,
    stocks_updated_webhook_trigger,
    mocked_get_webhooks_for_event,
    variant,
    warehouses,
    any_webhook,
    settings,
    site_settings,
    django_capture_on_commit_callbacks,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    stock = Stock.objects.create(
        product_variant=variant,
        warehouse=warehouses[0],
        quantity=-5,
    )
    stocks_data = [{"quantity": 10, "warehouse": "321"}]

    with django_capture_on_commit_callbacks(execute=True):
        ProductVariantStocksUpdate.update_or_create_variant_stocks(
            variant,
            stocks_data,
            warehouses,
            site_settings,
            None,
        )

    variant.refresh_from_db()
    assert variant.stocks.count() == 1
    assert {stock.quantity for stock in variant.stocks.all()} == {
        data["quantity"] for data in stocks_data
    }
    back_in_stock_webhook_trigger.assert_called_once_with(
        stock, webhooks=[any_webhook], requestor=ANY
    )
    stocks_updated_webhook_trigger.assert_called_once_with(
        [stock], webhooks=[any_webhook], requestor=ANY
    )
    assert variant.stocks.all()[0].quantity == 10


def test_update_or_create_variant_stocks_empty_stocks_data(
    variant, warehouses, site_settings
):
    Stock.objects.create(
        product_variant=variant,
        warehouse=warehouses[0],
        quantity=5,
    )

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, [], warehouses, site_settings, None
    )

    variant.refresh_from_db()
    assert variant.stocks.count() == 1
    stock = variant.stocks.first()
    assert stock.warehouse == warehouses[0]
    assert stock.quantity == 5


@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.get_webhooks_for_event"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_stocks_updated"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_back_in_stock"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_out_of_stock"
)
def test_update_or_create_variant_with_back_in_stock_webhooks_only_success(
    product_variant_stock_out_of_stock_webhook,
    product_variant_back_in_stock_webhook,
    product_variant_stocks_updated_webhook,
    mocked_get_webhooks_for_event,
    settings,
    site_settings,
    variant,
    warehouses,
    any_webhook,
    django_capture_on_commit_callbacks,
):
    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse)
            for warehouse in warehouses
        ]
    )
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
    ]
    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 0

    with django_capture_on_commit_callbacks(execute=True):
        ProductVariantStocksUpdate.update_or_create_variant_stocks(
            variant, stocks_data, warehouses, site_settings, None
        )

    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 10

    stock = Stock.objects.all()[1]
    product_variant_back_in_stock_webhook.assert_called_once_with(
        stock, webhooks=[any_webhook], requestor=ANY
    )
    product_variant_stocks_updated_webhook.assert_called_once_with(
        [stock], webhooks=[any_webhook], requestor=ANY
    )
    product_variant_stock_out_of_stock_webhook.assert_not_called()


@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.get_webhooks_for_event"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_stocks_updated"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_back_in_stock"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_out_of_stock"
)
def test_update_or_create_variant_with_back_in_stock_webhooks_only_failed(
    product_variant_stock_out_of_stock_webhook,
    product_variant_back_in_stock_webhook,
    product_variant_stocks_update_webhook,
    mocked_get_webhooks_for_event,
    settings,
    site_settings,
    variant,
    warehouses,
    any_webhook,
    django_capture_on_commit_callbacks,
):
    # given — stocks currently have availability, update drops both to 0
    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=5)
            for warehouse in warehouses
        ]
    )

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    stocks_data = [
        {"quantity": 0, "warehouse": "123"},
    ]
    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 10

    # when
    with django_capture_on_commit_callbacks(execute=True):
        ProductVariantStocksUpdate.update_or_create_variant_stocks(
            variant, stocks_data, warehouses, site_settings, None
        )

    # then — updated stock transitioned from available (5) to out of stock (0)
    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 5

    stock = Stock.objects.all()[1]
    product_variant_back_in_stock_webhook.assert_not_called()
    product_variant_stock_out_of_stock_webhook.assert_called_once_with(
        stock, webhooks=[any_webhook], requestor=ANY
    )
    assert product_variant_stocks_update_webhook.call_count == 1
    product_variant_stocks_update_webhook.assert_called_with(
        [stock], webhooks=[any_webhook], requestor=ANY
    )


@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.get_webhooks_for_event"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_stocks_updated"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_back_in_stock"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_out_of_stock"
)
def test_update_or_create_variant_with_back_in_stock_webhooks_with_allocations(
    product_variant_stock_out_of_stock_webhook,
    product_variant_back_in_stock_webhook,
    product_variant_stocks_updated_webhook,
    mocked_get_webhooks_for_event,
    settings,
    site_settings,
    variant,
    warehouse,
    any_webhook,
    django_capture_on_commit_callbacks,
):
    stock_quantity = 4
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=stock_quantity
    )

    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    stock.quantity_allocated = stock_quantity
    stock.save(update_fields=["quantity_allocated"])
    stocks_data = [
        {"quantity": stock.quantity_allocated + 1},
    ]

    # when
    with django_capture_on_commit_callbacks(execute=True):
        ProductVariantStocksUpdate.update_or_create_variant_stocks(
            variant, stocks_data, [warehouse], site_settings, None
        )
    # then
    product_variant_back_in_stock_webhook.assert_called_once_with(
        stock, webhooks=[any_webhook], requestor=ANY
    )
    product_variant_stocks_updated_webhook.assert_called_once_with(
        [stock], webhooks=[any_webhook], requestor=ANY
    )
    product_variant_stock_out_of_stock_webhook.assert_not_called()


@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.get_webhooks_for_event"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_stocks_updated"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_back_in_stock"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_out_of_stock"
)
def test_update_or_create_variant_with_out_of_stock_webhooks_with_allocations(
    product_variant_stock_out_of_stock_webhook,
    product_variant_back_in_stock_webhook,
    product_variant_stocks_updated_webhook,
    mocked_get_webhooks_for_event,
    settings,
    site_settings,
    variant,
    warehouse,
    any_webhook,
    django_capture_on_commit_callbacks,
):
    stock_quantity = 4
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=stock_quantity
    )

    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    stock.quantity_allocated = stock_quantity - 1
    stock.save(update_fields=["quantity_allocated"])
    stocks_data = [
        {"quantity": stock.quantity_allocated},
    ]

    # when
    with django_capture_on_commit_callbacks(execute=True):
        ProductVariantStocksUpdate.update_or_create_variant_stocks(
            variant, stocks_data, [warehouse], site_settings, None
        )
    # then
    product_variant_stock_out_of_stock_webhook.assert_called_once_with(
        stock, webhooks=[any_webhook], requestor=ANY
    )
    product_variant_stocks_updated_webhook.assert_called_once_with(
        [stock], webhooks=[any_webhook], requestor=ANY
    )
    product_variant_back_in_stock_webhook.assert_not_called()


@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.get_webhooks_for_event"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_stocks_updated"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_back_in_stock"
)
@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_stocks_update.trigger_product_variant_out_of_stock"
)
def test_update_or_create_variant_stocks_with_out_of_stock_webhook_only(
    product_variant_stock_out_of_stock_webhook,
    product_variant_back_in_stock_webhook,
    product_variant_stocks_update_webhook,
    mocked_get_webhooks_for_event,
    settings,
    site_settings,
    variant,
    warehouses,
    any_webhook,
    django_capture_on_commit_callbacks,
):
    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=5)
            for warehouse in warehouses
        ]
    )

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    stocks_data = [
        {"quantity": 0, "warehouse": "123"},
        {"quantity": 2, "warehouse": "321"},
    ]

    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 10
    with django_capture_on_commit_callbacks(execute=True):
        ProductVariantStocksUpdate.update_or_create_variant_stocks(
            variant, stocks_data, warehouses, site_settings, None
        )

    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 2
    assert product_variant_stock_out_of_stock_webhook.call_count == 1

    assert product_variant_stocks_update_webhook.call_count == 1
    product_variant_stocks_update_webhook.assert_called_once_with(
        list(variant.stocks.all()), webhooks=[any_webhook], requestor=ANY
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


@patch(
    "saleor.graphql.product.bulk_mutations.product_variant_stocks_update"
    ".trigger_back_in_stock_in_channel_events_for_stocks"
)
def test_update_stocks_triggers_back_in_stock_channel_events(
    mocked_trigger,
    staff_api_client,
    variant,
    warehouses,
    site_settings,
    permission_manage_products,
):
    # given - two stocks at 0; update sets both positive
    site_settings.use_legacy_shipping_zone_stock_availability = False
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    stocks = Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouses[0], quantity=0),
            Stock(product_variant=variant, warehouse=warehouses[1], quantity=0),
        ]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "variantId": variant_id,
        "stocks": [
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouses[0].pk),
                "quantity": 10,
            },
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouses[1].pk),
                "quantity": 5,
            },
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then
    mocked_trigger.assert_called_once()
    triggered_stocks, triggered_site_settings = mocked_trigger.call_args.args
    assert {stock.pk for stock in triggered_stocks} == {stock.pk for stock in stocks}
    assert triggered_site_settings == site_settings


@patch(
    "saleor.graphql.product.bulk_mutations.product_variant_stocks_update"
    ".trigger_out_of_stock_in_channel_events_for_stocks"
)
def test_update_stocks_triggers_out_of_stock_channel_events(
    mocked_trigger,
    staff_api_client,
    variant,
    warehouses,
    site_settings,
    permission_manage_products,
):
    # given - two stocks with availability; update sets both to 0
    site_settings.use_legacy_shipping_zone_stock_availability = False
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    stocks = Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouses[0], quantity=10),
            Stock(product_variant=variant, warehouse=warehouses[1], quantity=5),
        ]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "variantId": variant_id,
        "stocks": [
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouses[0].pk),
                "quantity": 0,
            },
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouses[1].pk),
                "quantity": 0,
            },
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then
    mocked_trigger.assert_called_once()
    triggered_stocks, triggered_site_settings = mocked_trigger.call_args.args
    assert {stock.pk for stock in triggered_stocks} == {stock.pk for stock in stocks}
    assert triggered_site_settings == site_settings


@patch(
    "saleor.graphql.product.bulk_mutations.product_variant_stocks_update"
    ".trigger_out_of_stock_in_channel_events_for_stocks"
)
@patch(
    "saleor.graphql.product.bulk_mutations.product_variant_stocks_update"
    ".trigger_back_in_stock_in_channel_events_for_stocks"
)
def test_update_stocks_skips_channel_events_when_legacy_flag_enabled(
    mocked_back,
    mocked_out,
    staff_api_client,
    variant,
    warehouses,
    site_settings,
    permission_manage_products,
):
    # given - legacy flag is on; two stocks at 0 updated to positive
    site_settings.use_legacy_shipping_zone_stock_availability = True
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouses[0], quantity=0),
            Stock(product_variant=variant, warehouse=warehouses[1], quantity=0),
        ]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "variantId": variant_id,
        "stocks": [
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouses[0].pk),
                "quantity": 10,
            },
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouses[1].pk),
                "quantity": 5,
            },
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then
    mocked_back.assert_not_called()
    mocked_out.assert_not_called()


@patch(
    "saleor.graphql.product.bulk_mutations.product_variant_stocks_update"
    ".trigger_out_of_stock_in_channel_events_for_stocks"
)
@patch(
    "saleor.graphql.product.bulk_mutations.product_variant_stocks_update"
    ".trigger_back_in_stock_in_channel_events_for_stocks"
)
def test_update_stocks_does_not_trigger_channel_events_when_quantity_remains(
    mocked_back,
    mocked_out,
    staff_api_client,
    variant,
    warehouses,
    site_settings,
    permission_manage_products,
):
    # given - two stocks with availability; update reduces but keeps positive
    site_settings.use_legacy_shipping_zone_stock_availability = False
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouses[0], quantity=10),
            Stock(product_variant=variant, warehouse=warehouses[1], quantity=8),
        ]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "variantId": variant_id,
        "stocks": [
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouses[0].pk),
                "quantity": 5,
            },
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouses[1].pk),
                "quantity": 3,
            },
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then
    mocked_back.assert_not_called()
    mocked_out.assert_not_called()


VARIANT_STOCKS_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation ProductVariantStocksUpdate(
        $variantId: ID,
        $sku: String,
        $variantExternalReference: String,
        $stocks: [StockInput!]!
    ){
        productVariantStocksUpdate(
            variantId: $variantId,
            sku: $sku,
            variantExternalReference: $variantExternalReference,
            stocks: $stocks
        ){
            productVariant {
                id
                stocks {
                    quantity
                    warehouse {
                        slug
                    }
                }
            }
            errors {
                code
                field
                message
            }
        }
    }
"""


def test_by_external_reference(
    staff_api_client, variant, warehouse, permission_manage_products, mocker
):
    # given
    external_reference = "variant-ext-ref"
    variant.external_reference = external_reference
    variant.save(update_fields=["external_reference"])
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=10
    )
    stocks_updated = mocker.patch(
        "saleor.graphql.product.bulk_mutations.product_variant_stocks_update"
        ".trigger_product_variant_stocks_updated"
    )
    quantity = 20
    variables = {
        "variantExternalReference": external_reference,
        "stocks": [
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
                "quantity": quantity,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVariantStocksUpdate"]
    assert data["errors"] == []
    assert data["productVariant"] == {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "stocks": [{"quantity": quantity, "warehouse": {"slug": warehouse.slug}}],
    }
    stock.refresh_from_db(fields=("quantity",))
    assert stock.quantity == quantity
    stocks_updated.assert_called_once()


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'variantId', 'sku', "
            "'variantExternalReference'.",
        ),
        (
            "null",
            {"variantId": None, "sku": None, "variantExternalReference": None},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'variantId', 'sku', "
            "'variantExternalReference'.",
        ),
        (
            "empty",
            {"variantExternalReference": ""},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'variantId', 'sku', "
            "'variantExternalReference'.",
        ),
        (
            "both",
            {"variantExternalReference": "existing-reference"},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "Argument 'variantId' cannot be combined with 'variantExternalReference'",
        ),
        (
            "sku_and_external_reference",
            {"variantExternalReference": "existing-reference"},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "Argument 'sku' cannot be combined with 'variantExternalReference'",
        ),
        (
            "not_found",
            {"variantExternalReference": "missing-reference"},
            "variantExternalReference",
            ProductErrorCode.NOT_FOUND,
            "Couldn't resolve to a node: missing-reference",
        ),
    ],
)
def test_external_reference_invalid_identifiers(
    _case,
    identifiers,
    error_field,
    error_code,
    message,
    staff_api_client,
    variant,
    warehouse,
    permission_manage_products,
    mocker,
):
    # given
    variant.external_reference = "existing-reference"
    variant.save(update_fields=["external_reference"])
    original_quantity = 10
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=original_quantity
    )
    stocks_updated = mocker.patch(
        "saleor.graphql.product.bulk_mutations.product_variant_stocks_update"
        ".trigger_product_variant_stocks_updated"
    )
    variables = dict(identifiers)
    if _case == "both":
        variables["variantId"] = graphene.Node.to_global_id(
            "ProductVariant", variant.pk
        )
    elif _case == "sku_and_external_reference":
        variables["sku"] = variant.sku
    variables["stocks"] = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    data = get_graphql_content(response)["data"]["productVariantStocksUpdate"]
    assert data["productVariant"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    stock.refresh_from_db(fields=("quantity",))
    assert stock.quantity == original_quantity
    stocks_updated.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "client_fixture", "is_allowed"),
    [
        ("anonymous", "api_client", False),
        ("customer", "user_api_client", False),
        ("staff_without_permission", "staff_api_client", False),
        ("staff_with_permission", "staff_api_client", True),
        ("app_without_permission", "app_api_client", False),
        ("app_with_permission", "app_api_client", True),
    ],
)
def test_external_reference_authorization(
    _case,
    client_fixture,
    is_allowed,
    request,
    variant,
    warehouse,
    permission_manage_products,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    external_reference = "existing-reference"
    variant.external_reference = external_reference
    variant.save(update_fields=["external_reference"])
    original_quantity = 10
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=original_quantity
    )
    stocks_updated = mocker.patch(
        "saleor.graphql.product.bulk_mutations.product_variant_stocks_update"
        ".trigger_product_variant_stocks_updated"
    )
    quantity = 20
    variables = {
        "variantExternalReference": external_reference,
        "stocks": [
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
                "quantity": quantity,
            }
        ],
    }

    # when
    response = client.post_graphql(
        VARIANT_STOCKS_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    stock.refresh_from_db(fields=("quantity",))
    if is_allowed:
        data = get_graphql_content(response)["data"]["productVariantStocksUpdate"]
        assert data["errors"] == []
        assert data["productVariant"]["id"] == graphene.Node.to_global_id(
            "ProductVariant", variant.pk
        )
        assert stock.quantity == quantity
        stocks_updated.assert_called_once()
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"productVariantStocksUpdate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["productVariantStocksUpdate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_PRODUCTS"
        )
        assert stock.quantity == original_quantity
        stocks_updated.assert_not_called()
