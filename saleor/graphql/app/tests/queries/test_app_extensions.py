import pytest

from .....app.models import AppExtension
from .....app.types import DeprecatedAppExtensionMount, DeprecatedAppExtensionTarget
from .....core.jwt import jwt_decode
from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_APP_EXTENSIONS = """
query ($filter: AppExtensionFilterInput){
    appExtensions(first: 10, filter: $filter){
    edges{
      node{
        label
        url
        mountName
        targetName
        settings
        id
        accessToken
        permissions{
          code
        }
      }
    }
  }
}
"""


def test_app_extensions(staff_api_client, app, permission_manage_products):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=DeprecatedAppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
        http_target_method="POST",
        target=DeprecatedAppExtensionTarget.WIDGET,
    )
    app_extension.permissions.add(permission_manage_products)
    variables = {}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSIONS,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)

    extensions_data = content["data"]["appExtensions"]["edges"]

    assert len(extensions_data) == 1
    extension_data = extensions_data[0]["node"]
    assert app_extension.label == extension_data["label"]
    assert app_extension.url == extension_data["url"]
    assert app_extension.mount == extension_data["mountName"].lower()

    assert app_extension.permissions.count() == 1
    assert len(extension_data["permissions"]) == 1
    permission_code = extension_data["permissions"][0]["code"].lower()
    assert app_extension.permissions.first().codename == permission_code

    assert extension_data["accessToken"]
    decode_token = jwt_decode(extension_data["accessToken"])
    decode_token["permissions"] = ["MANAGE_PRODUCTS"]

    assert extension_data["mountName"] == "PRODUCT_OVERVIEW_MORE_ACTIONS"
    assert extension_data["targetName"] == "WIDGET"


def test_app_extensions_app_not_active(
    staff_api_client, app, permission_manage_products
):
    # given
    app.is_active = False
    app.save()
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=DeprecatedAppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    variables = {}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSIONS,
        variables,
    )

    # then
    content = get_graphql_content(response)

    extensions_data = content["data"]["appExtensions"]["edges"]

    assert len(extensions_data) == 0


def test_app_extensions_app_removed_app(
    staff_api_client, removed_app, permission_manage_products
):
    # given
    app_extension = AppExtension.objects.create(
        app=removed_app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=DeprecatedAppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    variables = {}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSIONS,
        variables,
    )

    # then
    content = get_graphql_content(response)

    extensions_data = content["data"]["appExtensions"]["edges"]

    assert len(extensions_data) == 0


def test_app_extensions_user_not_staff(
    user_api_client, app, permission_manage_products
):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=DeprecatedAppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    app_extension.permissions.add(permission_manage_products)
    variables = {}

    # when
    response = user_api_client.post_graphql(
        QUERY_APP_EXTENSIONS,
        variables,
    )

    # then
    assert_no_permission(response)


@pytest.mark.parametrize(
    ("filter", "expected_count"),
    [
        ({}, 4),
        ({"targetName": "APP_PAGE"}, 1),
        ({"targetName": "POPUP"}, 3),
        ({"mountName": ["PRODUCT_OVERVIEW_MORE_ACTIONS"]}, 1),
        ({"mountName": ["PRODUCT_OVERVIEW_CREATE"]}, 2),
        (
            {
                "mountName": [
                    "PRODUCT_OVERVIEW_CREATE",
                    "PRODUCT_OVERVIEW_MORE_ACTIONS",
                ]
            },
            3,
        ),
        (
            {
                "targetName": "APP_PAGE",
                "mountName": [
                    "PRODUCT_OVERVIEW_CREATE",
                    "PRODUCT_OVERVIEW_MORE_ACTIONS",
                ],
            },
            1,
        ),
    ],
)
def test_app_extensions_with_filter(
    filter, expected_count, staff_api_client, app, permission_manage_products
):
    # given
    app_extensions = AppExtension.objects.bulk_create(
        [
            AppExtension(
                app=app,
                label="Create product with App1",
                url="https://www.example.com/app-product",
                mount=DeprecatedAppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
                target=DeprecatedAppExtensionTarget.APP_PAGE,
            ),
            AppExtension(
                app=app,
                label="Create product with App2",
                url="https://www.example.com/app-product",
                mount=DeprecatedAppExtensionMount.PRODUCT_DETAILS_MORE_ACTIONS,
                target=DeprecatedAppExtensionTarget.POPUP,
            ),
            AppExtension(
                app=app,
                label="Create product with App3",
                url="https://www.example.com/app-product",
                mount=DeprecatedAppExtensionMount.PRODUCT_OVERVIEW_CREATE,
            ),
            AppExtension(
                app=app,
                label="Create product with App4",
                url="https://www.example.com/app-product",
                mount=DeprecatedAppExtensionMount.PRODUCT_OVERVIEW_CREATE,
            ),
        ]
    )
    app_extensions[0].permissions.add(permission_manage_products)
    variables = {"filter": filter}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSIONS,
        variables,
    )

    # then
    content = get_graphql_content(response)

    extensions_data = content["data"]["appExtensions"]["edges"]

    assert len(extensions_data) == expected_count


@pytest.mark.parametrize(
    ("filter", "expected_count"),
    [
        ({}, 4),
        ({"targetName": "APP_PAGE"}, 1),
        ({"targetName": "POPUP"}, 3),
        ({"mountName": ["PRODUCT_OVERVIEW_MORE_ACTIONS"]}, 1),
        ({"mountName": ["PRODUCT_OVERVIEW_CREATE"]}, 2),
        ({"mountName": ["PRODUCT_DETAILS_MORE_ACTIONS"]}, 1),
        (
            {
                "mountName": [
                    "PRODUCT_OVERVIEW_CREATE",
                    "PRODUCT_OVERVIEW_MORE_ACTIONS",
                ]
            },
            3,
        ),
        (
            {
                "mountName": [
                    "PRODUCT_OVERVIEW_CREATE",
                    "PRODUCT_DETAILS_MORE_ACTIONS",
                ]
            },
            3,
        ),
        (
            {
                "targetName": "APP_PAGE",
                "mountName": ["PRODUCT_OVERVIEW_MORE_ACTIONS"],
            },
            1,
        ),
        (
            {
                "targetName": "POPUP",
                "mountName": ["PRODUCT_OVERVIEW_CREATE"],
            },
            2,
        ),
        (
            {
                "targetName": "APP_PAGE",
                "mountName": ["PRODUCT_DETAILS_MORE_ACTIONS"],
            },
            0,
        ),
        (
            {
                "targetName": "POPUP",
                "mountName": [
                    "PRODUCT_OVERVIEW_CREATE",
                    "PRODUCT_DETAILS_MORE_ACTIONS",
                ],
            },
            3,
        ),
    ],
)
def test_app_extensions_with_name_filter(
    filter, expected_count, staff_api_client, app, permission_manage_products
):
    # given
    AppExtension.objects.bulk_create(
        [
            AppExtension(
                app=app,
                label="Create product with App1",
                url="https://www.example.com/app-product",
                mount=DeprecatedAppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
                target=DeprecatedAppExtensionTarget.APP_PAGE,
            ),
            AppExtension(
                app=app,
                label="Create product with App2",
                url="https://www.example.com/app-product",
                mount=DeprecatedAppExtensionMount.PRODUCT_DETAILS_MORE_ACTIONS,
                target=DeprecatedAppExtensionTarget.POPUP,
            ),
            AppExtension(
                app=app,
                label="Create product with App3",
                url="https://www.example.com/app-product",
                mount=DeprecatedAppExtensionMount.PRODUCT_OVERVIEW_CREATE,
            ),
            AppExtension(
                app=app,
                label="Create product with App4",
                url="https://www.example.com/app-product",
                mount=DeprecatedAppExtensionMount.PRODUCT_OVERVIEW_CREATE,
            ),
        ]
    )
    variables = {"filter": filter}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSIONS,
        variables,
    )

    # then
    content = get_graphql_content(response)

    extensions_data = content["data"]["appExtensions"]["edges"]

    assert len(extensions_data) == expected_count


# Behavior specific to 3.22 which handles backwards compatibility
@pytest.mark.parametrize(
    ("mount_value", "target_value", "filter", "expected_count"),
    [
        # Test with lowercase values in database, uppercase input
        (
            "order_details_widgets",
            "widget",
            {"mountName": ["ORDER_DETAILS_WIDGETS"]},
            1,
        ),
        ("order_details_widgets", "widget", {"targetName": "WIDGET"}, 1),
        (
            "order_details_widgets",
            "widget",
            {"mountName": ["ORDER_DETAILS_WIDGETS"], "targetName": "WIDGET"},
            1,
        ),
        # Test with lowercase values in database, lowercase input
        (
            "order_details_widgets",
            "widget",
            {"mountName": ["order_details_widgets"]},
            1,
        ),
        ("order_details_widgets", "widget", {"targetName": "widget"}, 1),
        (
            "order_details_widgets",
            "widget",
            {"mountName": ["order_details_widgets"], "targetName": "widget"},
            1,
        ),
        # Test mixed case input
        (
            "order_details_widgets",
            "widget",
            {"mountName": ["Order_Details_Widgets"]},
            1,
        ),
        ("order_details_widgets", "widget", {"targetName": "WiDgEt"}, 1),
    ],
)
def test_app_extensions_case_insensitive_filter(
    mount_value,
    target_value,
    filter,
    expected_count,
    staff_api_client,
    app,
):
    # given
    AppExtension.objects.create(
        app=app,
        label="Test Extension",
        url="https://www.example.com/app-extension",
        mount=mount_value,
        target=target_value,
        http_target_method="POST",
    )
    variables = {"filter": filter}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_EXTENSIONS,
        variables,
    )

    # then
    content = get_graphql_content(response)
    extensions_data = content["data"]["appExtensions"]["edges"]

    assert len(extensions_data) == expected_count
