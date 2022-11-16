from unittest.mock import Mock

import graphene

from .....app.models import AppInstallation
from .....core import JobStatus
from ....core.enums import AppErrorCode
from ....tests.utils import get_graphql_content

RETRY_INSTALL_APP_MUTATION = """
    mutation AppRetryInstall(
        $id: ID!, $activate_after_installation: Boolean){
        appRetryInstall(id:$id, activateAfterInstallation:$activate_after_installation){
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


def test_retry_install_app_mutation(
    monkeypatch,
    app_installation,
    permission_manage_apps,
    staff_api_client,
    permission_manage_orders,
    staff_user,
):
    app_installation.status = JobStatus.FAILED
    app_installation.save()
    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_retry_install.install_app_task.delay",
        mocked_task,
    )
    query = RETRY_INSTALL_APP_MUTATION
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    id = graphene.Node.to_global_id("AppInstallation", app_installation.id)
    variables = {
        "id": id,
        "activate_after_installation": True,
    }
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
    )
    content = get_graphql_content(response)
    app_installation = AppInstallation.objects.get()
    app_installation_data = content["data"]["appRetryInstall"]["appInstallation"]
    _, app_id = graphene.Node.from_global_id(app_installation_data["id"])
    assert int(app_id) == app_installation.id
    assert app_installation_data["status"] == JobStatus.PENDING.upper()
    assert app_installation_data["manifestUrl"] == app_installation.manifest_url
    mocked_task.assert_called_with(app_installation.pk, True)


def test_retry_install_app_mutation_by_app(
    permission_manage_apps,
    permission_manage_orders,
    app_api_client,
    monkeypatch,
    app_installation,
):
    app_installation.status = JobStatus.FAILED
    app_installation.save()
    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_retry_install.install_app_task.delay",
        mocked_task,
    )
    id = graphene.Node.to_global_id("AppInstallation", app_installation.id)
    query = RETRY_INSTALL_APP_MUTATION
    app_api_client.app.permissions.set(
        [permission_manage_apps, permission_manage_orders]
    )
    variables = {
        "id": id,
        "activate_after_installation": False,
    }
    response = app_api_client.post_graphql(
        query,
        variables=variables,
    )
    content = get_graphql_content(response)
    app_installation = AppInstallation.objects.get()
    app_installation_data = content["data"]["appRetryInstall"]["appInstallation"]
    _, app_id = graphene.Node.from_global_id(app_installation_data["id"])
    assert int(app_id) == app_installation.id
    assert app_installation_data["status"] == JobStatus.PENDING.upper()
    assert app_installation_data["manifestUrl"] == app_installation.manifest_url
    mocked_task.assert_called_with(app_installation.pk, False)


def test_retry_install_app_mutation_app_has_more_permission_than_user_requestor(
    permission_manage_apps,
    staff_api_client,
    staff_user,
    app_installation,
    permission_manage_orders,
    monkeypatch,
):
    app_installation.status = JobStatus.FAILED
    app_installation.permissions.add(permission_manage_orders)
    app_installation.save()

    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_retry_install.install_app_task.delay",
        mocked_task,
    )

    query = RETRY_INSTALL_APP_MUTATION

    staff_user.user_permissions.set([permission_manage_apps])

    id = graphene.Node.to_global_id("AppInstallation", app_installation.id)
    variables = {
        "id": id,
    }
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["appRetryInstall"]

    errors = data["errors"]
    assert not errors

    app_installation = AppInstallation.objects.get()
    app_installation_data = content["data"]["appRetryInstall"]["appInstallation"]
    _, app_id = graphene.Node.from_global_id(app_installation_data["id"])
    assert int(app_id) == app_installation.id
    assert app_installation_data["status"] == JobStatus.PENDING.upper()
    assert app_installation_data["manifestUrl"] == app_installation.manifest_url
    mocked_task.assert_called_with(app_installation.pk, True)


def test_retry_install_app_mutation_app_has_more_permission_than_app_requestor(
    permission_manage_apps,
    app_api_client,
    app_installation,
    permission_manage_orders,
    monkeypatch,
):
    app_installation.status = JobStatus.FAILED
    app_installation.permissions.add(permission_manage_orders)
    app_installation.save()

    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_retry_install.install_app_task.delay",
        mocked_task,
    )

    query = RETRY_INSTALL_APP_MUTATION
    app_api_client.app.permissions.set([permission_manage_apps])
    id = graphene.Node.to_global_id("AppInstallation", app_installation.id)
    variables = {
        "id": id,
    }
    response = app_api_client.post_graphql(
        query,
        variables=variables,
    )

    content = get_graphql_content(response)
    data = content["data"]["appRetryInstall"]

    errors = data["errors"]
    assert not errors

    app_installation = AppInstallation.objects.get()
    app_installation_data = content["data"]["appRetryInstall"]["appInstallation"]
    _, app_id = graphene.Node.from_global_id(app_installation_data["id"])
    assert int(app_id) == app_installation.id
    assert app_installation_data["status"] == JobStatus.PENDING.upper()
    assert app_installation_data["manifestUrl"] == app_installation.manifest_url
    mocked_task.assert_called_with(app_installation.pk, True)


def test_cannot_retry_installation_if_status_is_different_than_failed(
    monkeypatch,
    app_installation,
    permission_manage_apps,
    staff_api_client,
    permission_manage_orders,
    staff_user,
):
    app_installation.status = JobStatus.PENDING
    app_installation.save()

    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_retry_install.install_app_task.delay",
        mocked_task,
    )
    query = RETRY_INSTALL_APP_MUTATION
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    id = graphene.Node.to_global_id("AppInstallation", app_installation.id)
    variables = {
        "id": id,
        "activate_after_installation": True,
    }
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
    )
    content = get_graphql_content(response)

    AppInstallation.objects.get()
    app_installation_data = content["data"]["appRetryInstall"]["appInstallation"]
    app_installation_errors = content["data"]["appRetryInstall"]["errors"]
    assert not app_installation_data
    assert len(app_installation_errors) == 1
    assert app_installation_errors[0]["field"] == "id"
    assert app_installation_errors[0]["code"] == AppErrorCode.INVALID_STATUS.name

    assert not mocked_task.called
