import pytest

from .....app.models import App
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .....webhook.models import Webhook, WebhookEvent


@pytest.fixture
def shipping_app(db, permission_manage_shipping):
    app = App.objects.create(name="Shipping App", is_active=True)
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_shipping)

    webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=app,
        target_url="https://shipping-app.com/api/",
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in [
                WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                WebhookEventAsyncType.FULFILLMENT_CREATED,
            ]
        ]
    )
    return app


@pytest.fixture
def shipping_app_with_subscription(db, permission_manage_shipping):
    app = App.objects.create(name="Shipping App with subscription", is_active=True)
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_shipping)

    webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=app,
        target_url="https://shipping-app.com/api/",
        subscription_query="""
        subscription {
  event {
    ... on ShippingListMethodsForCheckout {
      __typename
    }
  }
}

        """,
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in [
                WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                WebhookEventAsyncType.FULFILLMENT_CREATED,
            ]
        ]
    )
    return app
