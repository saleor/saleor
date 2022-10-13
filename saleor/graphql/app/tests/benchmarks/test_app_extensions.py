import pytest

from .....app.models import AppExtension
from .....app.types import AppExtensionMount
from ....tests.utils import get_graphql_content
from ...enums import AppExtensionMountEnum, AppExtensionTargetEnum


@pytest.mark.count_queries(autouse=False)
def test_app_extensions(
    staff_api_client,
    app,
    permission_manage_products,
    count_queries,
):
    # given
    query = """
    query{
        appExtensions(first: 10){
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

    app_extensions = AppExtension.objects.bulk_create(
        [
            AppExtension(
                app=app,
                label="Create product with App1",
                url="https://www.example.com/app-product",
                mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
            ),
            AppExtension(
                app=app,
                label="Create product with App2",
                url="https://www.example.com/app-product",
                mount=AppExtensionMount.PRODUCT_DETAILS_MORE_ACTIONS,
            ),
            AppExtension(
                app=app,
                label="Create product with App3",
                url="https://www.example.com/app-product",
                mount=AppExtensionMount.PRODUCT_OVERVIEW_CREATE,
            ),
        ]
    )
    app_extensions[0].permissions.add(permission_manage_products)
    app_extensions[1].permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_products], check_no_permissions=False
    )

    # then
    content = get_graphql_content(response)

    extensions_data = content["data"]["appExtensions"]["edges"]

    assert len(extensions_data) == 3


@pytest.mark.parametrize(
    "filter",
    [
        {},
        {"mount": AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name},
        {"target": AppExtensionTargetEnum.POPUP.name},
        {
            "mount": AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name,
            "target": AppExtensionTargetEnum.POPUP.name,
        },
    ],
)
@pytest.mark.count_queries(autouse=False)
def test_app_extensions_with_filter(
    filter,
    staff_api_client,
    app,
    permission_manage_products,
    count_queries,
):
    # given
    query = """
    query ($filter: AppExtensionFilterInput){
        appExtensions(first: 10, filter: $filter){
        edges{
          node{
            label
            url
            target
            id
            mount
            accessToken
            permissions{
              code
            }
          }
        }
      }
    }
    """
    app_extensions = AppExtension.objects.bulk_create(
        [
            AppExtension(
                app=app,
                label="Create product with App1",
                url="https://www.example.com/app-product",
                mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
            ),
            AppExtension(
                app=app,
                label="Create product with App2",
                url="https://www.example.com/app-product",
                mount=AppExtensionMount.PRODUCT_DETAILS_MORE_ACTIONS,
            ),
            AppExtension(
                app=app,
                label="Create product with App3",
                url="https://www.example.com/app-product",
                mount=AppExtensionMount.PRODUCT_OVERVIEW_CREATE,
            ),
        ]
    )
    app_extensions[0].permissions.add(permission_manage_products)
    variables = {"filter": filter}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    get_graphql_content(response)
