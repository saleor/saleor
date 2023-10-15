import graphene

from .....warehouse.error_codes import WarehouseErrorCode
from ....tests.utils import get_graphql_content

MUTATION_ASSIGN_SHIPPING_ZONE_WAREHOUSE = """
mutation assignWarehouseShippingZone($id: ID!, $shippingZoneIds: [ID!]!) {
  assignWarehouseShippingZone(id: $id, shippingZoneIds: $shippingZoneIds) {
    errors {
      field
      message
      code
      shippingZones
    }
  }
}

"""


def test_shipping_zone_can_be_assigned_only_to_one_warehouse(
    staff_api_client, warehouse, warehouse_JPY, permission_manage_products
):
    # given
    used_shipping_zone = warehouse.shipping_zones.first()
    used_shipping_zone_id = graphene.Node.to_global_id(
        "ShippingZone", used_shipping_zone.pk
    )
    zone_warehouses_count = used_shipping_zone.warehouses.count()

    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse_JPY.pk),
        "shippingZoneIds": [used_shipping_zone_id],
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_ASSIGN_SHIPPING_ZONE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["assignWarehouseShippingZone"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == WarehouseErrorCode.INVALID.name
    assert errors[0]["field"] == "shippingZones"
    used_shipping_zone.refresh_from_db()
    assert used_shipping_zone.warehouses.count() == zone_warehouses_count


def test_shipping_zone_assign_to_warehouse(
    staff_api_client,
    warehouse_no_shipping_zone,
    shipping_zone,
    permission_manage_products,
):
    # given
    assert not warehouse_no_shipping_zone.shipping_zones.all()
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse_no_shipping_zone.pk),
        "shippingZoneIds": [
            graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
        ],
    }

    # when
    staff_api_client.post_graphql(
        MUTATION_ASSIGN_SHIPPING_ZONE_WAREHOUSE, variables=variables
    )

    # then
    warehouse_no_shipping_zone.refresh_from_db()
    shipping_zone.refresh_from_db()
    assert warehouse_no_shipping_zone.shipping_zones.first().pk == shipping_zone.pk


def test_shipping_zone_assign_to_warehouse_no_common_channel(
    staff_api_client,
    warehouse_no_shipping_zone,
    shipping_zone,
    permission_manage_products,
    channel_PLN,
):
    # given
    assert not warehouse_no_shipping_zone.shipping_zones.all()

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # remove channel_USD from shipping zone channels, assign channel_PLN
    shipping_zone.channels.set([channel_PLN])

    zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)

    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse_no_shipping_zone.pk),
        "shippingZoneIds": [zone_id],
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_ASSIGN_SHIPPING_ZONE_WAREHOUSE, variables=variables
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["assignWarehouseShippingZone"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == WarehouseErrorCode.INVALID.name
    assert errors[0]["field"] == "shippingZones"
    assert errors[0]["shippingZones"] == [zone_id]


def test_shipping_zone_assign_to_warehouse_no_zone_channels(
    staff_api_client,
    warehouse_no_shipping_zone,
    shipping_zone,
    permission_manage_products,
    channel_PLN,
):
    # given
    assert not warehouse_no_shipping_zone.shipping_zones.all()

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # remove all channels from the shipping zone
    shipping_zone.channels.clear()

    zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)

    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse_no_shipping_zone.pk),
        "shippingZoneIds": [
            graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_ASSIGN_SHIPPING_ZONE_WAREHOUSE, variables=variables
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["assignWarehouseShippingZone"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == WarehouseErrorCode.INVALID.name
    assert errors[0]["field"] == "shippingZones"
    assert errors[0]["shippingZones"] == [zone_id]


def test_empty_shipping_zone_assign_to_warehouse(
    staff_api_client,
    warehouse_no_shipping_zone,
    shipping_zone,
    permission_manage_products,
):
    # given
    assert not warehouse_no_shipping_zone.shipping_zones.all()
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse_no_shipping_zone.pk),
        "shippingZoneIds": [],
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_ASSIGN_SHIPPING_ZONE_WAREHOUSE, variables=variables
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["assignWarehouseShippingZone"]["errors"]
    warehouse_no_shipping_zone.refresh_from_db()
    shipping_zone.refresh_from_db()

    assert not warehouse_no_shipping_zone.shipping_zones.all()
    assert errors[0]["field"] == "shippingZoneId"
    assert errors[0]["code"] == "GRAPHQL_ERROR"
