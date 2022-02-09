import pytest

from .....app.models import AppExtension
from .....app.types import AppExtensionMount, AppExtensionTarget
from .....core.jwt import jwt_decode
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import AppExtensionMountEnum, AppExtensionTargetEnum

QUERY_APP_EXTENSIONS = """
query ($filter: AppExtensionFilterInput){
    appExtensions(first: 10, filter: $filter){
    edges{
      node{
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
  }
}
"""


def test_app_extensions(staff_api_client, app, permission_manage_products):
    # given
    app_extension = AppExtension.objects.create(
        app=app,
        label="Create product with App",
        url="https://www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
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
    assert app_extension.mount == extension_data["mount"].lower()

    assert app_extension.permissions.count() == 1
    assert len(extension_data["permissions"]) == 1
    permission_code = extension_data["permissions"][0]["code"].lower()
    assert app_extension.permissions.first().codename == permission_code

    assert extension_data["accessToken"]
    decode_token = jwt_decode(extension_data["accessToken"])
    decode_token["permissions"] = ["MANAGE_PRODUCTS"]


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
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
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
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
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
    "filter, expected_count",
    [
        ({}, 4),
        ({"target": AppExtensionTargetEnum.APP_PAGE.name}, 1),
        ({"target": AppExtensionTargetEnum.POPUP.name}, 3),
        ({"mount": [AppExtensionMountEnum.PRODUCT_OVERVIEW_MORE_ACTIONS.name]}, 1),
        ({"mount": [AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name]}, 2),
        (
            {
                "mount": [
                    AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name,
                    AppExtensionMountEnum.PRODUCT_OVERVIEW_MORE_ACTIONS.name,
                ]
            },
            3,
        ),
        (
            {
                "target": AppExtensionTargetEnum.APP_PAGE.name,
                "mount": [
                    AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name,
                    AppExtensionMountEnum.PRODUCT_OVERVIEW_MORE_ACTIONS.name,
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
                mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
                target=AppExtensionTarget.APP_PAGE,
            ),
            AppExtension(
                app=app,
                label="Create product with App2",
                url="https://www.example.com/app-product",
                mount=AppExtensionMount.PRODUCT_DETAILS_MORE_ACTIONS,
                target=AppExtensionTarget.POPUP,
            ),
            AppExtension(
                app=app,
                label="Create product with App3",
                url="https://www.example.com/app-product",
                mount=AppExtensionMount.PRODUCT_OVERVIEW_CREATE,
            ),
            AppExtension(
                app=app,
                label="Create product with App4",
                url="https://www.example.com/app-product",
                mount=AppExtensionMount.PRODUCT_OVERVIEW_CREATE,
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
