import pytest
from freezegun import freeze_time

from .....app.models import App
from .....webhook.models import Webhook
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import AppTypeEnum

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
                    type
                    aboutApp
                    dataPrivacy
                    dataPrivacyUrl
                    homepageUrl
                    supportUrl
                    configurationUrl
                    appUrl
                }
            }
        }
    }
    """


@pytest.mark.parametrize(
    "app_filter, count",
    (
        ({"search": "Sample"}, 1),
        ({"isActive": False}, 1),
        ({}, 2),
        ({"type": AppTypeEnum.THIRDPARTY.name}, 1),
        ({"type": AppTypeEnum.LOCAL.name}, 1),
    ),
)
def test_apps_query(
    staff_api_client,
    permission_manage_apps,
    permission_manage_orders,
    app,
    external_app,
    app_filter,
    count,
):
    external_app.is_active = False
    external_app.save()
    webhooks = Webhook.objects.bulk_create(
        [
            Webhook(app=app, name="first", target_url="http://www.example.com/test"),
            Webhook(app=external_app, name="second", target_url="http://www.exa.com/s"),
        ]
    )
    webhooks_names = [w.name for w in webhooks]

    variables = {"filter": app_filter}
    response = staff_api_client.post_graphql(
        QUERY_APPS_WITH_FILTER,
        variables,
        permissions=[permission_manage_apps, permission_manage_orders],
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
    apps_sort,
    result_order,
    staff_api_client,
    permission_manage_apps,
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
