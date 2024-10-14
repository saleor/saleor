import pytest
from django.utils import timezone

from ....app.models import App
from ....app.types import AppType


@pytest.fixture
def app(db):
    app = App.objects.create(
        name="Sample app objects",
        is_active=True,
        identifier="saleor.app.test",
        manifest_url="http://localhost:3000/manifest",
    )
    return app


@pytest.fixture
def app_marked_to_be_removed(db):
    app = App.objects.create(
        name="Sample app objects",
        is_active=True,
        identifier="saleor.app.test",
        manifest_url="http://localhost:3000/manifest",
        removed_at=timezone.now(),
    )
    return app


@pytest.fixture
def webhook_app(
    db,
    permission_manage_shipping,
    permission_manage_gift_card,
    permission_manage_discounts,
    permission_manage_menus,
    permission_manage_products,
    permission_manage_staff,
    permission_manage_orders,
    permission_manage_users,
):
    app = App.objects.create(name="Webhook app", is_active=True)
    app.permissions.add(permission_manage_shipping)
    app.permissions.add(permission_manage_gift_card)
    app.permissions.add(permission_manage_discounts)
    app.permissions.add(permission_manage_menus)
    app.permissions.add(permission_manage_products)
    app.permissions.add(permission_manage_staff)
    app.permissions.add(permission_manage_orders)
    app.permissions.add(permission_manage_users)
    return app


@pytest.fixture
def app_with_token(db):
    app = App.objects.create(name="Sample app objects", is_active=True)
    app.tokens.create(name="Test")
    return app


@pytest.fixture
def removed_app(db):
    app = App.objects.create(
        name="Deleted app ",
        is_active=True,
        removed_at=(timezone.now() - timezone.timedelta(days=1, hours=1)),
    )
    return app


@pytest.fixture
def external_app(db):
    app = App.objects.create(
        name="External App",
        is_active=True,
        type=AppType.THIRDPARTY,
        identifier="mirumee.app.sample",
        about_app="About app text.",
        data_privacy="Data privacy text.",
        data_privacy_url="http://www.example.com/privacy/",
        homepage_url="http://www.example.com/homepage/",
        support_url="http://www.example.com/support/contact/",
        configuration_url="http://www.example.com/app-configuration/",
        app_url="http://www.example.com/app/",
    )
    app.tokens.create(name="Default")
    return app


@pytest.fixture
def apps_without_webhooks(db):
    return App.objects.bulk_create(
        [
            App(name="App1", is_active=True),
            App(name="App2", is_active=False),
            App(name="App3", is_active=True),
            App(name="App4", is_active=False),
        ]
    )
