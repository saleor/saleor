import pytest
from django.db import connection

from saleor.app.migrations.tasks.saleor3_23 import (
    fill_app_extension_settings_task,
)
from saleor.app.models import App, AppExtension


def set_legacy_http_target_method(extension: AppExtension, method: str) -> None:
    """Write the column the 3.24 model state no longer knows about."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE app_appextension SET http_target_method = %s WHERE id = %s",
            [method, extension.pk],
        )


@pytest.fixture
def app_with_extensions():
    return App.objects.create(name="Test App", is_active=True)


def test_skip_settings_if_filled(app_with_extensions):
    # given
    existing_settings = {"some": "data"}
    extension = AppExtension.objects.create(
        app=app_with_extensions,
        label="Widget Extension",
        url="http://example.com/widget",
        mount="product_details_widgets",
        target="widget",
        settings=existing_settings,
    )
    set_legacy_http_target_method(extension, "POST")

    # when
    fill_app_extension_settings_task()

    # then
    extension.refresh_from_db(fields=("settings",))
    assert extension.settings == existing_settings


@pytest.mark.parametrize(
    ("_case", "target", "method", "expected_settings"),
    [
        (
            "new_tab target keeps its method",
            "new_tab",
            "GET",
            {"newTabTarget": {"method": "GET"}},
        ),
        (
            "widget target keeps its method",
            "widget",
            "POST",
            {"widgetTarget": {"method": "POST"}},
        ),
    ],
)
def test_fill_settings_json(
    _case, target, method, expected_settings, app_with_extensions
):
    # given
    extension = AppExtension.objects.create(
        app=app_with_extensions,
        label="Extension",
        url="http://example.com/extension",
        mount="product_overview_create",
        target=target,
        settings={},
    )
    set_legacy_http_target_method(extension, method)

    # when
    fill_app_extension_settings_task()

    # then
    extension.refresh_from_db(fields=("settings",))
    assert extension.settings == expected_settings


def test_fill_settings_json_skips_non_widget_non_new_tab_targets(app_with_extensions):
    # given
    existing_settings = {"original": "settings"}
    extension = AppExtension.objects.create(
        app=app_with_extensions,
        label="Popup Extension",
        url="http://example.com/popup",
        mount="product_overview_create",
        target="popup",
        settings=existing_settings,
    )
    set_legacy_http_target_method(extension, "GET")

    # when
    fill_app_extension_settings_task()

    # then
    extension.refresh_from_db(fields=("settings",))
    assert extension.settings == existing_settings
