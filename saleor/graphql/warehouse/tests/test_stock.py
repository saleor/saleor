from datetime import timedelta

import graphene
from django.utils import timezone

from ....core.permissions import ProductPermissions
from ....warehouse.models import Reservation, Stock, Warehouse
from ....warehouse.tests.utils import get_quantity_allocated_for_stock
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

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
        quantityReserved
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
                    quantityReserved
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
    assert content_stock["quantityReserved"] == 0


def test_query_stock_with_reservations(
    site_settings_with_reservations,
    staff_api_client,
    stock,
    checkout_line_with_reservation_in_many_stocks,
    permission_manage_products,
):
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
    assert content_stock["quantityReserved"] == 2


def test_query_stock_with_expired_reservations(
    site_settings_with_reservations,
    staff_api_client,
    stock,
    checkout_line_with_reservation_in_many_stocks,
    permission_manage_products,
):
    Reservation.objects.update(reserved_until=timezone.now() - timedelta(minutes=2))
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
    assert content_stock["quantityReserved"] == 0


def test_staff_query_stock_by_invalid_id(
    staff_api_client, stock, permission_manage_products
):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_STOCK, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["stock"] is None


def test_staff_query_stock_with_invalid_object_type(
    staff_api_client, stock, permission_manage_products
):
    variables = {"id": graphene.Node.to_global_id("Order", stock.pk)}
    response = staff_api_client.post_graphql(
        QUERY_STOCK, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["stock"] is None


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


def test_stock_quantities_in_different_warehouses(
    api_client, channel_USD, variant_with_many_stocks_different_shipping_zones
):
    query = """
    query ProductVariant(
        $id: ID!, $channel: String!, $country1: CountryCode, $country2: CountryCode
    ) {
        productVariant(id: $id, channel: $channel) {
            quantityPL: quantityAvailable(address: { country: $country1 })
            quantityUS: quantityAvailable(address: { country: $country2 })
            quantityNoAddress: quantityAvailable
        }
    }
    """

    variant = variant_with_many_stocks_different_shipping_zones
    stock_map = {}
    for stock in variant.stocks.all():
        country = stock.warehouse.shipping_zones.get().countries[0]
        stock_map[country.code] = stock.quantity

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
        "country1": "PL",
        "country2": "US",
    }
    response = api_client.post_graphql(
        query,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["productVariant"]["quantityPL"] == stock_map["PL"]
    assert content["data"]["productVariant"]["quantityUS"] == stock_map["US"]

    # when country is not provided, should return max value of all available stock
    # quantities
    assert content["data"]["productVariant"]["quantityNoAddress"] == max(
        stock_map.values()
    )


def test_stock_quantity_is_max_from_all_warehouses_without_provided_country(
    api_client, channel_USD, variant_with_many_stocks_different_shipping_zones
):
    query = """
    query ProductVariant($id: ID!, $channel: String!) {
        productVariant(id: $id, channel: $channel) {
            quantityAvailable
        }
    }
    """

    variant = variant_with_many_stocks_different_shipping_zones
    max_warehouse_quantity = max([stock.quantity for stock in variant.stocks.all()])

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    assert (
        content["data"]["productVariant"]["quantityAvailable"] == max_warehouse_quantity
    )


def test_stock_quantity_is_sum_of_quantities_from_warehouses_that_support_country(
    api_client,
    address,
    channel_USD,
    shipping_zone,
    variant_with_many_stocks_different_shipping_zones,
):
    query = """
    query ProductVariant($id: ID!, $channel: String!, $country: CountryCode) {
        productVariant(id: $id, channel: $channel) {
            quantityAvailable(address: { country: $country })
        }
    }
    """

    variant = variant_with_many_stocks_different_shipping_zones

    # Create another warehouse with a different shipping zone that supports PL. As
    # a result there should be two shipping zones and two warehouses that support PL.
    stocks = variant.stocks.for_channel_and_country(channel_USD.slug, "PL")
    warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="WarehousePL",
        slug="warehousePL",
        email="warehousePL@example.com",
    )
    warehouse.shipping_zones.add(shipping_zone)
    warehouse.channels.add(channel_USD)
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=10)

    stocks = variant.stocks.for_channel_and_country(channel_USD.slug, "PL")
    sum_quantities = sum([stock.quantity for stock in stocks])

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
        "country": "PL",
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    assert content["data"]["productVariant"]["quantityAvailable"] == sum_quantities
