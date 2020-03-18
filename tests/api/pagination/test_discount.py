from decimal import Decimal

import pytest
from django.utils import timezone
from freezegun import freeze_time

from saleor.discount import DiscountValueType
from saleor.discount.models import Sale
from tests.api.utils import get_graphql_content


@pytest.fixture
@freeze_time("2020-03-18 12:00:00", auto_tick_seconds=60)
def sales_for_pagination(db):
    now = timezone.now()
    return Sale.objects.bulk_create(
        [
            Sale(
                name="Sale1",
                start_date=now + timezone.timedelta(hours=4),
                end_date=now + timezone.timedelta(hours=14),
                type=DiscountValueType.PERCENTAGE,
                value=Decimal("1"),
            ),
            Sale(
                name="Sale2",
                end_date=now + timezone.timedelta(hours=1),
                value=Decimal("7"),
            ),
            Sale(
                name="Sale3",
                end_date=now + timezone.timedelta(hours=2),
                type=DiscountValueType.PERCENTAGE,
                value=Decimal("5"),
            ),
            Sale(
                name="Sale4",
                end_date=now + timezone.timedelta(hours=1),
                value=Decimal("5"),
            ),
            Sale(
                name="Sale15",
                start_date=now + timezone.timedelta(hours=1),
                end_date=now + timezone.timedelta(hours=2),
                value=Decimal("25"),
            ),
        ]
    )


QUERY_SALES_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: SaleSortingInput, $filter: SaleFilterInput
    ){
        sales(
            first: $first, last: $last, after: $after, before: $before,
            sortBy: $sortBy, filter: $filter
        ) {
            edges {
                node {
                    name
                }
            }
            pageInfo{
                startCursor
                endCursor
                hasNextPage
                hasPreviousPage
            }
        }
    }
"""


@pytest.mark.parametrize("page_size", [1, 3, 6])
def test_sales_pagination_forward(
    page_size, staff_api_client, permission_manage_discounts, sales_for_pagination,
):
    end_cursor = None
    has_next_page = True
    sale_count = 0
    while has_next_page:
        variables = {"first": page_size, "after": end_cursor}
        response = staff_api_client.post_graphql(
            QUERY_SALES_PAGINATION,
            variables,
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        page_info = content["data"]["sales"]["pageInfo"]
        has_next_page = page_info["hasNextPage"]
        end_cursor = page_info["endCursor"]
        sale_count += len(content["data"]["sales"]["edges"])
    assert sale_count == len(sales_for_pagination)


@pytest.mark.parametrize("page_size", [1, 3, 6])
def test_sales_pagination_backward(
    page_size, staff_api_client, permission_manage_discounts, sales_for_pagination,
):
    start_cursor = None
    has_previous_page = True
    sale_count = 0
    while has_previous_page:
        variables = {"last": page_size, "before": start_cursor}
        response = staff_api_client.post_graphql(
            QUERY_SALES_PAGINATION,
            variables,
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        page_info = content["data"]["sales"]["pageInfo"]
        has_previous_page = page_info["hasPreviousPage"]
        start_cursor = page_info["startCursor"]
        sale_count += len(content["data"]["sales"]["edges"])
    assert sale_count == len(sales_for_pagination)


def test_sales_pagination_order(
    staff_api_client, permission_manage_discounts, sales_for_pagination,
):
    page_size = len(sales_for_pagination)

    variables = {"first": page_size, "after": None}
    response = staff_api_client.post_graphql(
        QUERY_SALES_PAGINATION,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    edges_forward = content["data"]["sales"]["edges"]

    variables = {"last": page_size, "before": None}
    response = staff_api_client.post_graphql(
        QUERY_SALES_PAGINATION,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    edges_backward = content["data"]["sales"]["edges"]

    assert edges_forward == edges_backward


def test_sales_pagination_previous_page_using_last(
    staff_api_client, permission_manage_discounts, sales_for_pagination
):
    page_size = 2

    variables = {"first": page_size, "after": None}
    response = staff_api_client.post_graphql(
        QUERY_SALES_PAGINATION,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    first_page_edges_forward = content["data"]["sales"]["edges"]
    first_page_info = content["data"]["sales"]["pageInfo"]

    variables = {"first": page_size, "after": first_page_info["endCursor"]}
    response = staff_api_client.post_graphql(
        QUERY_SALES_PAGINATION,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    second_page_info = content["data"]["sales"]["pageInfo"]

    variables = {"last": page_size, "before": second_page_info["startCursor"]}
    response = staff_api_client.post_graphql(
        QUERY_SALES_PAGINATION,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    first_page_edges_backward = content["data"]["sales"]["edges"]

    assert first_page_edges_forward == first_page_edges_backward


@pytest.mark.parametrize(
    "sort_by, sales_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["Sale1", "Sale15", "Sale2"]),
        ({"field": "NAME", "direction": "DESC"}, ["Sale4", "Sale3", "Sale2"]),
        ({"field": "START_DATE", "direction": "ASC"}, ["Sale2", "Sale3", "Sale4"]),
        ({"field": "END_DATE", "direction": "ASC"}, ["Sale2", "Sale4", "Sale3"]),
        ({"field": "VALUE", "direction": "ASC"}, ["Sale1", "Sale3", "Sale4"]),
        ({"field": "TYPE", "direction": "ASC"}, ["Sale2", "Sale4", "Sale15"]),
    ],
)
def test_sales_pagination_with_sorting(
    sort_by,
    sales_order,
    staff_api_client,
    permission_manage_discounts,
    sales_for_pagination,
):
    page_size = 3

    variables = {"first": page_size, "after": None, "sortBy": sort_by}
    response = staff_api_client.post_graphql(
        QUERY_SALES_PAGINATION,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    sales_nodes = content["data"]["sales"]["edges"]
    assert sales_order[0] == sales_nodes[0]["node"]["name"]
    assert sales_order[1] == sales_nodes[1]["node"]["name"]
    assert sales_order[2] == sales_nodes[2]["node"]["name"]
    assert len(sales_nodes) == page_size


@pytest.mark.parametrize(
    "filter_by, sales_order",
    [
        ({"status": "SCHEDULED"}, ["Sale1", "Sale15"]),
        ({"status": "ACTIVE"}, ["Sale2", "Sale3"]),
        ({"saleType": "FIXED"}, ["Sale2", "Sale4"]),
        ({"saleType": "PERCENTAGE"}, ["Sale1", "Sale3"]),
        ({"started": {"gte": "2020-03-18T13:00:00+00:00"}}, ["Sale1", "Sale15"]),
        ({"started": {"lte": "2020-03-18T13:00:00+00:00"}}, ["Sale2", "Sale3"]),
    ],
)
@freeze_time("2020-03-18 12:15:00")
def test_sales_pagination_with_filtering(
    filter_by,
    sales_order,
    staff_api_client,
    permission_manage_discounts,
    sales_for_pagination,
):
    page_size = 2

    variables = {"first": page_size, "after": None, "filter": filter_by}
    response = staff_api_client.post_graphql(
        QUERY_SALES_PAGINATION,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    sales_nodes = content["data"]["sales"]["edges"]
    assert sales_order[0] == sales_nodes[0]["node"]["name"]
    assert sales_order[1] == sales_nodes[1]["node"]["name"]
    assert len(sales_nodes) == page_size
