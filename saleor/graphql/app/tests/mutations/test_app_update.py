from unittest import mock

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....app.error_codes import AppErrorCode
from .....app.models import App, AppToken
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....core.enums import PermissionEnum
from ....tests.utils import assert_no_permission, get_graphql_content

APP_UPDATE_MUTATION = """
mutation AppUpdate($id: ID!, $permissions: [PermissionEnum!]){
    appUpdate(id: $id,
        input:{permissions:$permissions}){
        app{
            isActive
            id
            permissions{
                code
                name
            }
            tokens{
                authToken
            }
            name
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


def test_app_update_mutation(
    app_with_token,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
    staff_api_client,
    staff_user,
):
    query = APP_UPDATE_MUTATION
    app = app_with_token
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    app_data = content["data"]["appUpdate"]["app"]
    tokens_data = app_data["tokens"]
    app.refresh_from_db()
    tokens = app.tokens.all()

    assert app_data["isActive"] == app.is_active
    assert len(tokens_data) == 1
    assert tokens_data[0]["authToken"] == tokens.get().auth_token[-4:]
    assert set(app.permissions.all()) == {
        permission_manage_products,
        permission_manage_users,
    }


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_app_update_trigger_mutation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    app_with_token,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
    staff_api_client,
    staff_user,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)
    app_global_id = graphene.Node.to_global_id("App", app_with_token.id)

    variables = {
        "id": app_global_id,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        APP_UPDATE_MUTATION, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)
    app_with_token.refresh_from_db()

    # then
    assert content["data"]["appUpdate"]["app"]
    mocked_webhook_trigger.assert_called_once_with(
        {
            "id": variables["id"],
            "is_active": app_with_token.is_active,
            "name": app_with_token.name,
            "meta": generate_meta(
                requestor_data=generate_requestor(
                    SimpleLazyObject(lambda: staff_api_client.user)
                )
            ),
        },
        WebhookEventAsyncType.APP_UPDATED,
        [any_webhook],
        app_with_token,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_app_update_mutation_for_app(
    permission_manage_apps,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    app_api_client,
):
    query = APP_UPDATE_MUTATION

    app = App.objects.create(name="New_app")
    app.permissions.add(permission_manage_orders)
    AppToken.objects.create(app=app)

    requestor = app_api_client.app
    requestor.permissions.add(
        permission_manage_apps,
        permission_manage_products,
        permission_manage_users,
        permission_manage_orders,
    )
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    app_data = content["data"]["appUpdate"]["app"]
    tokens_data = app_data["tokens"]
    app.refresh_from_db()
    tokens = app.tokens.all()

    assert app_data["isActive"] == app.is_active
    assert len(tokens_data) == 1
    assert tokens_data[0]["authToken"] == tokens.get().auth_token[-4:]
    assert set(app.permissions.all()) == {
        permission_manage_products,
        permission_manage_users,
    }


def test_app_update_mutation_out_of_scope_permissions(
    app,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
    staff_api_client,
    staff_user,
):
    """Ensure user cannot add permissions to app witch he doesn't have."""
    query = APP_UPDATE_MUTATION
    staff_user.user_permissions.add(permission_manage_apps, permission_manage_products)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }

    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appUpdate"]
    errors = data["errors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert error["permissions"] == [PermissionEnum.MANAGE_USERS.name]


def test_app_update_mutation_superuser_can_add_any_permissions_to_app(
    app_with_token,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
    superuser_api_client,
):
    """Ensure superuser can add any permissions to app."""
    query = APP_UPDATE_MUTATION
    app = app_with_token
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }

    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appUpdate"]
    app_data = data["app"]
    tokens_data = app_data["tokens"]
    app.refresh_from_db()
    tokens = app.tokens.all()

    assert app_data["isActive"] == app.is_active
    assert len(tokens_data) == 1
    assert tokens_data[0]["authToken"] == tokens.get().auth_token[-4:]
    assert set(app.permissions.all()) == {
        permission_manage_products,
        permission_manage_users,
    }


def test_app_update_mutation_for_app_out_of_scope_permissions(
    permission_manage_apps,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    app_api_client,
):
    app = App.objects.create(name="New_app")
    query = APP_UPDATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(
        permission_manage_apps,
        permission_manage_products,
        permission_manage_orders,
    )
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appUpdate"]
    errors = data["errors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert error["permissions"] == [PermissionEnum.MANAGE_USERS.name]


def test_app_update_mutation_out_of_scope_app(
    app,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    staff_api_client,
    staff_user,
):
    """Ensure user cannot manage app with wider permission scope."""
    query = APP_UPDATE_MUTATION
    staff_user.user_permissions.add(
        permission_manage_apps,
        permission_manage_products,
        permission_manage_users,
    )
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }

    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appUpdate"]
    errors = data["errors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "id"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name


def test_app_update_mutation_superuser_can_update_any_app(
    app_with_token,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    superuser_api_client,
):
    """Ensure superuser can manage any app."""
    query = APP_UPDATE_MUTATION
    app = app_with_token
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }

    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appUpdate"]
    app_data = data["app"]
    tokens_data = app_data["tokens"]
    app.refresh_from_db()
    tokens = app.tokens.all()

    assert app_data["isActive"] == app.is_active
    assert len(tokens_data) == 1
    assert tokens_data[0]["authToken"] == tokens.get().auth_token[-4:]
    assert set(app.permissions.all()) == {
        permission_manage_products,
        permission_manage_users,
    }


def test_app_update_mutation_for_app_out_of_scope_app(
    permission_manage_apps,
    permission_manage_products,
    permission_manage_orders,
    permission_manage_users,
    app_api_client,
):
    app = App.objects.create(name="New_app")
    query = APP_UPDATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(
        permission_manage_apps,
        permission_manage_products,
        permission_manage_users,
    )
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {
        "id": id,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appUpdate"]
    errors = data["errors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "id"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name


def test_app_update_no_permission(app, staff_api_client, staff_user):
    query = APP_UPDATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
