import graphene

from .....app.models import App, AppToken
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

QUERY_APP_TOKENS_WITH_CREATED_BY = """
    query ($id: ID) {
        app(id: $id) {
            id
            tokens {
                id
                createdAt
                createdBy {
                    id
                    email
                }
            }
        }
    }
"""


def test_manage_staff_can_see_created_by(
    staff_api_client, permission_manage_apps, permission_manage_staff
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_apps, permission_manage_staff)
    app = App.objects.create(name="New_app")
    token, _ = AppToken.objects.create(app=app, created_by=staff_user)
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_TOKENS_WITH_CREATED_BY, variables
    )

    # then
    content = get_graphql_content(response)
    tokens = content["data"]["app"]["tokens"]
    assert len(tokens) == 1
    assert tokens[0]["createdBy"]["email"] == staff_user.email
    assert tokens[0]["createdAt"] == token.created_at.isoformat()


def test_manage_apps_only_cannot_see_created_by(
    staff_api_client, permission_manage_apps
):
    # given - MANAGE_APPS but not MANAGE_STAFF, querying the User object
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_apps)
    app = App.objects.create(name="New_app")
    AppToken.objects.create(app=app, created_by=staff_user)
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_TOKENS_WITH_CREATED_BY, variables
    )

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["extensions"]["exception"]["code"] == "PermissionDenied"


def test_app_with_manage_staff_can_see_created_by(
    app_api_client, app, staff_user, permission_manage_staff
):
    # given - the app queries its own tokens (OWNER), createdBy needs MANAGE_STAFF
    app.permissions.add(permission_manage_staff)
    token = app.tokens.get()
    token.created_by = staff_user
    token.save(update_fields=["created_by"])
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_TOKENS_WITH_CREATED_BY, variables)

    # then
    content = get_graphql_content(response)
    tokens = content["data"]["app"]["tokens"]
    assert len(tokens) == 1
    assert tokens[0]["createdBy"]["email"] == staff_user.email
    assert tokens[0]["createdAt"] == token.created_at.isoformat()


def test_app_without_manage_staff_cannot_see_created_by(
    app_api_client, app, staff_user
):
    # given - no MANAGE_STAFF granted to the app
    token = app.tokens.get()
    token.created_by = staff_user
    token.save(update_fields=["created_by"])
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_TOKENS_WITH_CREATED_BY, variables)

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["extensions"]["exception"]["code"] == "PermissionDenied"


def test_created_by_null_is_handled_properly(
    staff_api_client, permission_manage_apps, permission_manage_staff
):
    # given - token whose creator was later deleted (FK set to null)
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_apps, permission_manage_staff)
    app = App.objects.create(name="New_app")
    AppToken.objects.create(app=app, created_by=None)
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_TOKENS_WITH_CREATED_BY, variables
    )

    # then
    content = get_graphql_content(response)
    tokens = content["data"]["app"]["tokens"]
    assert len(tokens) == 1
    assert tokens[0]["createdBy"] is None
