import graphene

from saleor.warehouse.models import Warehouse
from tests.api.utils import get_graphql_content

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

QUERY_WAREHOUSE = """
query warehouse($id: ID!){
    warehouse(id: $id) {
        id
        name
        companyName
        email
        shippingZones(first: 100) {
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
            streetAddress1
            streetAddress2
            postalCode
            city
            phone
        }
    }
}
"""


MUTATION_CREATE_WAREHOUSE = """
mutation createWarehouse($input: WarehouseCreateInput!) {
    createWarehouse(input: $input){
        errors {
            message
        }
        warehouse {
            id
            name
            companyName
        }
    }
}
"""


def test_warehouse_cannot_query_without_permissions(user_api_client, warehouse):
    assert not user_api_client.user.has_perm("warehouse.manage_warehouses")
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    response = user_api_client.post_graphql(
        QUERY_WAREHOUSE, variables={"id": warehouse_id}
    )
    content = get_graphql_content(response, ignore_errors=True)
    queried_warehouse = content["data"]["warehouse"]
    errors = content["errors"]
    assert queried_warehouse is None
    assert len(errors) == 1
    assert errors[0]["message"] == "You do not have permission to perform this action"


def test_warehouse_query(staff_api_client, warehouse, permission_manage_warehouses):
    staff_api_client.user.user_permissions.add(permission_manage_warehouses)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSE, variables={"id": warehouse_id}
    )
    content = get_graphql_content(response)

    queried_warehouse = content["data"]["warehouse"]
    assert queried_warehouse["name"] == warehouse.name
    assert queried_warehouse["email"] == warehouse.email

    shipping_zones = queried_warehouse["shippingZones"]["edges"]
    assert len(shipping_zones) == warehouse.shipping_zones.count()
    queried_shipping_zone = shipping_zones[0]["node"]
    shipipng_zone = warehouse.shipping_zones.first()
    assert queried_shipping_zone["name"] == shipipng_zone.name
    assert len(queried_shipping_zone["countries"]) == len(shipipng_zone.countries)

    address = warehouse.address
    queried_address = queried_warehouse["address"]
    assert queried_address["streetAddress1"] == address.street_address_1
    assert queried_address["postalCode"] == address.postal_code


def test_query_warehouses_requires_permissions(staff_api_client, warehouse):
    assert not staff_api_client.user.has_perm("warehouse.manage_warehouses")
    response = staff_api_client.post_graphql(QUERY_WAREHOUSES)
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["errors"]
    assert len(errors) == 1
    assert errors[0]["message"] == "You do not have permission to perform this action"


def test_query_warehouses(staff_api_client, warehouse, permission_manage_warehouses):
    staff_api_client.user.user_permissions.add(permission_manage_warehouses)
    response = staff_api_client.post_graphql(QUERY_WAREHOUSES)
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


def test_mutation_create_warehouse_requires_permission(staff_api_client):
    assert not staff_api_client.user.has_perm("warehouse.manage_warehouses")
    variables = {
        "input": {
            "name": "Test warehouse",
            "companyName": "Amazing Company Inc",
            "email": "test-admin@example.com",
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
            },
        }
    }
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE, variables=variables
    )
    content = get_graphql_content(response, ignore_errors=True)
    assert not Warehouse.objects.exists()
    errors = content["errors"]
    assert len(errors) == 1
    assert errors[0]["message"] == "You do not have permission to perform this action"


def test_mutation_create_warehouse(
    staff_api_client, permission_manage_warehouses, shipping_zone
):
    assert not Warehouse.objects.exists()
    staff_api_client.user.user_permissions.add(permission_manage_warehouses)
    variables = {
        "input": {
            "name": "Test warehouse",
            "companyName": "Amazing Company Inc",
            "email": "test-admin@example.com",
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
            },
            "shippingZones": [
                graphene.Node.to_global_id("ShippingZone", shipping_zone.id)
            ],
        }
    }

    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE, variables=variables
    )
    content = get_graphql_content(response)
    assert Warehouse.objects.count() == 1
    warehouse = Warehouse.objects.prefetch_data().first()
    created_warehouse = content["data"]["createWarehouse"]["warehouse"]
    assert created_warehouse["id"] == graphene.Node.to_global_id(
        "Warehouse", warehouse.id
    )
    assert created_warehouse["name"] == warehouse.name
