import pytest

from .....app.models import App
from .....app.types import AppType
from .....graphql.core.utils import to_global_id_or_none
from .....webhook.event_types import WebhookEventSyncType
from .....webhook.models import Webhook, WebhookEvent
from .....webhook.tests.subscription_webhooks import subscription_queries


@pytest.fixture
def tax_app(db, permission_handle_taxes):
    app = App.objects.create(name="Tax App", is_active=True)
    app.identifier = to_global_id_or_none(app)
    app.save()
    app.permissions.add(permission_handle_taxes)

    webhook = Webhook.objects.create(
        name="tax-webhook-1",
        app=app,
        target_url="https://tax-app.com/api/",
        subscription_query=subscription_queries.CALCULATE_TAXES_SUBSCRIPTION_QUERY,
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in [
                WebhookEventSyncType.ORDER_CALCULATE_TAXES,
                WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
            ]
        ]
    )
    return app


@pytest.fixture
def external_tax_app(db, permission_handle_taxes):
    app = App.objects.create(
        name="External App",
        is_active=True,
        type=AppType.THIRDPARTY,
        identifier="mirumee.app.simple.tax",
        about_app="About app text.",
        data_privacy="Data privacy text.",
        data_privacy_url="http://www.example.com/privacy/",
        homepage_url="http://www.example.com/homepage/",
        support_url="http://www.example.com/support/contact/",
        configuration_url="http://www.example.com/app-configuration/",
        app_url="http://www.example.com/app/",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_handle_taxes)

    webhook = Webhook.objects.create(
        name="external-tax-webhook-1",
        app=app,
        target_url="https://tax-app.example.com/api/",
        subscription_query=subscription_queries.CALCULATE_TAXES_SUBSCRIPTION_QUERY,
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in [
                WebhookEventSyncType.ORDER_CALCULATE_TAXES,
                WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
            ]
        ]
    )
    return app


@pytest.fixture
def tax_app_with_subscription_webhooks(db, permission_handle_taxes):
    app = App.objects.create(name="Tax App with subscription", is_active=True)
    app.permissions.add(permission_handle_taxes)

    webhook = Webhook.objects.create(
        name="tax-subscription-webhook-1",
        app=app,
        target_url="https://tax-app.com/api/",
        subscription_query=subscription_queries.CALCULATE_TAXES_SUBSCRIPTION_QUERY,
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in [
                WebhookEventSyncType.ORDER_CALCULATE_TAXES,
                WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
            ]
        ]
    )
    return app
