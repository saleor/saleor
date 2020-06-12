import graphene

from .....app.models import App
from ....core.enums import AppErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

APP_ACTIVATE_MUTATION = """
    mutation AppActivate($id: ID!){
      appActivate(id:$id){
        app{
          id
          isActive
        }
        appErrors{
          field
          message
          code
        }
      }
    }
"""


def test_activate_app(app, staff_api_client, permission_manage_apps):
    app.is_active = False
    app.save()
    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    get_graphql_content(response)

    app.refresh_from_db()
    assert app.is_active


def test_activate_app_by_app(app, app_api_client, permission_manage_apps):
    app = App.objects.create(name="Sample app objects", is_active=False)
    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }
    app_api_client.app.permissions.set([permission_manage_apps])
    response = app_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)

    app.refresh_from_db()
    assert app.is_active


def test_activate_app_missing_permission(
    app, staff_api_client, permission_manage_orders
):
    app.is_active = False
    app.save()
    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_orders,)
    )
    assert_no_permission(response)

    app.refresh_from_db()
    assert not app.is_active


def test_activate_app_by_app_missing_permission(
    app, app_api_client, permission_manage_orders
):
    app = App.objects.create(name="Sample app objects", is_active=False)
    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }
    app_api_client.app.permissions.set([permission_manage_orders])
    response = app_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)

    assert not app.is_active


def test_app_has_more_permission_than_user_requestor(
    app, staff_api_client, permission_manage_orders, permission_manage_apps
):
    app.permissions.add(permission_manage_orders)
    app.is_active = False
    app.save()

    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)
    app_data = content["data"]["appActivate"]["app"]
    app_errors = content["data"]["appActivate"]["appErrors"]
    app.refresh_from_db()

    assert not app_data
    assert len(app_errors) == 1
    assert app_errors[0]["field"] == "id"
    assert app_errors[0]["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert not app.is_active


def test_app_has_more_permission_than_app_requestor(
    app_api_client, permission_manage_orders, permission_manage_apps
):
    app = App.objects.create(name="Sample app objects", is_active=False)
    app.permissions.add(permission_manage_orders)

    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)
    app_data = content["data"]["appActivate"]["app"]
    app_errors = content["data"]["appActivate"]["appErrors"]
    app.refresh_from_db()

    assert not app_data
    assert len(app_errors) == 1
    assert app_errors[0]["field"] == "id"
    assert app_errors[0]["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert not app.is_active
