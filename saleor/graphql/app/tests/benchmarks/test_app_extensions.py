import pytest

from .....app.models import AppExtension
from .....app.types import AppExtensionTarget, AppExtensionType, AppExtensionView
from ....tests.utils import get_graphql_content
from ...enums import AppExtensionTargetEnum, AppExtensionTypeEnum, AppExtensionViewEnum


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
        {"view": AppExtensionViewEnum.PRODUCT.name},
        {"target": AppExtensionTargetEnum.CREATE.name},
        {"type": AppExtensionTypeEnum.OVERVIEW.name},
        {
            "type": AppExtensionTypeEnum.OVERVIEW.name,
            "view": AppExtensionViewEnum.PRODUCT.name,
        },
        {
            "type": AppExtensionTypeEnum.DETAILS.name,
            "target": AppExtensionTargetEnum.CREATE.name,
        },
        {
            "type": AppExtensionTypeEnum.DETAILS.name,
            "target": AppExtensionTargetEnum.MORE_ACTIONS.name,
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
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    get_graphql_content(response)
