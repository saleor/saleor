from unittest.mock import Mock

import graphene

from .....app.models import AppInstallation
from .....core import JobStatus
from ....core.enums import AppErrorCode, PermissionEnum
from ....tests.utils import get_graphql_content

INSTALL_APP_MUTATION = """
    mutation AppInstall(
        $app_name: String, $manifest_url: String, $permissions: [PermissionEnum!]){
        appInstall(
            input:{appName: $app_name, manifestUrl: $manifest_url,
                permissions:$permissions}){
            appInstallation{
                id
                status
                appName
                manifestUrl
            }
            errors{
                field
                message
                code
                permissions
            }
        }
    }
"""


def _mutate_app_install(client, variables, ignore_errors=False):
    response = client.post_graphql(INSTALL_APP_MUTATION, variables)
    content = get_graphql_content(response, ignore_errors=True)
    return content["data"]["appInstall"]


def test_install_app_mutation(
    permission_manage_apps,
    permission_manage_orders,
    staff_api_client,
    staff_user,
    monkeypatch,
):
    # given
    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_install.install_app_task.delay", mocked_task
    )
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    variables = {
        "app_name": "New external integration",
        "manifest_url": "http://localhost:3000/manifest",
        "permissions": [PermissionEnum.MANAGE_ORDERS.name],
    }
    # when
    data = _mutate_app_install(staff_api_client, variables)

    # then
    app_installation = AppInstallation.objects.get()
    app_installation_data = data["appInstallation"]
    _, app_id = graphene.Node.from_global_id(app_installation_data["id"])
    assert int(app_id) == app_installation.id
    assert app_installation_data["status"] == JobStatus.PENDING.upper()
    assert app_installation_data["manifestUrl"] == app_installation.manifest_url
    mocked_task.assert_called_with(app_installation.pk, True)
    assert app_installation.uuid is not None


def test_app_is_not_allowed_to_install_app(
    permission_manage_apps, permission_manage_orders, app_api_client, monkeypatch
):
    # given
    app_api_client.app.permissions.set(
        [permission_manage_apps, permission_manage_orders]
    )
    variables = {
        "app_name": "New external integration",
        "manifest_url": "http://localhost:3000/manifest",
        "permissions": [PermissionEnum.MANAGE_ORDERS.name],
    }

    # when
    data = _mutate_app_install(app_api_client, variables)

    # then
    assert data is None


def test_app_install_mutation_out_of_scope_permissions(
    permission_manage_apps, staff_api_client, staff_user
):
    # given
    staff_user.user_permissions.set([permission_manage_apps])
    variables = {
        "app_name": "New external integration",
        "manifest_url": "http://localhost:3000/manifest",
        "permissions": [PermissionEnum.MANAGE_ORDERS.name],
    }
    # when
    data = _mutate_app_install(staff_api_client, variables)

    # then
    errors = data["errors"]
    assert not data["appInstallation"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert error["permissions"] == [PermissionEnum.MANAGE_ORDERS.name]


def test_install_app_mutation_with_the_same_manifest_twice(
    permission_manage_apps,
    permission_manage_orders,
    staff_api_client,
    staff_user,
    monkeypatch,
    app,
):
    # given
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_install.install_app_task.delay", Mock()
    )
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    variables = {
        "app_name": "New external integration",
        "manifest_url": app.manifest_url,
        "permissions": [PermissionEnum.MANAGE_ORDERS.name],
    }

    # when
    data = _mutate_app_install(staff_api_client, variables)

    # then
    errors = data["errors"]
    assert not data["appInstallation"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "manifestUrl"
    assert error["code"] == "INVALID"
    assert error["message"] == (
        f"App with the same manifest_url is already installed: {app.name}"
    )
