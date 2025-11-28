from django.apps import apps as django_apps

from saleor.app.migration_utils import (
    fill_settings_json,
    migrate_mount_enum_upper_string,
    migrate_target_enum_upper_string,
)
from saleor.app.models import App, AppExtension


def test_migrate_target_enum_upper_string():
    app = App.objects.create(name="Test App", is_active=True)

    # Create extensions with lowercase target values
    extension1 = AppExtension.objects.create(
        app=app,
        label="Test Extension 1",
        url="http://example.com/ext1",
        mount="product_overview_create",
        target="popup",
    )
    extension2 = AppExtension.objects.create(
        app=app,
        label="Test Extension 2",
        url="http://example.com/ext2",
        mount="product_details_more_actions",
        target="app_page",
    )
    extension3 = AppExtension.objects.create(
        app=app,
        label="Test Extension 3",
        url="http://example.com/ext3",
        mount="order_overview_create",
        target="widget",
    )

    migrate_target_enum_upper_string(django_apps, None)

    # then
    extension1.refresh_from_db()
    extension2.refresh_from_db()
    extension3.refresh_from_db()

    assert extension1.target == "POPUP"
    assert extension2.target == "APP_PAGE"
    assert extension3.target == "WIDGET"


def test_migrate_mount_enum_upper_string():
    # given
    app = App.objects.create(name="Test App", is_active=True)

    # Create extensions with lowercase mount values
    extension1 = AppExtension.objects.create(
        app=app,
        label="Test Extension 1",
        url="http://example.com/ext1",
        mount="product_overview_create",
        target="popup",
    )
    extension2 = AppExtension.objects.create(
        app=app,
        label="Test Extension 2",
        url="http://example.com/ext2",
        mount="order_details_more_actions",
        target="popup",
    )
    extension3 = AppExtension.objects.create(
        app=app,
        label="Test Extension 3",
        url="http://example.com/ext3",
        mount="customer_overview_more_actions",
        target="popup",
    )

    # when
    # Run migration
    migrate_mount_enum_upper_string(django_apps, None)

    # then
    extension1.refresh_from_db()
    extension2.refresh_from_db()
    extension3.refresh_from_db()

    assert extension1.mount == "PRODUCT_OVERVIEW_CREATE"
    assert extension2.mount == "ORDER_DETAILS_MORE_ACTIONS"
    assert extension3.mount == "CUSTOMER_OVERVIEW_MORE_ACTIONS"


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
    fill_settings_json(django_apps, None)

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
    fill_settings_json(django_apps, None)

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
    fill_settings_json(django_apps, None)

    # then
    extension.refresh_from_db()

    # Settings should remain unchanged for non-widget/non-new_tab targets
    assert extension.settings == {"original": "settings"}


def test_migration_handles_large_batch():
    # given
    app = App.objects.create(name="Test App", is_active=True)

    # Create 150 extensions (more than BATCH_SIZE of 100)
    extensions = []
    for i in range(150):
        target = "widget" if i % 2 == 0 else "new_tab"
        extensions.append(
            AppExtension(
                app=app,
                label=f"Extension {i}",
                url=f"http://example.com/ext{i}",
                mount="product_overview_create",
                target=target,
                http_target_method="POST",
                settings={},
            )
        )

    AppExtension.objects.bulk_create(extensions)

    # when
    # Run migrations
    migrate_target_enum_upper_string(django_apps, None)
    migrate_mount_enum_upper_string(django_apps, None)
    fill_settings_json(django_apps, None)

    # then
    # Verify all extensions were migrated
    widget_extensions = AppExtension.objects.filter(target="WIDGET")
    new_tab_extensions = AppExtension.objects.filter(target="NEW_TAB")

    assert widget_extensions.count() == 75
    assert new_tab_extensions.count() == 75

    # Check that settings were properly migrated
    for ext in widget_extensions:
        assert ext.settings == {"widgetTarget": {"method": "POST"}}

    for ext in new_tab_extensions:
        assert ext.settings == {"newTabTarget": {"method": "POST"}}


def test_migration_all_operations_together():
    # given
    app = App.objects.create(name="Test App", is_active=True)

    # Create extension that will be affected by all three migration operations
    extension = AppExtension.objects.create(
        app=app,
        label="Complete Migration Test",
        url="http://example.com/complete",
        mount="product_details_widgets",
        target="widget",
        http_target_method="GET",
        settings={},
    )

    # when
    # Run all migrations
    migrate_target_enum_upper_string(django_apps, None)
    migrate_mount_enum_upper_string(django_apps, None)
    fill_settings_json(django_apps, None)

    # then
    extension.refresh_from_db()

    # Verify all three migrations were applied:
    # 1. Target converted to uppercase
    assert extension.target == "WIDGET"
    # 2. Mount converted to uppercase
    assert extension.mount == "PRODUCT_DETAILS_WIDGETS"
    # 3. Settings filled based on target and http_target_method
    assert extension.settings == {"widgetTarget": {"method": "GET"}}
