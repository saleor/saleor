from unittest.mock import Mock, patch

import graphene

from .....app.models import App, AppInstallation
from .....app.tasks import install_app_task
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
    assert App.objects.count() == 0


def test_install_app_mutation_with_another_app_installed_but_marked_to_be_removed(
    permission_manage_apps,
    permission_manage_orders,
    staff_api_client,
    staff_user,
    monkeypatch,
    app_marked_to_be_removed,
):
    assert app_marked_to_be_removed.removed_at is not None
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
    assert App.objects.count() == 1


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


@patch("saleor.app.installation_utils.send_app_token", Mock())
@patch(
    "saleor.graphql.app.mutations.app_install.install_app_task.delay", install_app_task
)
def test_install_app_mutation_with_the_same_identifier_twice(
    permission_manage_apps,
    permission_manage_orders,
    staff_api_client,
    staff_user,
    monkeypatch,
    app,
):
    # given
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    variables = {
        "app_name": "New external integration",
        "manifest_url": app.manifest_url,
        "permissions": [PermissionEnum.MANAGE_ORDERS.name],
    }

    # when
    with patch("saleor.app.installation_utils.fetch_manifest") as mocked_fetch:
        mocked_fetch.return_value = {
            "id": app.identifier,
            "tokenTargetUrl": "http://localhost:3000/register",
            "name": "app",
            "version": "1.0.0",
        }
        data = _mutate_app_install(staff_api_client, variables)

    # then
    # Installation is done in celery task - response shows that app is being installed
    assert not data["errors"]
    assert data["appInstallation"]["status"] == JobStatus.PENDING.upper()
    assert data["appInstallation"]["manifestUrl"] == app.manifest_url
    assert App.objects.count() == 1
    # Celery bypassed, AppInstallation instance failed to install app
    app_installation = AppInstallation.objects.first()
    assert app_installation.status == JobStatus.FAILED
    assert app_installation.message == (
        "identifier: "
        "['App with the same identifier is already installed: Sample app objects']"
    )
