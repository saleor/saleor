import json
from unittest import mock

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

DELETE_SHIPPING_PRICE_MUTATION = """
    mutation deleteShippingPrice($id: ID!) {
        shippingPriceDelete(id: $id) {
            shippingZone {
                id
            }
            shippingMethod {
                id
            }
            errors {
                code
            }
        }
    }
"""


def test_delete_shipping_method(
    staff_api_client, shipping_method, permission_manage_shipping
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    shipping_zone_id = graphene.Node.to_global_id(
        "ShippingZone", shipping_method.shipping_zone.pk
    )
    variables = {"id": shipping_method_id}

    # when
    response = staff_api_client.post_graphql(
        DELETE_SHIPPING_PRICE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["shippingPriceDelete"]
    assert data["shippingMethod"]["id"] == shipping_method_id
    assert data["shippingZone"]["id"] == shipping_zone_id


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_shipping_method_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )

    # when
    response = staff_api_client.post_graphql(
        DELETE_SHIPPING_PRICE_MUTATION,
        {"id": shipping_method_id},
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["shippingPriceDelete"]
    assert not data["errors"]

    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": shipping_method_id,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.SHIPPING_PRICE_DELETED,
        [any_webhook],
        shipping_method,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )
