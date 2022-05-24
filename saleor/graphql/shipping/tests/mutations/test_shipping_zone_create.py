from unittest import mock

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....shipping.error_codes import ShippingErrorCode
from .....shipping.models import ShippingZone
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

CREATE_SHIPPING_ZONE_MUTATION = """
    mutation createShipping(
        $name: String
        $description: String
        $default: Boolean
        $countries: [String!]
        $addWarehouses: [ID!]
        $addChannels: [ID!]
    ) {
        shippingZoneCreate(
            input: {
                name: $name
                description: $description
                countries: $countries
                default: $default
                addWarehouses: $addWarehouses
                addChannels: $addChannels
            }
        ) {
            errors {
                field
                code
                message
                channels
            }
            shippingZone {
                id
                name
                description
                countries {
                    code
                }
                default
                warehouses {
                    name
                }
                channels {
                    id
                }
            }
        }
    }
"""


def test_create_shipping_zone(
    staff_api_client, warehouse, permission_manage_shipping, channel_PLN
):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.pk)
    variables = {
        "name": "test shipping",
        "description": "test description",
        "countries": ["PL"],
        "addWarehouses": [warehouse_id],
        "addChannels": [channel_id],
    }
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneCreate"]
    zone = data["shippingZone"]
    assert not data["errors"]
    assert zone["name"] == "test shipping"
    assert zone["description"] == "test description"
    assert zone["countries"] == [{"code": "PL"}]
    assert len(zone["warehouses"]) == 1
    assert zone["warehouses"][0]["name"] == warehouse.name
    assert len(zone["channels"]) == 1
    assert zone["channels"][0]["id"] == channel_id
    assert zone["default"] is False


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_shipping_zone_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_shipping,
    warehouse,
    channel_USD,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    variables = {
        "name": "Shipping Zone Name",
        "description": "Shipping Zone Description",
        "countries": ["PL"],
        "addWarehouses": [warehouse_id],
        "addChannels": [channel_id],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    shipping_zone = ShippingZone.objects.last()
    data = content["data"]["shippingZoneCreate"]

    # then
    assert shipping_zone
    assert data["errors"] == []

    mocked_webhook_trigger.assert_called_once_with(
        {
            "id": data["shippingZone"]["id"],
            "meta": generate_meta(
                requestor_data=generate_requestor(
                    SimpleLazyObject(lambda: staff_api_client.user)
                )
            ),
        },
        WebhookEventAsyncType.SHIPPING_ZONE_CREATED,
        [any_webhook],
        shipping_zone,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_create_shipping_zone_with_empty_warehouses(
    staff_api_client, permission_manage_shipping
):
    variables = {
        "name": "test shipping",
        "countries": ["PL"],
        "addWarehouses": [],
    }
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneCreate"]
    assert not data["errors"]
    zone = data["shippingZone"]
    assert zone["name"] == "test shipping"
    assert zone["countries"] == [{"code": "PL"}]
    assert not zone["warehouses"]
    assert zone["default"] is False


def test_create_shipping_zone_without_warehouses_and_channels(
    staff_api_client, permission_manage_shipping
):
    variables = {
        "name": "test shipping",
        "countries": ["PL"],
    }
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneCreate"]
    assert not data["errors"]
    zone = data["shippingZone"]
    assert zone["name"] == "test shipping"
    assert zone["countries"] == [{"code": "PL"}]
    assert not zone["warehouses"]
    assert zone["default"] is False


TEST_COUNTRIES_LIST = ["DZ", "AX", "BY"]


@mock.patch(
    "saleor.graphql.shipping.mutations.shippings.get_countries_without_shipping_zone",
    return_value=TEST_COUNTRIES_LIST,
)
def test_create_default_shipping_zone(
    _, staff_api_client, warehouse, permission_manage_shipping
):
    unassigned_countries = TEST_COUNTRIES_LIST
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "default": True,
        "name": "test shipping",
        "countries": ["PL"],
        "addWarehouses": [warehouse_id],
    }
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    expected_countries = set(unassigned_countries + variables["countries"])
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneCreate"]
    assert not data["errors"]
    zone = data["shippingZone"]
    assert zone["name"] == "test shipping"
    assert zone["warehouses"][0]["name"] == warehouse.name
    assert zone["default"] is True
    zone_countries = {c["code"] for c in zone["countries"]}
    assert zone_countries == expected_countries


def test_create_duplicated_default_shipping_zone(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    shipping_zone.default = True
    shipping_zone.save()

    variables = {
        "default": True,
        "name": "test shipping",
        "countries": ["PL"],
        "addChannels": [],
    }
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneCreate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "default"
    assert data["errors"][0]["code"] == ShippingErrorCode.ALREADY_EXISTS.name
