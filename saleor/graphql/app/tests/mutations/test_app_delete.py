import json
from unittest import mock

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....app.error_codes import AppErrorCode
from .....app.models import App
from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

APP_DELETE_MUTATION = """
    mutation appDelete($id: ID!){
      appDelete(id: $id){
        errors{
          field
          message
          code
        }
        app{
          name
        }
      }
    }
"""


def test_app_delete(
    staff_api_client,
    staff_user,
    app,
    permission_manage_orders,
    permission_manage_apps,
):
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    staff_user.user_permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    assert data["app"]
    assert not data["errors"]
    assert not App.objects.filter(id=app.id)


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_app_delete_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    staff_user,
    app,
    permission_manage_orders,
    permission_manage_apps,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    app.permissions.add(permission_manage_orders)
    staff_user.user_permissions.add(permission_manage_orders)
    app_global_id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": app_global_id}

    # when
    response = staff_api_client.post_graphql(
        APP_DELETE_MUTATION, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["appDelete"]["app"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": app_global_id,
                "is_active": app.is_active,
                "name": app.name,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.APP_DELETED,
        [any_webhook],
        app,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_app_delete_for_app(
    app_api_client,
    permission_manage_orders,
    permission_manage_apps,
):
    requestor = app_api_client.app
    app = App.objects.create(name="New_app")
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    requestor.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    assert data["app"]
    assert not data["errors"]
    assert not App.objects.filter(id=app.id).exists()


def test_app_delete_out_of_scope_app(
    staff_api_client,
    staff_user,
    app,
    permission_manage_apps,
    permission_manage_orders,
):
    """Ensure user can't delete app with wider scope of permissions."""
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    errors = data["errors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "id"


def test_app_delete_superuser_can_delete_any_app(
    superuser_api_client,
    app,
    permission_manage_apps,
    permission_manage_orders,
):
    """Ensure superuser can delete app with any scope of permissions."""
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}

    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    assert data["app"]
    assert not data["errors"]
    assert not App.objects.filter(id=app.id).exists()


def test_app_delete_for_app_out_of_scope_app(
    app_api_client,
    permission_manage_orders,
    permission_manage_apps,
):
    app = App.objects.create(name="New_app")
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    errors = data["errors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "id"
