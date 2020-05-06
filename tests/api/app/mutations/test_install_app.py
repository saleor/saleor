from unittest.mock import Mock

from saleor.app.models import AppJob
from saleor.core import JobStatus
from saleor.graphql.core.enums import AppErrorCode, PermissionEnum

from ...utils import get_graphql_content

INSTALL_APP_MUTATION = """
    mutation InstallApp(
        $name: String, $manifest_url: String, $permissions: [PermissionEnum]){
        installApp(
            input:{name: $name, manifestUrl: $manifest_url, permissions:$permissions}){
            appJob{
                id
                status
                name
                manifestUrl
            }
            appErrors{
                field
                message
                code
                permissions
            }
        }
    }
"""


def test_install_app_mutation(
    permission_manage_apps,
    permission_manage_orders,
    staff_api_client,
    staff_user,
    monkeypatch,
):
    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.install_app_task.delay", mocked_task
    )
    query = INSTALL_APP_MUTATION
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    variables = {
        "name": "New external integration",
        "manifest_url": "http://localhost:3000/manifest",
        "permissions": [PermissionEnum.MANAGE_ORDERS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables,)
    content = get_graphql_content(response)
    app_job = AppJob.objects.get()
    app_job_data = content["data"]["installApp"]["appJob"]
    assert int(app_job_data["id"]) == app_job.id
    assert app_job_data["status"] == JobStatus.PENDING.upper()
    assert app_job_data["manifestUrl"] == app_job.manifest_url
    mocked_task.assert_called_with(app_job.pk)


def test_install_app_mutation_by_app(
    permission_manage_apps, permission_manage_orders, app_api_client, monkeypatch
):
    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.install_app_task.delay", mocked_task
    )
    query = INSTALL_APP_MUTATION
    app_api_client.app.permissions.set(
        [permission_manage_apps, permission_manage_orders]
    )
    variables = {
        "name": "New external integration",
        "manifest_url": "http://localhost:3000/manifest",
        "permissions": [PermissionEnum.MANAGE_ORDERS.name],
    }
    response = app_api_client.post_graphql(query, variables=variables,)
    content = get_graphql_content(response)
    app_job = AppJob.objects.get()
    app_job_data = content["data"]["installApp"]["appJob"]
    assert int(app_job_data["id"]) == app_job.id
    assert app_job_data["status"] == JobStatus.PENDING.upper()
    assert app_job_data["manifestUrl"] == app_job.manifest_url
    mocked_task.assert_called_with(app_job.pk)


def test_app_install_mutation_out_of_scope_permissions(
    permission_manage_apps, staff_api_client, staff_user
):
    query = INSTALL_APP_MUTATION
    staff_user.user_permissions.set([permission_manage_apps])
    variables = {
        "name": "New external integration",
        "manifest_url": "http://localhost:3000/manifest",
        "permissions": [PermissionEnum.MANAGE_ORDERS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables,)
    content = get_graphql_content(response)
    data = content["data"]["installApp"]

    errors = data["appErrors"]
    assert not data["appJob"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert error["permissions"] == [PermissionEnum.MANAGE_ORDERS.name]


def test_install_app_mutation_by_app_out_of_scope_permissions(
    permission_manage_apps, app_api_client
):
    query = INSTALL_APP_MUTATION
    app_api_client.app.permissions.set([permission_manage_apps])
    variables = {
        "name": "New external integration",
        "manifest_url": "http://localhost:3000/manifest",
        "permissions": [PermissionEnum.MANAGE_ORDERS.name],
    }
    response = app_api_client.post_graphql(query, variables=variables,)

    content = get_graphql_content(response)
    data = content["data"]["installApp"]

    errors = data["appErrors"]
    assert not data["appJob"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert error["permissions"] == [PermissionEnum.MANAGE_ORDERS.name]
