import graphene
import pytest

from ...app.models import App
from ...permission.enums import (
    CheckoutPermissions,
    get_permissions_from_codenames,
)
from ...webhook.event_types import WebhookEventSyncType
from ...webhook.models import Webhook, WebhookEvent


@pytest.fixture
def app_factory():
    def factory(name, is_active, webhook_event_types, permissions):
        app = App.objects.create(name=name, is_active=is_active)
        app.identifier = graphene.Node.to_global_id("App", app.pk)
        app.save()
        webhook = Webhook.objects.create(
            name=f"{name} Webhook",
            app=app,
            target_url="https://test.webhook.url",
        )
        for event_type in webhook_event_types:
            WebhookEvent.objects.create(
                webhook=webhook,
                event_type=event_type,
            )
        app.permissions.add(
            *get_permissions_from_codenames([p.codename for p in permissions])
        )
        return app

    return factory


@pytest.fixture
def tax_app_factory(app_factory):
    def factory(name, is_active=True, webhook_event_types=None, permissions=None):
        if webhook_event_types is None:
            webhook_event_types = [
                WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
                WebhookEventSyncType.ORDER_CALCULATE_TAXES,
            ]
        if permissions is None:
            permissions = [CheckoutPermissions.HANDLE_TAXES]
        return app_factory(
            name=name,
            is_active=is_active,
            webhook_event_types=webhook_event_types,
            permissions=permissions,
        )

    return factory


@pytest.fixture
def tax_app(tax_app_factory):
    return tax_app_factory(
        name="Tax App",
        is_active=True,
    )
