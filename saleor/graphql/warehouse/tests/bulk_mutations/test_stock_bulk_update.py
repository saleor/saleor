from unittest.mock import patch

import graphene

from .....warehouse.error_codes import StockBulkUpdateErrorCode
from ....tests.utils import get_graphql_content

STOCKS_BULK_UPDATE_MUTATION = """
    mutation StockBulkUpdate($stocks: [StockBulkUpdateInput!]!){
        stockBulkUpdate(stocks: $stocks){
            results{
                errors {
                    field
                    message
                    code
                }
                stock{
                    id
                    quantity
                }
            }
            count
        }
    }
"""


def test_stocks_bulk_update_using_ids(
    staff_api_client,
    variant_with_many_stocks,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = variant.stocks.all()
    stock_1 = stocks[0]
    stock_2 = stocks[1]
    new_quantity_1 = 999
    new_quantity_2 = 12

    assert stock_1.quantity != new_quantity_1
    assert stock_2.quantity != new_quantity_2

    warehouse_1_id = graphene.Node.to_global_id("Warehouse", stock_1.warehouse_id)
    warehouse_2_id = graphene.Node.to_global_id("Warehouse", stock_2.warehouse_id)

    stocks_input = [
        {
            "variantId": variant_id,
            "warehouseId": warehouse_1_id,
            "quantity": new_quantity_1,
        },
        {
            "variantId": variant_id,
            "warehouseId": warehouse_2_id,
            "quantity": new_quantity_2,
        },
    ]

    variables = {"stocks": stocks_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(STOCKS_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["stockBulkUpdate"]

    # then
    stock_1.refresh_from_db()
    stock_2.refresh_from_db()
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert stock_1.quantity == new_quantity_1
    assert stock_2.quantity == new_quantity_2


@patch(
    "saleor.graphql.warehouse.bulk_mutations."
    "stock_bulk_update.get_webhooks_for_event"
)
@patch("saleor.plugins.manager.PluginsManager.product_variant_stock_updated")
def test_stocks_bulk_update_send_stock_updated_event(
    product_variant_stock_update_webhook,
    mocked_get_webhooks_for_event,
    staff_api_client,
    variant_with_many_stocks,
    permission_manage_products,
    any_webhook,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = variant.stocks.all()
    stock = stocks[0]
    new_quantity = 999

    assert stock.quantity != new_quantity

    warehouse_id = graphene.Node.to_global_id("Warehouse", stock.warehouse_id)

    stocks_input = [
        {"variantId": variant_id, "warehouseId": warehouse_id, "quantity": new_quantity}
    ]

    variables = {"stocks": stocks_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(STOCKS_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["stockBulkUpdate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert product_variant_stock_update_webhook.call_count == 1


def test_stocks_bulk_update_using_external_refs(
    staff_api_client,
    variant_with_many_stocks,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    variant_external_reference = variant.external_reference
    stocks = variant.stocks.all()
    stock_1 = stocks[0]
    stock_2 = stocks[1]
    new_quantity_1 = 999
    new_quantity_2 = 12

    assert stock_1.quantity != new_quantity_1
    assert stock_2.quantity != new_quantity_2

    warehouse_1_external_reference = stock_1.warehouse.external_reference
    warehouse_2_external_reference = stock_2.warehouse.external_reference

    stocks_input = [
        {
            "variantExternalReference": variant_external_reference,
            "warehouseExternalReference": warehouse_1_external_reference,
            "quantity": new_quantity_1,
        },
        {
            "variantExternalReference": variant_external_reference,
            "warehouseExternalReference": warehouse_2_external_reference,
            "quantity": new_quantity_2,
        },
    ]

    variables = {"stocks": stocks_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(STOCKS_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["stockBulkUpdate"]

    # then
    stock_1.refresh_from_db()
    stock_2.refresh_from_db()
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert stock_1.quantity == new_quantity_1
    assert stock_2.quantity == new_quantity_2


def test_stocks_bulk_update_using_variant_id_and_warehouse_external_ref(
    staff_api_client,
    variant_with_many_stocks,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = variant.stocks.all()
    stock_1 = stocks[0]
    stock_2 = stocks[1]
    new_quantity_1 = 999
    new_quantity_2 = 12

    assert stock_1.quantity != new_quantity_1
    assert stock_2.quantity != new_quantity_2

    warehouse_1_external_reference = stock_1.warehouse.external_reference
    warehouse_2_external_reference = stock_2.warehouse.external_reference

    stocks_input = [
        {
            "variantId": variant_id,
            "warehouseExternalReference": warehouse_1_external_reference,
            "quantity": new_quantity_1,
        },
        {
            "variantId": variant_id,
            "warehouseExternalReference": warehouse_2_external_reference,
            "quantity": new_quantity_2,
        },
    ]

    variables = {"stocks": stocks_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(STOCKS_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["stockBulkUpdate"]

    # then
    stock_1.refresh_from_db()
    stock_2.refresh_from_db()
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert stock_1.quantity == new_quantity_1
    assert stock_2.quantity == new_quantity_2


def test_stocks_bulk_update_using_variant_external_ref_and_warehouse_id(
    staff_api_client,
    variant_with_many_stocks,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    variant_external_reference = variant.external_reference

    stocks = variant.stocks.all()
    stock_1 = stocks[0]
    stock_2 = stocks[1]
    new_quantity_1 = 999
    new_quantity_2 = 12

    assert stock_1.quantity != new_quantity_1
    assert stock_2.quantity != new_quantity_2

    warehouse_1_id = graphene.Node.to_global_id("Warehouse", stock_1.warehouse_id)
    warehouse_2_id = graphene.Node.to_global_id("Warehouse", stock_2.warehouse_id)

    stocks_input = [
        {
            "variantExternalReference": variant_external_reference,
            "warehouseId": warehouse_1_id,
            "quantity": new_quantity_1,
        },
        {
            "variantExternalReference": variant_external_reference,
            "warehouseId": warehouse_2_id,
            "quantity": new_quantity_2,
        },
    ]

    variables = {"stocks": stocks_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(STOCKS_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["stockBulkUpdate"]

    # then
    stock_1.refresh_from_db()
    stock_2.refresh_from_db()
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert stock_1.quantity == new_quantity_1
    assert stock_2.quantity == new_quantity_2


def test_stocks_bulk_update_when_no_variant_args_provided(
    staff_api_client,
    variant_with_many_stocks,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    stock = variant.stocks.first()

    warehouse_id = graphene.Node.to_global_id("Warehouse", stock.warehouse_id)

    stocks_input = [
        {"warehouseId": warehouse_id, "quantity": 10},
    ]

    variables = {"stocks": stocks_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(STOCKS_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["stockBulkUpdate"]

    # then
    assert data["count"] == 0
    assert data["results"][0]["errors"]
    error = data["results"][0]["errors"][0]
    assert error["message"] == (
        "At least one of arguments is required: 'variantId', "
        "'variantExternalReference'."
    )


def test_stocks_bulk_update_when_invalid_variant_id_provided(
    staff_api_client,
    variant_with_many_stocks,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    stock = variant.stocks.first()

    warehouse_id = graphene.Node.to_global_id("Warehouse", stock.warehouse_id)

    stocks_input = [
        {"variantId": "abcd", "warehouseId": warehouse_id, "quantity": 10},
    ]

    variables = {"stocks": stocks_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(STOCKS_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["stockBulkUpdate"]

    # then
    assert data["count"] == 0
    assert data["results"][0]["errors"]
    error = data["results"][0]["errors"][0]
    assert error["message"] == "Invalid variantId."


def test_stocks_bulk_update_when_no_warehouse_args_provided(
    staff_api_client,
    variant_with_many_stocks,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    stocks_input = [
        {"variantId": variant_id, "quantity": 10},
    ]

    variables = {"stocks": stocks_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(STOCKS_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["stockBulkUpdate"]

    # then
    assert data["count"] == 0
    assert data["results"][0]["errors"]
    error = data["results"][0]["errors"][0]
    assert error["message"] == (
        "At least one of arguments is required: 'warehouseId', "
        "'warehouseExternalReference'."
    )


def test_stocks_bulk_update_when_invalid_warehouse_id_provided(
    staff_api_client,
    variant_with_many_stocks,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    stocks_input = [
        {"variantId": variant_id, "warehouseId": "abcd", "quantity": 10},
    ]

    variables = {"stocks": stocks_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(STOCKS_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["stockBulkUpdate"]

    # then
    assert data["count"] == 0
    assert data["results"][0]["errors"]
    error = data["results"][0]["errors"][0]
    assert error["message"] == "Invalid warehouseId."


def test_stocks_bulk_update_when_stock_not_exists(
    staff_api_client, variant_with_many_stocks, permission_manage_products, warehouse
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert not variant.stocks.filter(warehouse=warehouse).exists()

    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)

    stocks_input = [
        {"variantId": variant_id, "warehouseId": warehouse_id, "quantity": 10},
    ]

    variables = {"stocks": stocks_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(STOCKS_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["stockBulkUpdate"]

    # then
    assert data["count"] == 0
    assert data["results"][0]["errors"]
    error = data["results"][0]["errors"][0]
    assert error["code"] == StockBulkUpdateErrorCode.NOT_FOUND.name
    assert error["message"] == "Stock was not found."
