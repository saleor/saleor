from unittest import mock

import graphene
from django.utils.functional import SimpleLazyObject

from .....app.error_codes import AppErrorCode
from .....app.models import App
from .....webhook.event_types import WebhookEventAsyncType
from ....core.enums import PermissionEnum
from ....tests.utils import assert_no_permission, get_graphql_content

APP_CREATE_MUTATION = """
    mutation AppCreate(
        $name: String, $permissions: [PermissionEnum!]){
        appCreate(input:
            {name: $name, permissions: $permissions})
        {
            authToken
            app{
                permissions{
                    code
                    name
                }
                id
                isActive
                name
                tokens{
                    authToken
                }
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


def test_app_create_mutation(
    permission_manage_apps,
    permission_manage_products,
    staff_api_client,
    staff_user,
):
    query = APP_CREATE_MUTATION
    staff_user.user_permissions.add(permission_manage_products)

    variables = {
        "name": "New integration",
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    app_data = content["data"]["appCreate"]["app"]
    default_token = content["data"]["appCreate"]["authToken"]
    app = App.objects.get()
    assert app_data["isActive"] == app.is_active
    assert app_data["name"] == app.name
    assert list(app.permissions.all()) == [permission_manage_products]
    assert default_token
    assert default_token[-4:] == app.tokens.get().token_last_4


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_app_create_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    permission_manage_apps,
    permission_manage_products,
    staff_api_client,
    staff_user,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    staff_user.user_permissions.add(permission_manage_products)

    variables = {
        "name": "Trigger Test",
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }

    # when
    response = staff_api_client.post_graphql(
        APP_CREATE_MUTATION, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)
    app = App.objects.get(name=variables["name"])

    # then
    assert content["data"]["appCreate"]["app"]
    mocked_webhook_trigger.assert_called_once_with(
        {
            "id": graphene.Node.to_global_id("App", app.id),
            "is_active": app.is_active,
            "name": app.name,
        },
        WebhookEventAsyncType.APP_CREATED,
        [any_webhook],
        app,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_app_is_not_allowed_to_call_create_mutation_for_app(
    permission_manage_apps,
    permission_manage_products,
    app_api_client,
    staff_user,
):
    # given
    query = APP_CREATE_MUTATION
    requestor = app_api_client.app
    requestor.permissions.add(permission_manage_apps, permission_manage_products)

    variables = {
        "name": "New integration",
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }

    # when
    response = app_api_client.post_graphql(query, variables=variables)

    # then
    assert_no_permission(response)


def test_app_create_mutation_out_of_scope_permissions(
    permission_manage_apps,
    permission_manage_products,
    staff_api_client,
    staff_user,
):
    """Ensure user can't create app with permissions out of user's scope.

    Ensure superuser pass restrictions.
    """
    query = APP_CREATE_MUTATION
    staff_user.user_permissions.add(permission_manage_apps)

    variables = {
        "name": "New integration",
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }

    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]

    errors = data["errors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "permissions"
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_PERMISSION.name
    assert error["permissions"] == [PermissionEnum.MANAGE_PRODUCTS.name]


def test_app_create_mutation_superuser_can_create_app_with_any_perms(
    permission_manage_apps,
    permission_manage_products,
    superuser_api_client,
):
    """Ensure superuser can create app with any permissions."""
    query = APP_CREATE_MUTATION

    variables = {
        "name": "New integration",
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }

    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    app_data = content["data"]["appCreate"]["app"]
    default_token = content["data"]["appCreate"]["authToken"]
    app = App.objects.get()
    assert app_data["isActive"] == app.is_active
    assert app_data["name"] == app.name
    assert list(app.permissions.all()) == [permission_manage_products]
    assert default_token
    assert default_token[-4:] == app.tokens.get().token_last_4


def test_app_create_mutation_no_permissions(
    permission_manage_apps,
    permission_manage_products,
    staff_api_client,
    staff_user,
):
    query = APP_CREATE_MUTATION
    variables = {
        "name": "New integration",
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
