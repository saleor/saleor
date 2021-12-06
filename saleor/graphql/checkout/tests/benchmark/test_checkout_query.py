from unittest import mock

import graphene
import pytest

from .....webhook.event_types import WebhookEventType
from .....webhook.models import Webhook
from ....tests.utils import get_graphql_content

GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
            availableShippingMethods {
                id
                name
                active
            }
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
@mock.patch("saleor.plugins.webhook.utils.send_webhook_request_sync")
def test_fetch_checkout_available_shipping_methods_with_configured_webhooks(
    mocked_webhook,
    api_client,
    checkout_with_items,
    settings,
    address,
    shipping_method,
    app,
    permission_manage_checkouts,
    count_queries,
):
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    app.permissions.add(permission_manage_checkouts)

    webhook = Webhook.objects.create(
        name="payment-webhook-1",
        app=app,
        target_url="https://payment-gateway.com/api/",
    )
    webhook.events.create(event_type=WebhookEventType.CHECKOUT_FILTER_SHIPPING_METHODS)

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "Checkout contains dangerous products."
    mocked_webhook.return_value = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "1"),
                "reason": webhook_reason,
            }
        ]
    }

    variables = {"token": checkout.token}

    response = get_graphql_content(
        api_client.post_graphql(GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS, variables)
    )

    assert response["data"]["checkout"]["availableShippingMethods"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_fetch_checkout_available_shipping_methods_webhooks_not_configured(
    api_client,
    checkout_with_items,
    address,
    shipping_method,
    count_queries,
):
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    variables = {"token": checkout.token}

    response = get_graphql_content(
        api_client.post_graphql(GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS, variables)
    )

    assert response["data"]["checkout"]["availableShippingMethods"]
