import graphene

from saleor.app.models import AppJob
from saleor.core import JobStatus
from saleor.graphql.core.enums import AppErrorCode
from tests.api.utils import get_graphql_content

DROP_FAILED_INSTALLATION_MUTATION = """
    mutation AppDropFailedInstallation($id: ID!){
        appDropFailedInstallation(id:$id){
            appErrors{
                field
                message
                code
                permissions
            }
        }
    }
"""


def test_drop_failed_installation_mutation(
    app_job,
    permission_manage_apps,
    staff_api_client,
    permission_manage_orders,
    staff_user,
):
    app_job.status = JobStatus.FAILED
    app_job.save()
    query = DROP_FAILED_INSTALLATION_MUTATION

    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    id = graphene.Node.to_global_id("AppOngoingInstallation", app_job.id)
    variables = {
        "id": id,
    }
    response = staff_api_client.post_graphql(query, variables=variables,)
    get_graphql_content(response)
    app_job = AppJob.objects.first()
    assert not app_job


def test_drop_failed_installation_mutation_by_app(
    permission_manage_apps, permission_manage_orders, app_api_client, app_job,
):
    app_job.status = JobStatus.FAILED
    app_job.save()

    id = graphene.Node.to_global_id("AppOngoingInstallation", app_job.id)
    query = DROP_FAILED_INSTALLATION_MUTATION
    app_api_client.app.permissions.set(
        [permission_manage_apps, permission_manage_orders]
    )
    variables = {
        "id": id,
        "activate_after_installation": False,
    }
    response = app_api_client.post_graphql(query, variables=variables,)
    get_graphql_content(response)
    assert not AppJob.objects.first()


def test_drop_failed_installation_mutation_out_of_scope_permissions(
    permission_manage_apps,
    staff_api_client,
    staff_user,
    app_job,
    permission_manage_orders,
):
    app_job.status = JobStatus.FAILED
    app_job.permissions.add(permission_manage_orders)
    app_job.save()

    query = DROP_FAILED_INSTALLATION_MUTATION

    staff_user.user_permissions.set([permission_manage_apps])

    id = graphene.Node.to_global_id("AppOngoingInstallation", app_job.id)
    variables = {
        "id": id,
    }
    response = staff_api_client.post_graphql(query, variables=variables,)
    get_graphql_content(response)
    assert AppJob.objects.get()


def test_drop_failed_installation_mutation_by_app_out_of_scope_permissions(
    permission_manage_apps, app_api_client, app_job, permission_manage_orders
):
    app_job.status = JobStatus.FAILED
    app_job.permissions.add(permission_manage_orders)
    app_job.save()
    query = DROP_FAILED_INSTALLATION_MUTATION

    app_api_client.app.permissions.set([permission_manage_apps])
    id = graphene.Node.to_global_id("AppOngoingInstallation", app_job.id)
    variables = {
        "id": id,
    }
    response = app_api_client.post_graphql(query, variables=variables,)

    get_graphql_content(response)
    assert AppJob.objects.get()


def test_cannot_drop_installation_if_status_is_different_than_failed(
    app_job,
    permission_manage_apps,
    staff_api_client,
    permission_manage_orders,
    staff_user,
):
    app_job.status = JobStatus.PENDING
    app_job.save()

    query = DROP_FAILED_INSTALLATION_MUTATION
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    id = graphene.Node.to_global_id("AppOngoingInstallation", app_job.id)
    variables = {
        "id": id,
    }
    response = staff_api_client.post_graphql(query, variables=variables,)
    content = get_graphql_content(response)

    AppJob.objects.get()
    app_job_errors = content["data"]["appDropFailedInstallation"]["appErrors"]

    assert len(app_job_errors) == 1
    assert app_job_errors[0]["field"] == "id"
    assert app_job_errors[0]["code"] == AppErrorCode.FORBIDDEN.name
