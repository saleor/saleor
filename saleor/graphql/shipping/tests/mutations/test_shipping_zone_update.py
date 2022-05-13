from unittest import mock

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....shipping.error_codes import ShippingErrorCode
from .....shipping.models import ShippingMethodChannelListing
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

UPDATE_SHIPPING_ZONE_MUTATION = """
    mutation updateShipping(
        $id: ID!
        $name: String
        $description: String
        $default: Boolean
        $countries: [String!]
        $addWarehouses: [ID!]
        $removeWarehouses: [ID!]
        $addChannels: [ID!]
        $removeChannels: [ID!]
    ) {
        shippingZoneUpdate(
            id: $id
            input: {
                name: $name
                description: $description
                default: $default
                countries: $countries
                addWarehouses: $addWarehouses
                removeWarehouses: $removeWarehouses
                addChannels: $addChannels
                removeChannels: $removeChannels
            }
        ) {
            shippingZone {
                id
                name
                description
                warehouses {
                    name
                    slug
                }
                channels {
                    id
                }
            }
            errors {
                field
                code
                warehouses
                channels
            }
        }
    }
"""


def test_update_shipping_zone(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    name = "Parabolic name"
    description = "Description of a shipping zone."
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "id": shipping_id,
        "name": name,
        "countries": [],
        "description": description,
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["errors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert data["name"] == name
    assert data["description"] == description


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_update_shipping_zone_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_shipping,
    shipping_zone,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "id": graphene.Node.to_global_id("ShippingZone", shipping_zone.id),
        "name": "New Shipping Zone Name",
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    shipping_zone.refresh_from_db()

    # then
    assert data["errors"] == []
    assert data["shippingZone"]

    mocked_webhook_trigger.assert_called_once_with(
        {
            "id": variables["id"],
            "meta": generate_meta(
                requestor_data=generate_requestor(
                    SimpleLazyObject(lambda: staff_api_client.user)
                )
            ),
        },
        WebhookEventAsyncType.SHIPPING_ZONE_UPDATED,
        [any_webhook],
        shipping_zone,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_update_shipping_zone_default_exists(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    default_zone = shipping_zone
    default_zone.default = True
    default_zone.pk = None
    default_zone.save()
    shipping_zone = shipping_zone.__class__.objects.filter(default=False).get()

    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {"id": shipping_id, "name": "Name", "countries": [], "default": True}
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert data["errors"][0]["field"] == "default"
    assert data["errors"][0]["code"] == ShippingErrorCode.ALREADY_EXISTS.name


def test_update_shipping_zone_add_warehouses(
    staff_api_client,
    shipping_zone,
    warehouses,
    permission_manage_shipping,
):
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", warehouse.pk)
        for warehouse in warehouses
    ]
    warehouse_names = [warehouse.name for warehouse in warehouses]

    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "addWarehouses": warehouse_ids,
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["errors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    for response_warehouse in data["warehouses"]:
        assert response_warehouse["name"] in warehouse_names
    assert len(data["warehouses"]) == len(warehouse_names)


def test_update_shipping_zone_add_second_warehouses(
    staff_api_client,
    shipping_zone,
    warehouse,
    warehouse_no_shipping_zone,
    permission_manage_shipping,
):
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    warehouse_id = graphene.Node.to_global_id(
        "Warehouse", warehouse_no_shipping_zone.pk
    )
    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "addWarehouses": [warehouse_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["errors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert data["warehouses"][1]["slug"] == warehouse.slug
    assert data["warehouses"][0]["slug"] == warehouse_no_shipping_zone.slug


def test_update_shipping_zone_remove_warehouses(
    staff_api_client,
    shipping_zone,
    warehouse,
    permission_manage_shipping,
):
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "removeWarehouses": [warehouse_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["errors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert not data["warehouses"]


def test_update_shipping_zone_remove_one_warehouses(
    staff_api_client,
    shipping_zone,
    warehouses,
    permission_manage_shipping,
):
    for warehouse in warehouses:
        warehouse.shipping_zones.add(shipping_zone)
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouses[0].pk)
    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "removeWarehouses": [warehouse_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["errors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert data["warehouses"][0]["name"] == warehouses[1].name
    assert len(data["warehouses"]) == 1


def test_update_shipping_zone_replace_warehouse(
    staff_api_client,
    shipping_zone,
    warehouse,
    warehouse_no_shipping_zone,
    permission_manage_shipping,
):
    assert shipping_zone.warehouses.first() == warehouse

    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    add_warehouse_id = graphene.Node.to_global_id(
        "Warehouse", warehouse_no_shipping_zone.pk
    )
    remove_warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "addWarehouses": [add_warehouse_id],
        "removeWarehouses": [remove_warehouse_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["errors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert data["warehouses"][0]["name"] == warehouse_no_shipping_zone.name
    assert len(data["warehouses"]) == 1


def test_update_shipping_zone_same_warehouse_id_in_add_and_remove(
    staff_api_client,
    shipping_zone,
    warehouse,
    permission_manage_shipping,
):
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "addWarehouses": [warehouse_id],
        "removeWarehouses": [warehouse_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "warehouses"
    assert data["errors"][0]["code"] == ShippingErrorCode.DUPLICATED_INPUT_ITEM.name
    assert data["errors"][0]["warehouses"][0] == warehouse_id


def test_update_shipping_zone_add_channels(
    staff_api_client,
    shipping_zone,
    channel_USD,
    channel_PLN,
    permission_manage_shipping,
):
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]

    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "addChannels": channel_ids,
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["errors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert len(data["channels"]) == len(channel_ids)
    assert {channel["id"] for channel in data["channels"]} == set(channel_ids)


@mock.patch(
    "saleor.graphql.shipping.mutations.shippings."
    "drop_invalid_shipping_methods_relations_for_given_channels.delay"
)
def test_update_shipping_zone_remove_channels(
    mocked_drop_invalid_shipping_methods_relations,
    staff_api_client,
    shipping_zone,
    channel_USD,
    channel_PLN,
    permission_manage_shipping,
):
    shipping_zone.channels.add(channel_USD, channel_PLN)
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)

    shipping_listing = ShippingMethodChannelListing.objects.filter(
        shipping_method__shipping_zone=shipping_zone, channel=channel_USD
    )
    assert shipping_listing
    shipping_method_ids = list(
        shipping_listing.values_list("shipping_method_id", flat=True)
    )

    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "removeChannels": [channel_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["errors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert len(data["channels"]) == 1
    assert data["channels"][0]["id"] == graphene.Node.to_global_id(
        "Channel", channel_PLN.pk
    )
    assert not ShippingMethodChannelListing.objects.filter(
        shipping_method__shipping_zone=shipping_zone, channel=channel_USD
    )
    mocked_drop_invalid_shipping_methods_relations.assert_called_once_with(
        shipping_method_ids, [channel_USD.pk]
    )


def test_update_shipping_zone_add_and_remove_channels(
    staff_api_client,
    shipping_zone,
    channel_USD,
    channel_PLN,
    permission_manage_shipping,
):
    shipping_zone.channels.add(channel_USD)
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    add_channel_id = graphene.Node.to_global_id("Channel", channel_PLN.pk)
    remove_channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)

    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "removeChannels": [remove_channel_id],
        "addChannels": [add_channel_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["errors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert len(data["channels"]) == 1
    assert data["channels"][0]["id"] == add_channel_id


def test_update_shipping_zone_same_channel_id_in_add_and_remove_list(
    staff_api_client,
    shipping_zone,
    channel_USD,
    channel_PLN,
    permission_manage_shipping,
):
    shipping_zone.channels.add(channel_USD)
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    add_channel_id = graphene.Node.to_global_id("Channel", channel_PLN.pk)
    remove_channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)

    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "removeChannels": [remove_channel_id],
        "addChannels": [add_channel_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["errors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert len(data["channels"]) == 1
    assert data["channels"][0]["id"] == add_channel_id
