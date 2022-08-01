import pytest

from ...app.models import App
from ...plugins.webhook.utils import get_current_tax_app
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...webhook.models import Webhook, WebhookEvent
from ..permissions import (
    CheckoutPermissions,
    OrderPermissions,
    get_permissions_from_codenames,
)


@pytest.fixture
def app_factory():
    def factory(name, is_active, webhook_event_types, permissions):
        app = App.objects.create(name=name, is_active=is_active)
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


def test_get_current_tax_app(tax_app):
    assert tax_app == get_current_tax_app()


def test_get_current_tax_app_multiple_apps(app_factory, tax_app_factory):
    # given
    tax_app_factory(
        name="A Tax App",
    )
    tax_app_factory(
        name="Z Tax App",
    )
    expected_app = tax_app_factory(
        name="Tax App",
    )
    app_factory(
        name="Non Tax App",
        is_active=True,
        webhook_event_types=[
            WebhookEventAsyncType.ORDER_UPDATED,
        ],
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
    )
    tax_app_factory(name="Unauthorized Tax App", permissions=[])
    tax_app_factory(
        name="Partial Tax App 2",
        webhook_event_types=[
            WebhookEventSyncType.ORDER_CALCULATE_TAXES,
        ],
    )
    tax_app_factory(
        name="Partial Tax App 1",
        webhook_event_types=[
            WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        ],
    )
    tax_app_factory(
        name="Inactive Tax App",
        is_active=False,
    )

    # when
    app = get_current_tax_app()

    # then
    assert expected_app == app


def test_get_current_tax_app_no_app():
    assert get_current_tax_app() is None
