import graphene

from .....app.models import AppExtension
from .....app.types import AppExtensionMount
from .....core.jwt import jwt_decode
from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_APP_EXTENSION = """
query ($id: ID!){
    appExtension(id: $id){
        label
        url
        mount
        target
        id
        accessToken
        permissions{
            code
        }
    }
}
"""


def test_app_extension_staff_user(app, staff_api_client, permission_manage_products):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]
    assert app_extension.label == extension_data["label"]
    assert app_extension.url == extension_data["url"]
    assert app_extension.mount == extension_data["mount"].lower()
    assert app_extension.target == extension_data["target"].lower()

    assert app_extension.permissions.count() == 1
    assert len(extension_data["permissions"]) == 1
    permission_code = extension_data["permissions"][0]["code"].lower()
    assert app_extension.permissions.first().codename == permission_code


def test_app_extension_by_app(app, app_api_client, permission_manage_products):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]
    assert app_extension.label == extension_data["label"]
    assert app_extension.url == extension_data["url"]
    assert app_extension.mount == extension_data["mount"].lower()
    assert app_extension.target == extension_data["target"].lower()

    assert app_extension.permissions.count() == 1
    assert len(extension_data["permissions"]) == 1
    permission_code = extension_data["permissions"][0]["code"].lower()
    assert app_extension.permissions.first().codename == permission_code


def test_app_extension_normal_user(app, user_api_client, permission_manage_products):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = user_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
    )

    # then
    assert_no_permission(response)


def test_app_extension_staff_user_without_all_permissions(
    app, staff_api_client, permission_manage_products, permission_manage_orders
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
        permissions=[permission_manage_orders],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]
    assert extension_data["accessToken"] is None


def test_app_extension_staff_user_fetching_access_token(
    app,
    staff_api_client,
    permission_manage_orders,
    permission_manage_products,
    permission_manage_apps,
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products, permission_manage_orders)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
        permissions=[
            permission_manage_orders,
            permission_manage_products,
            permission_manage_apps,
        ],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]

    assert extension_data["accessToken"]
    decoded_token = jwt_decode(extension_data["accessToken"])
    assert set(decoded_token["permissions"]) == set(
        ["MANAGE_PRODUCTS", "MANAGE_ORDERS"]
    )


def test_app_extension_staff_user_partial_permission(
    app,
    staff_api_client,
    permission_manage_orders,
    permission_manage_products,
    permission_manage_apps,
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products, permission_manage_orders)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION,
        variables,
        permissions=[permission_manage_orders, permission_manage_apps],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    extension_data = content["data"]["appExtension"]

    assert extension_data["accessToken"] is None


QUERY_APP_EXTENSION_WITH_APP = """
query ($id: ID!){
    appExtension(id: $id){
        label
        url
        mount
        target
        id
        permissions{
            code
        }
        app{
            id
        }
    }
}
"""


def test_app_extension_with_app_query_by_staff_without_permissions(
    app, staff_api_client, permission_manage_products
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION_WITH_APP,
        variables,
    )

    # then
    assert_no_permission(response)


def test_app_extension_with_app_query_by_app_without_permissions(
    external_app, app_api_client, permission_manage_products
):
    # given
    app_extension = AppExtension.objects.create(
        app=external_app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_EXTENSION_WITH_APP,
        variables,
    )

    # then
    assert_no_permission(response)


def test_app_extension_with_app_query_by_app_with_permissions(
    external_app,
    app,
    permission_manage_apps,
    app_api_client,
    permission_manage_products,
):
    # given
    app_extension = AppExtension.objects.create(
        app=external_app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    app.permissions.add(permission_manage_apps)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_EXTENSION_WITH_APP,
        variables,
    )

    # then
    get_graphql_content(response)


def test_app_extension_with_app_query_by_owner_app(
    app, app_api_client, permission_manage_products
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_EXTENSION_WITH_APP,
        variables,
    )

    # then
    get_graphql_content(response)


def test_app_extension_with_app_query_by_staff_with_permissions(
    external_app, app, permission_manage_apps, staff_api_client
):
    # given
    app_extension = AppExtension.objects.create(
        app=external_app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )

    id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSION_WITH_APP, variables, permissions=[permission_manage_apps]
    )

    # then
    get_graphql_content(response)
