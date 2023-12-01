from unittest import mock

import graphene
import pytest

from .....shipping.models import ShippingMethod, ShippingZone
from ....tests.utils import get_graphql_content


@pytest.fixture
def shipping_method_list(shipping_zone):
    shipping_method_1 = ShippingMethod.objects.create(
        shipping_zone=shipping_zone, name="DHL"
    )
    shipping_method_2 = ShippingMethod.objects.create(
        shipping_zone=shipping_zone, name="DPD"
    )
    shipping_method_3 = ShippingMethod.objects.create(
        shipping_zone=shipping_zone, name="GLS"
    )
    return shipping_method_1, shipping_method_2, shipping_method_3


BULK_DELETE_SHIPPING_PRICE_MUTATION = """
    mutation shippingPriceBulkDelete($ids: [ID!]!) {
        shippingPriceBulkDelete(ids: $ids) {
            count
        }
    }
"""


@pytest.fixture
def shipping_zone_list():
    shipping_zone_1 = ShippingZone.objects.create(name="Europe")
    shipping_zone_2 = ShippingZone.objects.create(name="Asia")
    shipping_zone_3 = ShippingZone.objects.create(name="Oceania")
    return shipping_zone_1, shipping_zone_2, shipping_zone_3


def test_delete_shipping_methods(
    staff_api_client, shipping_method_list, permission_manage_shipping
):
    # given
    variables = {
        "ids": [
            graphene.Node.to_global_id("ShippingMethodType", method.id)
            for method in shipping_method_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        BULK_DELETE_SHIPPING_PRICE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["shippingPriceBulkDelete"]["count"] == 3
    assert not ShippingMethod.objects.filter(
        id__in=[method.id for method in shipping_method_list]
    ).exists()


@mock.patch(
    "saleor.graphql.shipping.bulk_mutations."
    "shipping_price_bulk_delete.get_webhooks_for_event"
)
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_shipping_methods_trigger_multiple_webhook_events(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    shipping_method_list,
    permission_manage_shipping,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "ids": [
            graphene.Node.to_global_id("ShippingMethodType", method.id)
            for method in shipping_method_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        BULK_DELETE_SHIPPING_PRICE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["shippingPriceBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.call_count == len(shipping_method_list)


BULK_DELETE_SHIPPING_ZONE_MUTATION = """
    mutation shippingZoneBulkDelete($ids: [ID!]!) {
        shippingZoneBulkDelete(ids: $ids) {
            count
        }
    }
"""


def test_delete_shipping_zones(
    staff_api_client, shipping_zone_list, permission_manage_shipping
):
    # given
    variables = {
        "ids": [
            graphene.Node.to_global_id("ShippingZone", zone.id)
            for zone in shipping_zone_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        BULK_DELETE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["shippingZoneBulkDelete"]["count"] == 3
    assert not ShippingZone.objects.filter(
        id__in=[zone.id for zone in shipping_zone_list]
    ).exists()


@mock.patch(
    "saleor.graphql.shipping.bulk_mutations."
    "shipping_zone_bulk_delete.get_webhooks_for_event"
)
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_shipping_zones_trigger_multiple_webhook_events(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    shipping_zone_list,
    permission_manage_shipping,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "ids": [
            graphene.Node.to_global_id("ShippingZone", zone.id)
            for zone in shipping_zone_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        BULK_DELETE_SHIPPING_ZONE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["shippingZoneBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.call_count == len(shipping_zone_list)
