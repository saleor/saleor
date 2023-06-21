import graphene

from .....warehouse.models import Warehouse
from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_WAREHOUSES = """
query {
    warehouses(first:100) {
        totalCount
        edges {
            node {
                id
                name
                companyName
                email
                shippingZones(first:100) {
                    edges {
                        node {
                            name
                            countries {
                                country
                            }
                        }
                    }
                }
                address {
                    city
                    postalCode
                    country {
                        country
                    }
                    phone
                }
            }
        }
    }
}
"""


def test_query_warehouses_as_staff_with_manage_orders(
    staff_api_client, warehouse, permission_manage_orders
):
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)["data"]
    assert content["warehouses"]["totalCount"] == Warehouse.objects.count()
    warehouses = content["warehouses"]["edges"]
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    warehouse_first = warehouses[0]["node"]
    assert warehouse_first["id"] == warehouse_id
    assert warehouse_first["name"] == warehouse.name
    assert (
        len(warehouse_first["shippingZones"]["edges"])
        == warehouse.shipping_zones.count()
    )


def test_query_warehouses_as_staff_with_manage_shipping(
    staff_api_client, warehouse, permission_manage_shipping
):
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)["data"]
    assert content["warehouses"]["totalCount"] == Warehouse.objects.count()
    warehouses = content["warehouses"]["edges"]
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    warehouse_first = warehouses[0]["node"]
    assert warehouse_first["id"] == warehouse_id
    assert warehouse_first["name"] == warehouse.name
    assert (
        len(warehouse_first["shippingZones"]["edges"])
        == warehouse.shipping_zones.count()
    )


def test_query_warehouses_as_staff_with_manage_apps(
    staff_api_client, warehouse, permission_manage_apps
):
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES, permissions=[permission_manage_apps]
    )
    assert_no_permission(response)


def test_query_warehouses_as_customer(
    user_api_client, warehouse, permission_manage_apps
):
    response = user_api_client.post_graphql(QUERY_WAREHOUSES)
    assert_no_permission(response)


def test_query_warehouses(staff_api_client, warehouse, permission_manage_products):
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]
    assert content["warehouses"]["totalCount"] == Warehouse.objects.count()
    warehouses = content["warehouses"]["edges"]
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    warehouse_first = warehouses[0]["node"]
    assert warehouse_first["id"] == warehouse_id
    assert warehouse_first["name"] == warehouse.name
    assert (
        len(warehouse_first["shippingZones"]["edges"])
        == warehouse.shipping_zones.count()
    )
