import json
from unittest.mock import patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time

from .....channel.error_codes import ChannelErrorCode
from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import AllocationStrategyEnum

CHANNEL_UPDATE_MUTATION = """
    mutation UpdateChannel($id: ID!,$input: ChannelUpdateInput!){
        channelUpdate(id: $id, input: $input){
            channel{
                id
                name
                slug
                currencyCode
                defaultCountry {
                    code
                    country
                }
                warehouses {
                    slug
                }
                stockSettings {
                    allocationStrategy
                }
            }
            errors{
                field
                code
                message
                shippingZones
                warehouses
            }
        }
    }
"""


def test_channel_update_mutation_as_staff_user(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    default_country = "FR"
    allocation_strategy = AllocationStrategyEnum.PRIORITIZE_SORTING_ORDER.name
    variables = {
        "id": channel_id,
        "input": {
            "name": name,
            "slug": slug,
            "defaultCountry": default_country,
            "stockSettings": {"allocationStrategy": allocation_strategy},
        },
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"
    assert (
        channel_data["defaultCountry"]["code"]
        == channel_USD.default_country.code
        == default_country
    )
    assert channel_data["stockSettings"]["allocationStrategy"] == allocation_strategy


def test_channel_update_mutation_as_app(
    permission_manage_channels, app_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = app_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"


def test_channel_update_mutation_as_customer(user_api_client, channel_USD):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = user_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(),
    )

    # then
    assert_no_permission(response)


def test_channel_update_mutation_as_anonymous(api_client, channel_USD):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(),
    )

    # then
    assert_no_permission(response)


def test_channel_update_mutation_slugify_slug_field(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "testName"
    slug = "Invalid slug"
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channelUpdate"]["channel"]
    assert channel_data["slug"] == slugify(slug)


def test_channel_update_mutation_with_duplicated_slug(
    permission_manage_channels, staff_api_client, channel_USD, channel_PLN
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "New Channel"
    slug = channel_PLN.slug
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["channelUpdate"]["errors"][0]
    assert error["field"] == "slug"
    assert error["code"] == ChannelErrorCode.UNIQUE.name


def test_channel_update_mutation_only_name(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = channel_USD.slug
    variables = {"id": channel_id, "input": {"name": name}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"


def test_channel_update_mutation_only_slug(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = channel_USD.name
    slug = "new_slug"
    variables = {"id": channel_id, "input": {"slug": slug}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"


def test_channel_update_mutation_add_shipping_zone(
    permission_manage_channels, staff_api_client, channel_USD, shipping_zone
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "id": channel_id,
        "input": {"name": name, "slug": slug, "addShippingZones": [shipping_zone_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel_USD.refresh_from_db()
    shipping_zone.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"
    actual_shipping_zone = channel_USD.shipping_zones.first()
    assert actual_shipping_zone == shipping_zone


@patch(
    "saleor.graphql.channel.mutations.channel_update."
    "drop_invalid_shipping_methods_relations_for_given_channels.delay"
)
def test_channel_update_mutation_remove_shipping_zone(
    mocked_drop_invalid_shipping_methods_relations,
    permission_manage_channels,
    staff_api_client,
    channel_USD,
    shipping_zones,
    warehouses,
    channel_PLN,
):
    # given
    channel_USD.shipping_zones.add(*shipping_zones)
    channel_PLN.shipping_zones.add(*shipping_zones)

    for warehouse in warehouses:
        warehouse.shipping_zones.add(*shipping_zones)

    # add another common channel with zone to warehouses on index 1
    channel_PLN.warehouses.add(warehouses[0])

    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    shipping_zone = shipping_zones[0]
    shipping_method_ids = shipping_zone.shipping_methods.values_list("id", flat=True)
    remove_shipping_zone = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "id": channel_id,
        "input": {
            "name": name,
            "slug": slug,
            "removeShippingZones": [remove_shipping_zone],
        },
    }
    assert channel_USD.shipping_method_listings.filter(
        shipping_method__shipping_zone=shipping_zone
    )

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"
    assert not channel_USD.shipping_method_listings.filter(
        shipping_method__shipping_zone=shipping_zone
    )
    mocked_drop_invalid_shipping_methods_relations.assert_called_once_with(
        list(shipping_method_ids), [channel_USD.id]
    )
    # ensure one warehouse was removed from shipping zone as they do not have
    # common channel anymore
    assert warehouses[0].id not in shipping_zones[0].warehouses.values("id")

    # ensure another shipping zone has all warehouses assigned
    for zone in shipping_zones[1:]:
        assert zone.warehouses.count() == len(warehouses)


def test_channel_update_mutation_add_and_remove_shipping_zone(
    permission_manage_channels,
    staff_api_client,
    channel_USD,
    shipping_zones,
    shipping_zone,
):
    # given
    channel_USD.shipping_zones.add(*shipping_zones)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    remove_shipping_zone = graphene.Node.to_global_id(
        "ShippingZone", shipping_zones[0].pk
    )
    add_shipping_zone = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "id": channel_id,
        "input": {
            "name": name,
            "slug": slug,
            "addShippingZones": [add_shipping_zone],
            "removeShippingZones": [remove_shipping_zone],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"
    zones = channel_USD.shipping_zones.all()
    assert len(zones) == len(shipping_zones)


def test_channel_update_mutation_duplicated_shipping_zone(
    permission_manage_channels,
    staff_api_client,
    channel_USD,
    shipping_zones,
    shipping_zone,
):
    # given
    channel_USD.shipping_zones.add(*shipping_zones)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    remove_shipping_zone = graphene.Node.to_global_id(
        "ShippingZone", shipping_zones[0].pk
    )
    add_shipping_zone = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "id": channel_id,
        "input": {
            "name": name,
            "slug": slug,
            "addShippingZones": [add_shipping_zone],
            "removeShippingZones": [remove_shipping_zone, add_shipping_zone],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["channel"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingZones"
    assert errors[0]["code"] == ChannelErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["shippingZones"] == [add_shipping_zone]


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_channel_update_mutation_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    permission_manage_channels,
    staff_api_client,
    channel_USD,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    default_country = "FR"
    variables = {
        "id": channel_id,
        "input": {"name": name, "slug": slug, "defaultCountry": default_country},
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["errors"]
    assert data["channel"]

    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": channel_id,
                "is_active": channel_USD.is_active,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.CHANNEL_UPDATED,
        [any_webhook],
        channel_USD,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_channel_update_mutation_add_warehouse(
    permission_manage_channels, staff_api_client, channel_USD, warehouse
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "id": channel_id,
        "input": {"name": name, "slug": slug, "addWarehouses": [warehouse_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel_USD.refresh_from_db()
    warehouse.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"
    assert len(channel_data["warehouses"]) == 1
    assert channel_data["warehouses"][0]["slug"] == warehouse.slug


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_channel_update_mutation_remove_warehouse(
    permission_manage_channels,
    staff_api_client,
    channel_USD,
    channel_PLN,
    channel_JPY,
    warehouses,
    warehouse_JPY,
    shipping_zones,
    count_queries,
):
    """Ensure that removing warehouses from channel works properly.

    Also, ensure that when the warehouse is removed from the channel it's also removed
    from shipping zones with which the warehouse do not have a common channel anymore.
    """
    # given
    channel_USD.warehouses.add(*(warehouses + [warehouse_JPY]))
    channel_PLN.warehouses.add(*[warehouses[0], warehouse_JPY])
    channel_JPY.warehouses.add(warehouses[1])
    for shipping_zone in shipping_zones:
        shipping_zone.warehouses.add(*warehouses)

    # add additional common channel for warehouse[1]
    shipping_zones[0].channels.add(channel_JPY)

    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    remove_warehouses = [
        graphene.Node.to_global_id("Warehouse", warehouse.pk)
        for warehouse in warehouses
    ]
    warehouses_count = channel_USD.warehouses.count()

    variables = {
        "id": channel_id,
        "input": {
            "name": name,
            "slug": slug,
            "removeWarehouses": remove_warehouses,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"
    assert len(channel_data["warehouses"]) == warehouses_count - 2
    assert {
        warehouse_data["slug"] for warehouse_data in channel_data["warehouses"]
    } == {warehouse_JPY.slug}
    # ensure warehouse from index 1 has not been deleted from any shipping zone
    for zone in shipping_zones:
        zone.refresh_from_db()
        assert warehouses[0] in zone.warehouses.all()
    # ensure warehouse from index 1 has not been deleted from shipping zone
    # with JPY channel
    assert warehouses[1] in shipping_zones[0].warehouses.all()
    # ensure warehouse from index 1 has been deleted from shipping zone
    # without JPY channel
    assert warehouses[1] not in shipping_zones[1].warehouses.all()


def test_channel_update_mutation_add_and_remove_warehouse(
    permission_manage_channels,
    staff_api_client,
    channel_USD,
    warehouses,
    warehouse,
):
    # given
    channel_USD.warehouses.add(*warehouses)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    remove_warehouse = graphene.Node.to_global_id("Warehouse", warehouses[0].pk)
    add_warehouse = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "id": channel_id,
        "input": {
            "name": name,
            "slug": slug,
            "addWarehouses": [add_warehouse],
            "removeWarehouses": [remove_warehouse],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"
    assert {
        warehouse_data["slug"] for warehouse_data in channel_data["warehouses"]
    } == {warehouse.slug for warehouse in warehouses[1:] + [warehouse]}


def test_channel_update_mutation_duplicated_warehouses(
    permission_manage_channels,
    staff_api_client,
    channel_USD,
    warehouses,
    warehouse,
):
    # given
    channel_USD.warehouses.add(*warehouses)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    remove_warehouse = graphene.Node.to_global_id("Warehouse", warehouses[0].pk)
    add_warehouse = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "id": channel_id,
        "input": {
            "name": name,
            "slug": slug,
            "addWarehouses": [add_warehouse],
            "removeWarehouses": [remove_warehouse, add_warehouse],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["channel"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "warehouses"
    assert errors[0]["code"] == ChannelErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["warehouses"] == [add_warehouse]
