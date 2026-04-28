import pytest

from saleor.account.models import Group
from saleor.app.migrations.tasks import saleor3_24
from saleor.app.migrations.tasks.saleor3_24 import (
    remove_manage_apps_permission_from_app_extensions_task,
    remove_manage_apps_permission_from_apps_task,
)
from saleor.app.models import App, AppExtension
from saleor.permission.models import Permission


def test_removes_manage_apps_permission_from_app(permission_manage_apps):
    # given
    app = App.objects.create(name="Test App", is_active=True)
    app.permissions.add(permission_manage_apps)

    # when
    remove_manage_apps_permission_from_apps_task()

    # then
    assert app.permissions.count() == 0


def test_keeps_other_permissions_when_removing_manage_apps_from_app(
    permission_manage_apps, permission_manage_products
):
    # given
    app = App.objects.create(name="Test App", is_active=True)
    app.permissions.add(permission_manage_apps, permission_manage_products)

    # when
    remove_manage_apps_permission_from_apps_task()

    # then
    remaining = list(app.permissions.all())
    assert remaining == [permission_manage_products]


def test_no_op_when_app_does_not_have_manage_apps(permission_manage_products):
    # given
    app = App.objects.create(name="Test App", is_active=True)
    app.permissions.add(permission_manage_products)

    # when
    remove_manage_apps_permission_from_apps_task()

    # then
    assert list(app.permissions.all()) == [permission_manage_products]


def test_removes_manage_apps_permission_from_app_extension(
    permission_manage_apps,
):
    # given
    app = App.objects.create(name="Test App", is_active=True)
    extension = AppExtension.objects.create(
        app=app,
        label="Extension",
        url="http://example.com/ext",
        mount="product_overview_create",
        target="popup",
    )
    extension.permissions.add(permission_manage_apps)

    # when
    remove_manage_apps_permission_from_app_extensions_task()

    # then
    assert extension.permissions.count() == 0


def test_does_not_remove_manage_apps_from_groups(
    permission_manage_apps,
):
    # given
    group = Group.objects.create(
        name="Staff group", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_apps)

    # when
    remove_manage_apps_permission_from_apps_task()
    remove_manage_apps_permission_from_app_extensions_task()

    # then
    assert list(group.permissions.all()) == [permission_manage_apps]


def test_keeps_manage_apps_permission_row_after_run(permission_manage_apps):
    # given
    app = App.objects.create(name="Test App", is_active=True)
    app.permissions.add(permission_manage_apps)

    # when
    remove_manage_apps_permission_from_apps_task()

    # then
    assert Permission.objects.filter(pk=permission_manage_apps.pk).exists()


def test_does_not_reschedule_when_batch_not_full(permission_manage_apps, mocker):
    # given
    app = App.objects.create(name="Test App", is_active=True)
    app.permissions.add(permission_manage_apps)
    delay_mock = mocker.patch.object(
        remove_manage_apps_permission_from_apps_task, "delay"
    )

    # when
    remove_manage_apps_permission_from_apps_task()

    # then
    delay_mock.assert_not_called()


def test_reschedules_when_batch_is_full(permission_manage_apps, mocker):
    # given
    mocker.patch.object(saleor3_24, "REMOVE_MANAGE_APPS_PERMISSION_BATCH_SIZE", 2)
    for i in range(2):
        app = App.objects.create(name=f"App {i}", is_active=True)
        app.permissions.add(permission_manage_apps)
    delay_mock = mocker.patch.object(
        remove_manage_apps_permission_from_apps_task, "delay"
    )

    # when
    remove_manage_apps_permission_from_apps_task()

    # then
    delay_mock.assert_called_once_with(current_depth=1, max_depth=10000)


def test_recursion_guard_raises(permission_manage_apps):
    # given
    app = App.objects.create(name="Test App", is_active=True)
    app.permissions.add(permission_manage_apps)

    # when / then
    with pytest.raises(RecursionError):
        remove_manage_apps_permission_from_apps_task(current_depth=11, max_depth=10)
