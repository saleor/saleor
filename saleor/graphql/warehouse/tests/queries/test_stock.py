from datetime import timedelta

import graphene
from django.utils import timezone

from .....permission.enums import ProductPermissions
from .....warehouse.models import Reservation
from .....warehouse.tests.utils import get_quantity_allocated_for_stock
from ....tests.utils import (
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


def test_query_stock_requires_permission(staff_api_client, stock):
    # given
    assert not staff_api_client.user.has_perm(ProductPermissions.MANAGE_PRODUCTS)
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)

    # when
    response = staff_api_client.post_graphql(QUERY_STOCK, variables={"id": stock_id})

    # then
    assert_no_permission(response)


def test_query_stock(staff_api_client, stock, permission_manage_products):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)

    # when
    response = staff_api_client.post_graphql(QUERY_STOCK, variables={"id": stock_id})

    # then
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
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)

    # when
    response = staff_api_client.post_graphql(QUERY_STOCK, variables={"id": stock_id})

    # then
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
    # given
    Reservation.objects.update(reserved_until=timezone.now() - timedelta(minutes=2))
    staff_api_client.user.user_permissions.add(permission_manage_products)
    stock_id = graphene.Node.to_global_id("Stock", stock.pk)

    # when
    response = staff_api_client.post_graphql(QUERY_STOCK, variables={"id": stock_id})

    # then
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
    # given
    id = "bh/"
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_STOCK, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: Stock."
    assert content["data"]["stock"] is None


def test_staff_query_stock_with_invalid_object_type(
    staff_api_client, stock, permission_manage_products
):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", stock.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_STOCK, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["stock"] is None
