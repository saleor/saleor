from saleor.app.migrations.tasks.saleor3_23 import (
    fill_app_extension_settings_task,
)
from saleor.app.models import App, AppExtension


def test_skip_settings_if_filled():
    # given
    app = App.objects.create(name="Test App", is_active=True)

    extension = AppExtension.objects.create(
        app=app,
        label="Widget Extension",
        url="http://example.com/widget",
        mount="product_details_widgets",
        target="widget",
        http_target_method="POST",
        settings={"some": "data"},
    )

    # when
    # Run migration
    fill_app_extension_settings_task()

    # then
    extension.refresh_from_db()

    # Non empty should be ignored
    assert extension.settings == {"some": "data"}


def test_fill_settings_json_for_new_tab_target():
    # given
    app = App.objects.create(name="Test App", is_active=True)

    # Create new_tab extension with http_target_method
    extension = AppExtension.objects.create(
        app=app,
        label="New Tab Extension",
        url="http://example.com/newtab",
        mount="product_overview_create",
        target="new_tab",
        http_target_method="GET",
        settings={},
    )

    # when
    fill_app_extension_settings_task()

    # then
    extension.refresh_from_db()

    assert extension.settings == {"newTabTarget": {"method": "GET"}}


def test_fill_settings_json_skips_non_widget_non_new_tab_targets():
    # given
    app = App.objects.create(name="Test App", is_active=True)

    # Create popup extension
    extension = AppExtension.objects.create(
        app=app,
        label="Popup Extension",
        url="http://example.com/popup",
        mount="product_overview_create",
        target="popup",
        http_target_method="GET",
        settings={"original": "settings"},
    )

    # when
    # Run migration
    fill_app_extension_settings_task()

    # then
    extension.refresh_from_db()

    # Settings should remain unchanged for non-widget/non-new_tab targets
    assert extension.settings == {"original": "settings"}
