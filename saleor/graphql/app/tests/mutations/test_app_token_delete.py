import graphene

from .....app.error_codes import AppErrorCode
from .....app.models import App, AppToken
from ....tests.utils import assert_no_permission, get_graphql_content

APP_TOKEN_DELETE_MUTATION = """
    mutation appTokenDelete($id: ID!){
      appTokenDelete(id: $id){
        appErrors{
          field
          message
          code
        }
        appToken{
          name
          authToken
        }
      }
    }
"""


def test_app_token_delete(
    permission_manage_apps,
    staff_api_client,
    staff_user,
    app,
    permission_manage_products,
):

    query = APP_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    staff_user.user_permissions.add(permission_manage_products)
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppToken", token.id)
    staff_user.user_permissions.add(permission_manage_apps)

    variables = {"id": id}
    response = staff_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    assert not AppToken.objects.filter(id=token.id).first()


def test_app_token_delete_for_app(
    permission_manage_apps,
    app_api_client,
    permission_manage_products,
):
    app = App.objects.create(name="New_app", is_active=True)
    token = AppToken.objects.create(app=app)
    query = APP_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    requestor = app_api_client.app
    requestor.permissions.add(permission_manage_products)
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppToken", token.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    get_graphql_content(response)
    assert not AppToken.objects.filter(id=token.id).first()


def test_app_token_delete_no_permissions(staff_api_client, staff_user, app):

    query = APP_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    id = graphene.Node.to_global_id("AppToken", token.id)

    variables = {"id": id}
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    token.refresh_from_db()


def test_app_token_delete_out_of_scope_app(
    permission_manage_apps,
    staff_api_client,
    staff_user,
    app,
    permission_manage_products,
):
    """Ensure user can't delete app token with wider scope of permissions."""
    query = APP_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppToken", token.id)

    variables = {"id": id}

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appTokenDelete"]
    errors = data["appErrors"]

    assert not data["appToken"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "id"
    assert AppToken.objects.filter(id=token.id).exists()


def test_app_token_delete_superuser_can_delete_token_for_any_app(
    permission_manage_apps,
    superuser_api_client,
    app,
    permission_manage_products,
):
    """Ensure superuser can delete app token for app with any scope of permissions."""
    query = APP_TOKEN_DELETE_MUTATION
    token = app.tokens.get()
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppToken", token.id)

    variables = {"id": id}

    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appTokenDelete"]
    errors = data["appErrors"]

    assert data["appToken"]
    assert not errors
    assert not AppToken.objects.filter(id=token.id).exists()


def test_app_token_delete_for_app_out_of_scope_app(
    permission_manage_apps,
    app_api_client,
    permission_manage_products,
):
    app = App.objects.create(name="New_app", is_active=True)
    token = AppToken.objects.create(app=app)
    query = APP_TOKEN_DELETE_MUTATION
    app.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppToken", token.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appTokenDelete"]
    errors = data["appErrors"]

    assert not data["appToken"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "id"
    assert AppToken.objects.filter(id=token.id).exists()
