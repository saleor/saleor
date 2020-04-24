import graphene
import pytest
from freezegun import freeze_time

from saleor.app.models import App
from saleor.webhook.models import Webhook

from .utils import assert_no_permission, get_graphql_content

QUERY_APPS_WITH_FILTER = """
    query ($filter: AppFilterInput ){
        apps(first: 5, filter: $filter){
            edges{
                node{
                    id
                    isActive
                    permissions{
                        name
                        code
                    }
                    tokens{
                        authToken
                    }
                    webhooks{
                        name
                    }
                    name
                }
            }
        }
    }
    """


@pytest.mark.parametrize(
    "app_filter, count", (({"search": "Sample"}, 1), ({"isActive": False}, 1), ({}, 2)),
)
def test_apps_query(
    staff_api_client,
    permission_manage_apps,
    permission_manage_webhooks,
    app,
    app_filter,
    count,
):
    second_app = App.objects.create(name="Simple service")
    second_app.is_active = False
    second_app.tokens.create(name="default")
    second_app.save()

    webhooks = Webhook.objects.bulk_create(
        [
            Webhook(app=app, name="first", target_url="http://www.example.com/test"),
            Webhook(app=second_app, name="second", target_url="http://www.exa.com/s",),
        ]
    )
    webhooks_names = [w.name for w in webhooks]

    variables = {"filter": app_filter}
    response = staff_api_client.post_graphql(
        QUERY_APPS_WITH_FILTER,
        variables,
        permissions=[permission_manage_apps, permission_manage_webhooks],
    )
    content = get_graphql_content(response)

    apps_data = content["data"]["apps"]["edges"]
    for app_data in apps_data:
        tokens = app_data["node"]["tokens"]
        assert len(tokens) == 1
        assert len(tokens[0]["authToken"]) == 4
        webhooks = app_data["node"]["webhooks"]
        assert len(webhooks) == 1
        assert webhooks[0]["name"] in webhooks_names
    assert len(apps_data) == count


QUERY_APPS_WITH_SORT = """
    query ($sort_by: AppSortingInput!) {
        apps(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "apps_sort, result_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["facebook", "google"]),
        ({"field": "NAME", "direction": "DESC"}, ["google", "facebook"]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, ["google", "facebook"]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, ["facebook", "google"]),
    ],
)
def test_query_apps_with_sort(
    apps_sort, result_order, staff_api_client, permission_manage_apps,
):
    with freeze_time("2018-05-31 12:00:01"):
        App.objects.create(name="google", is_active=True)
    with freeze_time("2019-05-31 12:00:01"):
        App.objects.create(name="facebook", is_active=True)
    variables = {"sort_by": apps_sort}
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(QUERY_APPS_WITH_SORT, variables)
    content = get_graphql_content(response)
    apps = content["data"]["apps"]["edges"]

    for order, account_name in enumerate(result_order):
        assert apps[order]["node"]["name"] == account_name


def test_apps_query_no_permission(
    staff_api_client, permission_manage_users, permission_manage_staff, app
):
    variables = {"filter": {}}
    response = staff_api_client.post_graphql(
        QUERY_APPS_WITH_FILTER, variables, permissions=[]
    )
    assert_no_permission(response)

    response = staff_api_client.post_graphql(
        QUERY_APPS_WITH_FILTER,
        variables,
        permissions=[permission_manage_users, permission_manage_staff],
    )
    assert_no_permission(response)


QUERY_APP = """
    query ($id: ID! ){
        app(id: $id){
            id
            created
            isActive
            permissions{
                code
                name
            }
            tokens{
                authToken
            }
            webhooks{
                name
            }
            name
        }
    }
    """


def test_app_query(
    staff_api_client, permission_manage_apps, permission_manage_staff, app, webhook
):
    app.permissions.add(permission_manage_staff)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_APP, variables, permissions=[permission_manage_apps],
    )
    content = get_graphql_content(response)

    tokens = app.tokens.all()
    app_data = content["data"]["app"]
    tokens_data = app_data["tokens"]
    assert tokens.count() == 1
    assert tokens_data[0]["authToken"] == tokens.first().auth_token[-4:]

    assert app_data["isActive"] == app.is_active
    assert app_data["permissions"] == [
        {"code": "MANAGE_STAFF", "name": "Manage staff."}
    ]
    assert len(app_data["webhooks"]) == 1
    assert app_data["webhooks"][0]["name"] == webhook.name


def test_app_query_no_permission(
    staff_api_client, permission_manage_staff, permission_manage_users, app
):
    app.permissions.add(permission_manage_staff)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(QUERY_APP, variables, permissions=[])
    assert_no_permission(response)

    response = staff_api_client.post_graphql(
        QUERY_APP,
        variables,
        permissions=[permission_manage_users, permission_manage_staff],
    )
    assert_no_permission(response)


def test_app_with_access_to_resources(
    app_api_client, app, permission_manage_orders, order_with_lines,
):
    query = """
      query {
        orders(first: 5) {
          edges {
            node {
              id
            }
          }
        }
      }
    """
    response = app_api_client.post_graphql(query)
    assert_no_permission(response)
    response = app_api_client.post_graphql(
        query, permissions=[permission_manage_orders]
    )
    get_graphql_content(response)
