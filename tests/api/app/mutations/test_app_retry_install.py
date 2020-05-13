from unittest.mock import Mock

import graphene

from saleor.app.models import AppJob
from saleor.core import JobStatus
from saleor.graphql.core.enums import AppErrorCode
from tests.api.utils import get_graphql_content

RETRY_INSTALL_APP_MUTATION = """
    mutation AppRetryInstall(
        $id: ID!, $activate_after_installation: Boolean){
        appRetryInstall(id:$id, activateAfterInstallation:$activate_after_installation){
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


def test_retry_install_app_mutation(
    monkeypatch,
    app_job,
    permission_manage_apps,
    staff_api_client,
    permission_manage_orders,
    staff_user,
):
    app_job.status = JobStatus.FAILED
    app_job.save()
    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.install_app_task.delay", mocked_task
    )
    query = RETRY_INSTALL_APP_MUTATION
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    id = graphene.Node.to_global_id("OngoingAppInstallation", app_job.id)
    variables = {
        "id": id,
        "activate_after_installation": True,
    }
    response = staff_api_client.post_graphql(query, variables=variables,)
    content = get_graphql_content(response)
    app_job = AppJob.objects.get()
    app_job_data = content["data"]["appRetryInstall"]["appJob"]
    assert int(app_job_data["id"]) == app_job.id
    assert app_job_data["status"] == JobStatus.PENDING.upper()
    assert app_job_data["manifestUrl"] == app_job.manifest_url
    mocked_task.assert_called_with(app_job.pk, True)


def test_retry_install_app_mutation_by_app(
    permission_manage_apps,
    permission_manage_orders,
    app_api_client,
    monkeypatch,
    app_job,
):
    app_job.status = JobStatus.FAILED
    app_job.save()
    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.install_app_task.delay", mocked_task
    )
    id = graphene.Node.to_global_id("OngoingAppInstallation", app_job.id)
    query = RETRY_INSTALL_APP_MUTATION
    app_api_client.app.permissions.set(
        [permission_manage_apps, permission_manage_orders]
    )
    variables = {
        "id": id,
        "activate_after_installation": False,
    }
    response = app_api_client.post_graphql(query, variables=variables,)
    content = get_graphql_content(response)
    app_job = AppJob.objects.get()
    app_job_data = content["data"]["appRetryInstall"]["appJob"]
    assert int(app_job_data["id"]) == app_job.id
    assert app_job_data["status"] == JobStatus.PENDING.upper()
    assert app_job_data["manifestUrl"] == app_job.manifest_url
    mocked_task.assert_called_with(app_job.pk, False)


def test_retry_install_app_mutation_missing_required_permissions(
    permission_manage_apps,
    staff_api_client,
    staff_user,
    app_job,
    permission_manage_orders,
):
    app_job.status = JobStatus.FAILED
    app_job.permissions.add(permission_manage_orders)
    app_job.save()

    query = RETRY_INSTALL_APP_MUTATION

    staff_user.user_permissions.set([permission_manage_apps])

    id = graphene.Node.to_global_id("OngoingAppInstallation", app_job.id)
    variables = {
        "id": id,
    }
    response = staff_api_client.post_graphql(query, variables=variables,)
    content = get_graphql_content(response)
    data = content["data"]["appRetryInstall"]

    errors = data["appErrors"]
    assert not data["appJob"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "id"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name


def test_retry_install_app_mutation_by_app_missing_required_permissions(
    permission_manage_apps, app_api_client, app_job, permission_manage_orders
):
    app_job.status = JobStatus.FAILED
    app_job.permissions.add(permission_manage_orders)
    app_job.save()
    query = RETRY_INSTALL_APP_MUTATION
    app_api_client.app.permissions.set([permission_manage_apps])
    id = graphene.Node.to_global_id("OngoingAppInstallation", app_job.id)
    variables = {
        "id": id,
    }
    response = app_api_client.post_graphql(query, variables=variables,)

    content = get_graphql_content(response)
    data = content["data"]["appRetryInstall"]

    errors = data["appErrors"]
    assert not data["appJob"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "id"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name


def test_cannot_retry_installation_if_status_is_different_than_failed(
    monkeypatch,
    app_job,
    permission_manage_apps,
    staff_api_client,
    permission_manage_orders,
    staff_user,
):
    app_job.status = JobStatus.PENDING
    app_job.save()

    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.install_app_task.delay", mocked_task
    )
    query = RETRY_INSTALL_APP_MUTATION
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    id = graphene.Node.to_global_id("OngoingAppInstallation", app_job.id)
    variables = {
        "id": id,
        "activate_after_installation": True,
    }
    response = staff_api_client.post_graphql(query, variables=variables,)
    content = get_graphql_content(response)

    AppJob.objects.get()
    app_job_data = content["data"]["appRetryInstall"]["appJob"]
    app_job_errors = content["data"]["appRetryInstall"]["appErrors"]
    assert not app_job_data
    assert len(app_job_errors) == 1
    assert app_job_errors[0]["field"] == "id"
    assert app_job_errors[0]["code"] == AppErrorCode.FORBIDDEN.name

    assert not mocked_task.called
