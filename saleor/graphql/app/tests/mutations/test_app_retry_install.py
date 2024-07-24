from unittest.mock import Mock, patch

import graphene

from .....app.models import App, AppInstallation
from .....app.tasks import install_app_task
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


def _mutate_app_install_retry(client, variables, ignore_errors=False):
    response = client.post_graphql(RETRY_INSTALL_APP_MUTATION, variables)
    content = get_graphql_content(response, ignore_errors=True)
    return content["data"]["appRetryInstall"]


def test_retry_install_app_mutation(
    monkeypatch,
    app_installation,
    permission_manage_apps,
    staff_api_client,
    permission_manage_orders,
    staff_user,
):
    # given
    app_installation.status = JobStatus.FAILED
    app_installation.save()
    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_retry_install.install_app_task.delay",
        mocked_task,
    )
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    variables = {
        "id": graphene.Node.to_global_id("AppInstallation", app_installation.id),
        "activate_after_installation": True,
    }

    # when
    data = _mutate_app_install_retry(staff_api_client, variables)

    # then
    app_installation = AppInstallation.objects.get()
    _, app_id = graphene.Node.from_global_id(data["appInstallation"]["id"])
    assert int(app_id) == app_installation.id
    assert data["appInstallation"]["status"] == JobStatus.PENDING.upper()
    assert data["appInstallation"]["manifestUrl"] == app_installation.manifest_url
    mocked_task.assert_called_with(app_installation.pk, True)
    assert App.objects.count() == 0


def test_retry_install_app_mutation_with_another_app_installed_but_marked_to_be_removed(
    monkeypatch,
    app_installation,
    permission_manage_apps,
    staff_api_client,
    permission_manage_orders,
    staff_user,
    app_marked_to_be_removed,
):
    assert app_marked_to_be_removed.removed_at is not None
    # given
    app_installation.status = JobStatus.FAILED
    app_installation.save()
    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_retry_install.install_app_task.delay",
        mocked_task,
    )
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    variables = {
        "id": graphene.Node.to_global_id("AppInstallation", app_installation.id),
        "activate_after_installation": True,
    }

    # when
    data = _mutate_app_install_retry(staff_api_client, variables)

    # then
    app_installation = AppInstallation.objects.get()
    _, app_id = graphene.Node.from_global_id(data["appInstallation"]["id"])
    assert int(app_id) == app_installation.id
    assert data["appInstallation"]["status"] == JobStatus.PENDING.upper()
    assert data["appInstallation"]["manifestUrl"] == app_installation.manifest_url
    mocked_task.assert_called_with(app_installation.pk, True)
    assert App.objects.count() == 1


def test_retry_install_app_mutation_by_app(
    permission_manage_apps,
    permission_manage_orders,
    app_api_client,
    monkeypatch,
    app_installation,
):
    # given
    app_installation.status = JobStatus.FAILED
    app_installation.save()
    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_retry_install.install_app_task.delay",
        mocked_task,
    )
    app_api_client.app.permissions.set(
        [permission_manage_apps, permission_manage_orders]
    )
    variables = {
        "id": graphene.Node.to_global_id("AppInstallation", app_installation.id),
        "activate_after_installation": False,
    }

    # when
    data = _mutate_app_install_retry(app_api_client, variables)

    # then
    app_installation = AppInstallation.objects.get()
    _, app_id = graphene.Node.from_global_id(data["appInstallation"]["id"])
    assert int(app_id) == app_installation.id
    assert data["appInstallation"]["status"] == JobStatus.PENDING.upper()
    assert data["appInstallation"]["manifestUrl"] == app_installation.manifest_url
    mocked_task.assert_called_with(app_installation.pk, False)


def test_retry_install_app_mutation_app_has_more_permission_than_user_requestor(
    permission_manage_apps,
    staff_api_client,
    staff_user,
    app_installation,
    permission_manage_orders,
    monkeypatch,
):
    # given
    app_installation.status = JobStatus.FAILED
    app_installation.permissions.add(permission_manage_orders)
    app_installation.save()

    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_retry_install.install_app_task.delay",
        mocked_task,
    )
    staff_user.user_permissions.set([permission_manage_apps])
    variables = {
        "id": graphene.Node.to_global_id("AppInstallation", app_installation.id)
    }

    # when
    data = _mutate_app_install_retry(staff_api_client, variables)

    # then

    errors = data["errors"]
    assert not errors

    app_installation = AppInstallation.objects.get()
    _, app_id = graphene.Node.from_global_id(data["appInstallation"]["id"])
    assert int(app_id) == app_installation.id
    assert data["appInstallation"]["status"] == JobStatus.PENDING.upper()
    assert data["appInstallation"]["manifestUrl"] == app_installation.manifest_url
    mocked_task.assert_called_with(app_installation.pk, True)


def test_retry_install_app_mutation_app_has_more_permission_than_app_requestor(
    permission_manage_apps,
    app_api_client,
    app_installation,
    permission_manage_orders,
    monkeypatch,
):
    # given
    app_installation.status = JobStatus.FAILED
    app_installation.permissions.add(permission_manage_orders)
    app_installation.save()

    mocked_task = Mock()
    monkeypatch.setattr(
        "saleor.graphql.app.mutations.app_retry_install.install_app_task.delay",
        mocked_task,
    )

    app_api_client.app.permissions.set([permission_manage_apps])
    variables = {
        "id": graphene.Node.to_global_id("AppInstallation", app_installation.id)
    }

    # when
    data = _mutate_app_install_retry(app_api_client, variables)

    # then
    errors = data["errors"]
    assert not errors

    app_installation = AppInstallation.objects.get()
    _, app_id = graphene.Node.from_global_id(data["appInstallation"]["id"])
    assert int(app_id) == app_installation.id
    assert data["appInstallation"]["status"] == JobStatus.PENDING.upper()
    assert data["appInstallation"]["manifestUrl"] == app_installation.manifest_url
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
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])
    variables = {
        "id": graphene.Node.to_global_id("AppInstallation", app_installation.id),
        "activate_after_installation": True,
    }

    # when
    data = _mutate_app_install_retry(staff_api_client, variables)

    # then
    AppInstallation.objects.get()
    app_installation_errors = data["errors"]
    assert not data["appInstallation"]
    assert len(app_installation_errors) == 1
    assert app_installation_errors[0]["field"] == "id"
    assert app_installation_errors[0]["code"] == AppErrorCode.INVALID_STATUS.name

    assert not mocked_task.called


@patch("saleor.app.installation_utils.send_app_token", Mock())
@patch(
    "saleor.graphql.app.mutations.app_retry_install.install_app_task.delay",
    install_app_task,
)
def test_install_retry_app_mutation_with_the_same_identifier_twice(
    permission_manage_apps,
    permission_manage_orders,
    staff_api_client,
    app_installation,
    staff_user,
    monkeypatch,
    app,
):
    # given
    app_installation.status = JobStatus.FAILED
    app_installation.save()
    staff_user.user_permissions.set([permission_manage_apps, permission_manage_orders])

    variables = {
        "id": graphene.Node.to_global_id("AppInstallation", app_installation.id),
        "activate_after_installation": True,
    }

    # when
    with patch("saleor.app.installation_utils.fetch_manifest") as mocked_fetch:
        mocked_fetch.return_value = {
            "id": app.identifier,
            "tokenTargetUrl": "http://localhost:3000/register",
            "name": "app",
            "version": "1.0.0",
        }
        data = _mutate_app_install_retry(staff_api_client, variables)

    # then
    # Installation is done in celery task - response shows that app is being installed
    assert not data["errors"]
    assert data["appInstallation"]["status"] == "PENDING"
    assert data["appInstallation"]["manifestUrl"] == app.manifest_url
    assert App.objects.count() == 1
    # Celery bypassed, AppInstallation instance failed to install app
    app_installation = AppInstallation.objects.first()
    assert app_installation.status == JobStatus.FAILED
    assert app_installation.message == (
        "identifier: "
        "['App with the same identifier is already installed: Sample app objects']"
    )
