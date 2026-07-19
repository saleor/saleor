from unittest import mock

import graphene

from .....product.error_codes import ProductErrorCode
from .....warehouse import WarehouseClickAndCollectOption
from .....warehouse.models import Stock, Warehouse
from ....tests.utils import get_graphql_content

VARIANT_STOCKS_DELETE_MUTATION = """
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
            errors{
                field
                code
                message
            }
        }
    }
"""


def test_product_variant_stocks_delete_mutation(
    staff_api_client, variant, warehouse, permission_manage_products
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
    stocks_count = variant.stocks.count()

    warehouse_ids = [graphene.Node.to_global_id("Warehouse", second_warehouse.id)]

    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    variant.refresh_from_db()
    assert not data["errors"]
    assert (
        len(data["productVariant"]["stocks"])
        == variant.stocks.count()
        == stocks_count - 1
    )
    assert data["productVariant"]["stocks"][0]["quantity"] == 10
    assert data["productVariant"]["stocks"][0]["warehouse"]["slug"] == warehouse.slug


def test_product_variant_stocks_delete_mutation_invalid_warehouse_id(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.bulk_create(
        [Stock(product_variant=variant, warehouse=warehouse, quantity=10)]
    )
    stocks_count = variant.stocks.count()

    warehouse_ids = [graphene.Node.to_global_id("Warehouse", second_warehouse.id)]

    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    variant.refresh_from_db()
    assert not data["errors"]
    assert (
        len(data["productVariant"]["stocks"]) == variant.stocks.count() == stocks_count
    )
    assert data["productVariant"]["stocks"][0]["quantity"] == 10
    assert data["productVariant"]["stocks"][0]["warehouse"]["slug"] == warehouse.slug


def test_product_variant_stocks_delete_mutation_invalid_object_type_of_warehouse_id(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    Stock.objects.bulk_create(
        [Stock(product_variant=variant, warehouse=warehouse, quantity=10)]
    )

    warehouse_ids = [graphene.Node.to_global_id("Product", warehouse.id)]

    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.GRAPHQL_ERROR.name
    assert errors[0]["field"] == "warehouseIds"


VARIANT_UPDATE_AND_STOCKS_REMOVE_MUTATION = """
  fragment ProductVariant on ProductVariant {
    stocks {
      id
    }
  }

  mutation VariantUpdate($removeStocks: [ID!]!, $id: ID!) {
    productVariantUpdate(id: $id, input: {}) {
      productVariant {
        ...ProductVariant
      }
    }
    productVariantStocksDelete(variantId: $id, warehouseIds: $removeStocks) {
      productVariant {
        ...ProductVariant
      }
    }
  }
"""


def test_invalidate_stocks_dataloader_on_removing_stocks(
    staff_api_client, variant_with_many_stocks, permission_manage_products
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", stock.warehouse.id)
        for stock in variant_with_many_stocks.stocks.all()
    ]
    variables = {
        "id": variant_id,
        "removeStocks": warehouse_ids,
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_UPDATE_AND_STOCKS_REMOVE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    variant_data = content["data"]["productVariantUpdate"]["productVariant"]
    remove_stocks_data = content["data"]["productVariantStocksDelete"]["productVariant"]

    # no stocks were removed in the first mutation
    assert len(variant_data["stocks"]) == len(warehouse_ids)

    # stocks are empty in the second mutation
    assert remove_stocks_data["stocks"] == []


@mock.patch(
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_out_of_stock_in_channel"
)
def test_delete_stocks_triggers_out_of_stock_in_channel_for_non_cc_warehouses(
    mocked_trigger,
    staff_api_client,
    variant_with_many_stocks,
    channel_USD,
    site_settings,
    permission_manage_products,
):
    # given - `variant_with_many_stocks` has stocks in non-C&C warehouses
    site_settings.use_legacy_shipping_zone_stock_availability = False
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = list(variant.stocks.all())
    for stock in stocks:
        stock.warehouse.channels.add(channel_USD)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", stock.warehouse_id) for stock in stocks
    ]
    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables=variables,
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then - fires once per (variant, channel), dedup across warehouses
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].variant_id == variant.id
    assert stock_infos[0].channel_slug == channel_USD.slug


@mock.patch(
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_out_of_stock_for_click_and_collect"
)
def test_delete_stocks_triggers_out_of_stock_for_click_and_collect(
    mocked_trigger,
    staff_api_client,
    variant,
    channel_USD,
    address,
    site_settings,
    permission_manage_products,
):
    # given - two C&C warehouses with stocks
    site_settings.use_legacy_shipping_zone_stock_availability = False
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    cc_warehouses = Warehouse.objects.bulk_create(
        [
            Warehouse(
                address=address.get_copy(),
                name="cc-1",
                slug="cc-1",
                click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
            ),
            Warehouse(
                address=address.get_copy(),
                name="cc-2",
                slug="cc-2",
                click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
            ),
        ]
    )
    for warehouse in cc_warehouses:
        warehouse.channels.add(channel_USD)
    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=cc_warehouses[0], quantity=10),
            Stock(product_variant=variant, warehouse=cc_warehouses[1], quantity=5),
        ]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", warehouse.pk)
        for warehouse in cc_warehouses
    ]
    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables=variables,
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].variant_id == variant.id
    assert stock_infos[0].channel_slug == channel_USD.slug


@mock.patch(
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_out_of_stock_in_channel"
)
@mock.patch(
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_out_of_stock_for_click_and_collect"
)
def test_delete_stocks_skips_channel_events_when_legacy_flag_enabled(
    mocked_out_cc,
    mocked_out,
    staff_api_client,
    variant_with_many_stocks,
    site_settings,
    permission_manage_products,
):
    # given - legacy flag is on
    site_settings.use_legacy_shipping_zone_stock_availability = True
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = list(variant.stocks.all())
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", stock.warehouse_id) for stock in stocks
    ]
    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables=variables,
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then
    mocked_out.assert_not_called()
    mocked_out_cc.assert_not_called()
