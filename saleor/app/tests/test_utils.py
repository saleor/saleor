from ...app.utils import get_active_tax_apps
from ...core.tests.test_taxes import app_factory, tax_app_factory  # noqa: F401
from ...webhook.event_types import WebhookEventSyncType


def test_get_active_tax_apps(app_factory, tax_app_factory):  # noqa: F811
    # given
    app = app_factory(
        name="app1",
        is_active=True,
        webhook_event_types=[],
        permissions=[],
    )
    tax_app1 = tax_app_factory(name="app2", is_active=True)
    tax_app2 = tax_app_factory(name="app3", is_active=False)

    # when
    tax_apps = get_active_tax_apps()

    # then
    assert len(tax_apps) == 1
    assert tax_app1 in tax_apps
    assert tax_app2 not in tax_apps
    assert app not in tax_apps


def test_get_active_tax_app_no_permission(tax_app_factory):  # noqa: F811
    # given
    tax_app_factory(
        name="app1",
        is_active=True,
        permissions=[],
    )

    # when
    tax_apps = get_active_tax_apps()

    # then
    assert len(tax_apps) == 0


def test_get_active_tax_app_only_one_webhook(tax_app_factory):  # noqa: F811
    # given
    tax_app_factory(
        name="app1",
        is_active=True,
        webhook_event_types=[WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES],
    )

    # when
    tax_apps = get_active_tax_apps()

    # then
    assert len(tax_apps) == 1
