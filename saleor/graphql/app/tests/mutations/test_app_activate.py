import graphene

from .....app.models import App
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
    # given
    app.is_active = False
    app.save()
    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )

    # then
    get_graphql_content(response)

    app.refresh_from_db()
    assert app.is_active


def test_activate_app_by_app(app, app_api_client, permission_manage_apps):
    # given
    app = App.objects.create(name="Sample app objects", is_active=False)
    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }
    app_api_client.app.permissions.set([permission_manage_apps])

    # when
    response = app_api_client.post_graphql(query, variables=variables)

    # then
    get_graphql_content(response)

    app.refresh_from_db()
    assert app.is_active


def test_activate_app_missing_permission(
    app, staff_api_client, permission_manage_orders
):
    # given
    app.is_active = False
    app.save()
    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_orders,)
    )

    # then
    assert_no_permission(response)

    app.refresh_from_db()
    assert not app.is_active


def test_activate_app_by_app_missing_permission(
    app, app_api_client, permission_manage_orders
):
    # given
    app = App.objects.create(name="Sample app objects", is_active=False)
    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }
    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(query, variables=variables)

    # then
    assert_no_permission(response)

    assert not app.is_active


def test_app_has_more_permission_than_user_requestor(
    app, staff_api_client, permission_manage_orders, permission_manage_apps
):
    # given
    app.permissions.add(permission_manage_orders)
    app.is_active = False
    app.save()

    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["appActivate"]["app"]
    app_errors = content["data"]["appActivate"]["appErrors"]
    app.refresh_from_db()

    assert not app_errors
    assert app_data["isActive"] is True
    assert app.is_active


def test_app_has_more_permission_than_app_requestor(
    app_api_client, permission_manage_orders, permission_manage_apps
):
    # given
    app = App.objects.create(name="Sample app objects", is_active=False)
    app.permissions.add(permission_manage_orders)

    query = APP_ACTIVATE_MUTATION
    id = graphene.Node.to_global_id("App", app.id)
    variables = {
        "id": id,
    }

    # when
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["appActivate"]["app"]
    app_errors = content["data"]["appActivate"]["appErrors"]
    app.refresh_from_db()

    assert not app_errors
    assert app_data["isActive"] is True
    assert app.is_active
