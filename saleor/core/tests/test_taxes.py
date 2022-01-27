from unittest.mock import Mock, patch

import pytest

from ...app.models import App
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...webhook.models import Webhook, WebhookEvent
from ..permissions import (
    CheckoutPermissions,
    OrderPermissions,
    get_permissions_from_codenames,
)
from ..taxes import (
    DEFAULT_TAX_CODE,
    DEFAULT_TAX_DESCRIPTION,
    WEBHOOK_TAX_CODES_CACHE_KEY,
    TaxType,
    _get_cached_tax_codes_or_fetch,
    _get_current_tax_app,
    fetch_tax_types,
    get_tax_type,
    set_tax_code,
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
    assert tax_app == _get_current_tax_app()


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
    app = _get_current_tax_app()

    # then
    assert expected_app == app


def test_get_current_tax_app_no_app():
    assert _get_current_tax_app() is None


@pytest.fixture
def tax_type():
    return TaxType(
        code="code",
        description="description",
    )


@pytest.fixture
def tax_types(tax_type):
    return [tax_type]


@patch("saleor.core.taxes.cache")
def test_get_cached_tax_codes_or_fetch(mocked_cache, tax_types):
    # given
    mocked_cache.get = Mock(return_value=tax_types)

    # when
    fetched_tax_types = _get_cached_tax_codes_or_fetch(Mock())

    # then
    assert fetched_tax_types == tax_types


@patch("saleor.core.taxes.cache")
def test_get_cached_tax_codes_or_fetch_cache_miss(mocked_cache, tax_types):
    # given
    mocked_cache_set = Mock()
    mocked_cache.get = Mock(return_value=None)
    mocked_cache.set = mocked_cache_set
    manager = Mock(get_tax_codes=Mock(return_value=tax_types))

    # when
    fetched_tax_types = _get_cached_tax_codes_or_fetch(manager)

    # then
    assert fetched_tax_types == tax_types
    mocked_cache_set.assert_called_once_with(WEBHOOK_TAX_CODES_CACHE_KEY, tax_types)


def test_get_cached_tax_codes_or_fetch_empty_response():
    # given
    manager = Mock(get_tax_codes=Mock(return_value=None))

    # when
    fetched_tax_types = _get_cached_tax_codes_or_fetch(manager)

    # then
    assert fetched_tax_types == []


@patch("saleor.core.taxes._get_cached_tax_codes_or_fetch")
def test_set_tax_code(mocked_function, tax_app, tax_types, tax_type, product):
    # given
    mocked_function.return_value = tax_types

    # when
    set_tax_code(Mock(), product, tax_type.code)

    # then
    assert product.metadata == {
        f"{tax_app.name}.code": tax_type.code,
        f"{tax_app.name}.description": tax_type.description,
    }


def test_set_tax_code_delete(tax_app, product, tax_types, tax_type):
    # given
    product.metadata = {
        f"{tax_app.name}.code": tax_type.code,
        f"{tax_app.name}.description": tax_type.description,
    }

    # when
    set_tax_code(Mock(), product, None)

    # then
    assert product.metadata == {}


@patch("saleor.core.taxes._get_cached_tax_codes_or_fetch")
def test_set_tax_code_no_tax_types(mocked_function, tax_app, tax_types, product):
    # given
    mocked_function.return_value = None

    # when
    set_tax_code(Mock(), product, tax_types[0].code)

    # then
    assert product.metadata == {}


@patch("saleor.core.taxes._get_cached_tax_codes_or_fetch")
def test_set_tax_code_wrong_code(mocked_function, tax_app, tax_types, product):
    # given
    mocked_function.return_value = tax_types

    # when
    set_tax_code(Mock(), product, "wrong code")

    # then
    assert product.metadata == {}


def test_set_tax_code_old_method(product):
    # given
    mocked_assign_tax_code_to_object_meta = Mock()
    manager = Mock(assign_tax_code_to_object_meta=mocked_assign_tax_code_to_object_meta)
    tax_code = "tax code"

    # when
    set_tax_code(manager, product, tax_code)

    # then
    mocked_assign_tax_code_to_object_meta.assert_called_once_with(product, tax_code)


def test_get_tax_code(tax_app, product, tax_type):
    # given
    product.metadata = {
        f"{tax_app.name}.code": tax_type.code,
        f"{tax_app.name}.description": tax_type.description,
    }

    # when
    fetched_tax_type = get_tax_type(Mock(), product)

    # then
    assert fetched_tax_type == tax_type


def test_get_tax_code_defaults(tax_app, product):
    # when
    fetched_tax_type = get_tax_type(Mock(), product)

    # then
    assert fetched_tax_type == TaxType(
        code=DEFAULT_TAX_CODE,
        description=DEFAULT_TAX_DESCRIPTION,
    )


def test_get_tax_code_old_method(product, tax_type):
    # given
    mocked_get_tax_code_from_object_meta = Mock(return_value=tax_type)
    manager = Mock(get_tax_code_from_object_meta=mocked_get_tax_code_from_object_meta)

    # when
    fetched_tax_type = get_tax_type(manager, product)

    # then
    assert fetched_tax_type == tax_type
    mocked_get_tax_code_from_object_meta.assert_called_once_with(product)


@patch("saleor.core.taxes._get_cached_tax_codes_or_fetch")
def test_fetch_tax_types(mocked_get_cached_tax_codes_or_fetch, tax_types):
    # given
    mocked_get_cached_tax_codes_or_fetch.return_value = tax_types
    manager = Mock(get_tax_rate_type_choices=Mock(return_value=Mock()))

    # when
    expected_tax_types = fetch_tax_types(manager)

    # then
    assert tax_types == expected_tax_types


@patch("saleor.core.taxes._get_cached_tax_codes_or_fetch")
def test_fetch_tax_types_old_method(mocked_get_cached_tax_codes_or_fetch, tax_types):
    # given
    mocked_get_cached_tax_codes_or_fetch.return_value = []
    manager = Mock(get_tax_rate_type_choices=Mock(return_value=tax_types))

    # when
    expected_tax_types = fetch_tax_types(manager)

    # then
    assert tax_types == expected_tax_types
