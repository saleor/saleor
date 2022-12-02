import graphene
import pytest
from freezegun import freeze_time

from .....app.models import App
from .....app.types import AppType
from .....core.jwt import create_access_token_for_app
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
                    metafield(key: "test")
                    metafields(keys: ["test"])
                    extensions{
                        id
                        label
                        url
                        mount
                        target
                        permissions{
                            code
                        }
                    }
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
    app_with_extensions,
    external_app,
    app_filter,
    count,
):
    app, app_extensions = app_with_extensions
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


def test_apps_with_extensions_query(
    staff_api_client,
    permission_manage_apps,
    permission_manage_orders,
    app_with_extensions,
):
    # given
    app, app_extensions = app_with_extensions

    # when
    response = staff_api_client.post_graphql(
        QUERY_APPS_WITH_FILTER,
        permissions=[permission_manage_apps, permission_manage_orders],
    )

    # then
    content = get_graphql_content(response)

    apps_data = content["data"]["apps"]["edges"]

    assert len(apps_data) == 1
    app_data = apps_data[0]["node"]

    extensions_data = app_data["extensions"]
    returned_ids = {e["id"] for e in extensions_data}
    returned_labels = {e["label"] for e in extensions_data}
    returned_mounts = {e["mount"].lower() for e in extensions_data}
    returned_targets = {e["target"].lower() for e in extensions_data}
    returned_permission_codes = [e["permissions"] for e in extensions_data]
    for app_extension in app_extensions:
        global_id = graphene.Node.to_global_id("AppExtension", app_extension.id)
        assert global_id in returned_ids
        assert app_extension.label in returned_labels
        assert app_extension.mount in returned_mounts
        assert app_extension.target in returned_targets
        assigned_permissions = [p.codename for p in app_extension.permissions.all()]
        assigned_permissions = [{"code": p.upper()} for p in assigned_permissions]
        assert assigned_permissions in returned_permission_codes


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


QUERY_APPS_FOR_FEDERATION = """
    query GetAppInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
            __typename
            ... on App {
                id
                name
            }
        }
    }
"""


def test_query_app_for_federation(staff_api_client, app, permission_manage_apps):
    app_id = graphene.Node.to_global_id("App", app.pk)
    variables = {
        "representations": [
            {
                "__typename": "App",
                "id": app_id,
            },
        ],
    }

    response = staff_api_client.post_graphql(
        QUERY_APPS_FOR_FEDERATION,
        variables,
        permissions=[permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "App",
            "id": app_id,
            "name": app.name,
        }
    ]


def test_query_app_for_federation_without_permission(api_client, app):
    app_id = graphene.Node.to_global_id("App", app.pk)
    variables = {
        "representations": [
            {
                "__typename": "App",
                "id": app_id,
            },
        ],
    }

    response = api_client.post_graphql(QUERY_APPS_FOR_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


QUERY_APPS_AVAILABLE_FOR_STAFF_WITHOUT_MANAGE_APPS = """
    query{
        apps(first: 5){
            edges{
                node{
                    id
                    isActive
                    permissions{
                        name
                        code
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
                    accessToken
                    extensions{
                        id
                        label
                        url
                        mount
                        target
                        permissions{
                            code
                        }
                    }
                }
            }
        }
    }
"""


@freeze_time("2018-05-31 12:00:01")
def test_apps_query_staff_without_permissions(
    staff_api_client,
    staff_user,
    permission_manage_apps,
    permission_manage_orders,
    app,
):
    # given
    app.type = AppType.THIRDPARTY
    app.save()
    # when
    response = staff_api_client.post_graphql(
        QUERY_APPS_AVAILABLE_FOR_STAFF_WITHOUT_MANAGE_APPS,
    )

    # then
    content = get_graphql_content(response)

    apps_data = content["data"]["apps"]["edges"]

    assert len(apps_data) == 1
    app_data = apps_data[0]["node"]
    expected_id = graphene.Node.to_global_id("App", app.id)
    assert app_data["id"] == expected_id
    assert app_data["accessToken"] == create_access_token_for_app(app, staff_user)


def test_apps_query_for_normal_user(
    user_api_client, permission_manage_users, permission_manage_staff, app
):
    # when
    response = user_api_client.post_graphql(
        QUERY_APPS_AVAILABLE_FOR_STAFF_WITHOUT_MANAGE_APPS,
    )

    # then
    assert_no_permission(response)


QUERY_APPS_WITH_METADATA = """
    query{
        apps(first: 5){
            edges{
                node{
                    id
                    metadata{
                        key
                        value
                    }

                }
            }
        }
    }
"""


def test_apps_query_with_metadata_staff_user_without_permissions(
    staff_api_client,
    staff_user,
    app,
):
    # given
    app.type = AppType.THIRDPARTY
    app.store_value_in_metadata({"test": "123"})
    app.save()

    # when
    response = staff_api_client.post_graphql(
        QUERY_APPS_WITH_METADATA,
    )

    # then
    assert_no_permission(response)


QUERY_APPS_WITH_METAFIELD = """
    query{
        apps(first: 5){
            edges{
                node{
                    id
                    metafield(key: "test")
                }
            }
        }
    }
"""


def test_apps_query_with_metafield_staff_user_without_permissions(
    staff_api_client,
    staff_user,
    app,
):
    # given
    app.type = AppType.THIRDPARTY
    app.store_value_in_metadata({"test": "123"})
    app.save()

    # when
    response = staff_api_client.post_graphql(
        QUERY_APPS_WITH_METAFIELD,
    )

    # then
    assert_no_permission(response)


QUERY_APPS_WITH_METAFIELDS = """
    query{
        apps(first: 5){
            edges{
                node{
                    id
                    metafields(keys: ["test"])
                }
            }
        }
    }
"""


def test_apps_query_with_metafields_staff_user_without_permissions(
    staff_api_client,
    staff_user,
    app,
):
    # given
    app.type = AppType.THIRDPARTY
    app.store_value_in_metadata({"test": "123"})
    app.save()

    # when
    response = staff_api_client.post_graphql(
        QUERY_APPS_WITH_METAFIELDS,
    )

    # then
    assert_no_permission(response)
