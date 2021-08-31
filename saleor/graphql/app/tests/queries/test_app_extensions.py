import pytest

from .....app.models import AppExtension
from .....app.types import AppExtensionTarget, AppExtensionType, AppExtensionView
from .....core.jwt import jwt_decode
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import AppExtensionTargetEnum, AppExtensionTypeEnum, AppExtensionViewEnum

QUERY_APP_EXTENSIONS = """
query ($filter: AppExtensionFilterInput){
    appExtensions(first: 10, filter: $filter){
    edges{
      node{
        label
        url
        view
        target
        id
        type
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
        view=AppExtensionView.PRODUCT,
        type=AppExtensionType.OVERVIEW,
        target=AppExtensionTarget.MORE_ACTIONS,
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
    assert app_extension.view == extension_data["view"].lower()
    assert app_extension.target == extension_data["target"].lower()
    assert app_extension.type == extension_data["type"].lower()

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
        view=AppExtensionView.PRODUCT,
        type=AppExtensionType.OVERVIEW,
        target=AppExtensionTarget.MORE_ACTIONS,
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
        view=AppExtensionView.PRODUCT,
        type=AppExtensionType.OVERVIEW,
        target=AppExtensionTarget.MORE_ACTIONS,
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
        ({}, 3),
        ({"view": AppExtensionViewEnum.PRODUCT.name}, 3),
        ({"target": AppExtensionTargetEnum.CREATE.name}, 1),
        ({"type": AppExtensionTypeEnum.OVERVIEW.name}, 2),
        (
            {
                "type": AppExtensionTypeEnum.OVERVIEW.name,
                "view": AppExtensionViewEnum.PRODUCT.name,
            },
            2,
        ),
        (
            {
                "type": AppExtensionTypeEnum.DETAILS.name,
                "target": AppExtensionTargetEnum.CREATE.name,
            },
            0,
        ),
        (
            {
                "type": AppExtensionTypeEnum.DETAILS.name,
                "target": AppExtensionTargetEnum.MORE_ACTIONS.name,
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
                view=AppExtensionView.PRODUCT,
                type=AppExtensionType.OVERVIEW,
                target=AppExtensionTarget.MORE_ACTIONS,
            ),
            AppExtension(
                app=app,
                label="Create product with App2",
                url="https://www.example.com/app-product",
                view=AppExtensionView.PRODUCT,
                type=AppExtensionType.DETAILS,
                target=AppExtensionTarget.MORE_ACTIONS,
            ),
            AppExtension(
                app=app,
                label="Create product with App3",
                url="https://www.example.com/app-product",
                view=AppExtensionView.PRODUCT,
                type=AppExtensionType.OVERVIEW,
                target=AppExtensionTarget.CREATE,
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
