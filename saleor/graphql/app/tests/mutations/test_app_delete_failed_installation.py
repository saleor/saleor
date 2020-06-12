import graphene

from .....app.models import AppInstallation
from .....core import JobStatus
from ....core.enums import AppErrorCode
from ....tests.utils import get_graphql_content

DELETE_FAILED_INSTALLATION_MUTATION = """
    mutation AppDeleteFailedInstallation($id: ID!){
        appDeleteFailedInstallation(id:$id){
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
    app_installation,
    permission_manage_apps,
    staff_api_client,
    permission_manage_orders,
    staff_user,
):
    app_installation.status = JobStatus.FAILED
    app_installation.save()
    query = DELETE_FAILED_INSTALLATION_MUTATION

    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    id = graphene.Node.to_global_id("AppInstallation", app_installation.id)
    variables = {
        "id": id,
    }
    response = staff_api_client.post_graphql(query, variables=variables,)
    get_graphql_content(response)
    app_installation = AppInstallation.objects.first()
    assert not app_installation


def test_drop_failed_installation_mutation_by_app(
    permission_manage_apps, permission_manage_orders, app_api_client, app_installation,
):
    app_installation.status = JobStatus.FAILED
    app_installation.save()

    id = graphene.Node.to_global_id("AppInstallation", app_installation.id)
    query = DELETE_FAILED_INSTALLATION_MUTATION
    app_api_client.app.permissions.set(
        [permission_manage_apps, permission_manage_orders]
    )
    variables = {
        "id": id,
        "activate_after_installation": False,
    }
    response = app_api_client.post_graphql(query, variables=variables,)
    get_graphql_content(response)
    assert not AppInstallation.objects.first()


def test_drop_failed_installation_mutation_out_of_scope_permissions(
    permission_manage_apps,
    staff_api_client,
    staff_user,
    app_installation,
    permission_manage_orders,
):
    app_installation.status = JobStatus.FAILED
    app_installation.permissions.add(permission_manage_orders)
    app_installation.save()

    query = DELETE_FAILED_INSTALLATION_MUTATION

    staff_user.user_permissions.set([permission_manage_apps])

    id = graphene.Node.to_global_id("AppInstallation", app_installation.id)
    variables = {
        "id": id,
    }
    response = staff_api_client.post_graphql(query, variables=variables,)
    get_graphql_content(response)
    assert AppInstallation.objects.get()


def test_drop_failed_installation_mutation_by_app_out_of_scope_permissions(
    permission_manage_apps, app_api_client, app_installation, permission_manage_orders
):
    app_installation.status = JobStatus.FAILED
    app_installation.permissions.add(permission_manage_orders)
    app_installation.save()
    query = DELETE_FAILED_INSTALLATION_MUTATION

    app_api_client.app.permissions.set([permission_manage_apps])
    id = graphene.Node.to_global_id("AppInstallation", app_installation.id)
    variables = {
        "id": id,
    }
    response = app_api_client.post_graphql(query, variables=variables,)

    get_graphql_content(response)
    assert AppInstallation.objects.get()


def test_cannot_drop_installation_if_status_is_different_than_failed(
    app_installation,
    permission_manage_apps,
    staff_api_client,
    permission_manage_orders,
    staff_user,
):
    app_installation.status = JobStatus.PENDING
    app_installation.save()

    query = DELETE_FAILED_INSTALLATION_MUTATION
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    id = graphene.Node.to_global_id("AppInstallation", app_installation.id)
    variables = {
        "id": id,
    }
    response = staff_api_client.post_graphql(query, variables=variables,)
    content = get_graphql_content(response)

    AppInstallation.objects.get()
    app_installation_errors = content["data"]["appDeleteFailedInstallation"][
        "appErrors"
    ]

    assert len(app_installation_errors) == 1
    assert app_installation_errors[0]["field"] == "id"
    assert app_installation_errors[0]["code"] == AppErrorCode.INVALID_STATUS.name
