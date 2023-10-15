import graphene

MUTATION_UNASSIGN_SHIPPING_ZONE_WAREHOUSE = """
mutation unassignWarehouseShippingZone($id: ID!, $shippingZoneIds: [ID!]!) {
  unassignWarehouseShippingZone(id: $id, shippingZoneIds: $shippingZoneIds) {
    errors {
      field
      message
      code
    }
  }
}

"""


def test_shipping_zone_unassign_from_warehouse(
    staff_api_client, warehouse, shipping_zone, permission_manage_products
):
    # given
    assert warehouse.shipping_zones.first().pk == shipping_zone.pk
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse.pk),
        "shippingZoneIds": [
            graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
        ],
    }

    # when
    staff_api_client.post_graphql(
        MUTATION_UNASSIGN_SHIPPING_ZONE_WAREHOUSE, variables=variables
    )

    # then
    warehouse.refresh_from_db()
    shipping_zone.refresh_from_db()
    assert not warehouse.shipping_zones.all()
