from unittest import mock

import graphene
import pytest

from .....product.error_codes import ProductErrorCode
from .....warehouse import WarehouseClickAndCollectOption
from .....warehouse.error_codes import StockErrorCode
from .....warehouse.models import Stock, Warehouse
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

VARIANT_STOCKS_CREATE_MUTATION = """
    mutation ProductVariantStocksCreate($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksCreate(variantId: $variantId, stocks: $stocks){
            productVariant{
                id
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


def test_variant_stocks_create(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

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
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]

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


def test_variant_stocks_create_empty_stock_input(
    staff_api_client, variant, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {"variantId": variant_id, "stocks": []}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]

    assert not data["errors"]
    assert len(data["productVariant"]["stocks"]) == variant.stocks.count()
    assert data["productVariant"]["id"] == variant_id


def test_variant_stocks_create_stock_already_exists(
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
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    errors = data["errors"]

    assert errors
    assert errors[0]["code"] == StockErrorCode.UNIQUE.name
    assert errors[0]["field"] == "warehouse"
    assert errors[0]["index"] == 0


def test_variant_stocks_create_stock_duplicated_warehouse(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    second_warehouse_id = graphene.Node.to_global_id("Warehouse", second_warehouse.id)

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {"warehouse": second_warehouse_id, "quantity": 100},
        {"warehouse": second_warehouse_id, "quantity": 120},
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    errors = data["errors"]

    assert errors
    assert errors[0]["code"] == StockErrorCode.UNIQUE.name
    assert errors[0]["field"] == "warehouse"
    assert errors[0]["index"] == 2


def test_variant_stocks_create_stock_duplicated_warehouse_and_warehouse_already_exists(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    second_warehouse_id = graphene.Node.to_global_id("Warehouse", second_warehouse.id)
    Stock.objects.create(
        product_variant=variant, warehouse=second_warehouse, quantity=10
    )

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {"warehouse": second_warehouse_id, "quantity": 100},
        {"warehouse": second_warehouse_id, "quantity": 120},
    ]

    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    errors = data["errors"]

    assert len(errors) == 3
    assert {error["code"] for error in errors} == {
        StockErrorCode.UNIQUE.name,
    }
    assert {error["field"] for error in errors} == {
        "warehouse",
    }
    assert {error["index"] for error in errors} == {1, 2}


VARIANT_UPDATE_AND_STOCKS_CREATE_MUTATION = """
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
    productVariantStocksCreate(variantId: $id, stocks: $stocks) {
      productVariant {
        ...ProductVariant
      }
    }
  }
"""


def test_invalidate_stocks_dataloader_on_create_stocks(
    staff_api_client, variant_with_many_stocks, permission_manage_products
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", stock.warehouse.id)
        for stock in variant_with_many_stocks.stocks.all()
    ]
    variant.stocks.all().delete()
    variables = {
        "id": variant_id,
        "stocks": [
            {"warehouse": warehouse_id, "quantity": 10}
            for warehouse_id in warehouse_ids
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_UPDATE_AND_STOCKS_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    variant_data = content["data"]["productVariantUpdate"]["productVariant"]
    create_stocks_data = content["data"]["productVariantStocksCreate"]["productVariant"]

    # no stocks are present after the first mutation
    assert variant_data["stocks"] == []

    # stocks are returned in the second mutation, after dataloader invalidation
    assert len(create_stocks_data["stocks"]) == len(warehouse_ids)


@mock.patch(
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_back_in_stock_in_channel"
)
def test_create_stocks_triggers_back_in_stock_in_channel_for_non_cc_warehouses(
    mocked_trigger,
    staff_api_client,
    variant,
    warehouses,
    channel_USD,
    site_settings,
    permission_manage_products,
):
    # given - creating stocks in two non-C&C warehouses
    site_settings.use_legacy_shipping_zone_stock_availability = False
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    warehouses[0].channels.add(channel_USD)
    warehouses[1].channels.add(channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", warehouse.pk)
        for warehouse in warehouses
    ]
    variables = {
        "variantId": variant_id,
        "stocks": [
            {"warehouse": warehouse_ids[0], "quantity": 10},
            {"warehouse": warehouse_ids[1], "quantity": 5},
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables=variables,
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then - fires once per (variant, channel), dedup across the two warehouses
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].variant_id == variant.id
    assert stock_infos[0].channel_slug == channel_USD.slug


@mock.patch(
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_back_in_stock_for_click_and_collect"
)
def test_create_stocks_triggers_back_in_stock_for_click_and_collect(
    mocked_trigger,
    staff_api_client,
    variant,
    channel_USD,
    address,
    site_settings,
    permission_manage_products,
):
    # given - creating stocks in two C&C warehouses
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
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", warehouse.pk)
        for warehouse in cc_warehouses
    ]
    variables = {
        "variantId": variant_id,
        "stocks": [
            {"warehouse": warehouse_ids[0], "quantity": 10},
            {"warehouse": warehouse_ids[1], "quantity": 5},
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
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
    ".trigger_product_variant_back_in_stock_in_channel"
)
@mock.patch(
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_back_in_stock_for_click_and_collect"
)
def test_create_stocks_skips_channel_events_when_legacy_flag_enabled(
    mocked_back_cc,
    mocked_back,
    staff_api_client,
    variant,
    warehouses,
    site_settings,
    permission_manage_products,
):
    # given - legacy flag is on; creating stocks in two warehouses
    site_settings.use_legacy_shipping_zone_stock_availability = True
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", warehouse.pk)
        for warehouse in warehouses
    ]
    variables = {
        "variantId": variant_id,
        "stocks": [
            {"warehouse": warehouse_ids[0], "quantity": 10},
            {"warehouse": warehouse_ids[1], "quantity": 5},
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables=variables,
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then
    mocked_back.assert_not_called()
    mocked_back_cc.assert_not_called()


VARIANT_STOCKS_CREATE_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation ProductVariantStocksCreate(
        $variantId: ID, $variantExternalReference: String, $stocks: [StockInput!]!
    ){
        productVariantStocksCreate(
            variantId: $variantId,
            variantExternalReference: $variantExternalReference,
            stocks: $stocks
        ){
            productVariant{
                id
                stocks {
                    quantity
                    warehouse{
                        slug
                    }
                }
            }
            errors{
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
    assert variant.stocks.exists() is False
    back_in_stock = mocker.patch(
        "saleor.graphql.product.bulk_mutations.product_variant_stocks_create"
        ".trigger_product_variant_back_in_stock"
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
        VARIANT_STOCKS_CREATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVariantStocksCreate"]
    assert data["errors"] == []
    assert data["productVariant"] == {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "stocks": [{"quantity": quantity, "warehouse": {"slug": warehouse.slug}}],
    }
    stock = Stock.objects.get(product_variant=variant)
    assert stock.warehouse_id == warehouse.pk
    assert stock.quantity == quantity
    back_in_stock.assert_called_once()


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'variantId', "
            "'variantExternalReference'.",
        ),
        (
            "null",
            {"variantId": None, "variantExternalReference": None},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'variantId', "
            "'variantExternalReference'.",
        ),
        (
            "empty",
            {"variantExternalReference": ""},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'variantId', "
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
    assert variant.stocks.exists() is False
    back_in_stock = mocker.patch(
        "saleor.graphql.product.bulk_mutations.product_variant_stocks_create"
        ".trigger_product_variant_back_in_stock"
    )
    variables = dict(identifiers)
    if _case == "both":
        variables["variantId"] = graphene.Node.to_global_id(
            "ProductVariant", variant.pk
        )
    variables["stocks"] = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    # when
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    data = get_graphql_content(response)["data"]["productVariantStocksCreate"]
    assert data["productVariant"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    assert variant.stocks.exists() is False
    back_in_stock.assert_not_called()


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
    assert variant.stocks.exists() is False
    back_in_stock = mocker.patch(
        "saleor.graphql.product.bulk_mutations.product_variant_stocks_create"
        ".trigger_product_variant_back_in_stock"
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
        VARIANT_STOCKS_CREATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["productVariantStocksCreate"]
        assert data["errors"] == []
        assert data["productVariant"]["id"] == graphene.Node.to_global_id(
            "ProductVariant", variant.pk
        )
        stock = Stock.objects.get(product_variant=variant)
        assert stock.warehouse_id == warehouse.pk
        assert stock.quantity == quantity
        back_in_stock.assert_called_once()
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"productVariantStocksCreate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["productVariantStocksCreate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_PRODUCTS"
        )
        assert variant.stocks.exists() is False
        back_in_stock.assert_not_called()
