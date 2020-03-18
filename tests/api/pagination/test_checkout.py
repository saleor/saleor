import pytest

from saleor.checkout.models import Checkout
from tests.api.utils import get_graphql_content


@pytest.fixture
def checkouts_for_pagination():
    return Checkout.objects.bulk_create(
        [
            Checkout(token="1fa91751-fd0a-45ca-8633-4bac9f5cb2a7",),
            Checkout(token="63256386-a913-4dea-bee9-40c3f1faf952",),
            Checkout(token="31ad7bf3-2e0d-435d-aa8c-c23abaf6a934",),
            Checkout(token="308a080e-29e1-4eab-b856-148b925409c1",),
            Checkout(token="3e6140c5-5784-4965-8dc0-4d5ee4b9409a",),
        ]
    )


QUERY_CHECKOUTS_PAGINATION = """
    query ($first: Int, $last: Int, $after: String, $before: String){
        checkouts(first: $first, last: $last, after: $after, before: $before) {
            edges {
                node {
                    token
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
def test_checkouts_pagination_forward(
    page_size, staff_api_client, permission_manage_checkouts, checkouts_for_pagination,
):
    end_cursor = None
    has_next_page = True
    checkout_count = 0
    while has_next_page:
        variables = {"first": page_size, "after": end_cursor}
        response = staff_api_client.post_graphql(
            QUERY_CHECKOUTS_PAGINATION,
            variables,
            permissions=[permission_manage_checkouts],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        page_info = content["data"]["checkouts"]["pageInfo"]
        has_next_page = page_info["hasNextPage"]
        end_cursor = page_info["endCursor"]
        checkout_count += len(content["data"]["checkouts"]["edges"])
    assert checkout_count == len(checkouts_for_pagination)


@pytest.mark.parametrize("page_size", [1, 3, 6])
def test_checkouts_pagination_backward(
    page_size, staff_api_client, permission_manage_checkouts, checkouts_for_pagination,
):
    start_cursor = None
    has_previous_page = True
    checkout_count = 0
    while has_previous_page:
        variables = {"last": page_size, "before": start_cursor}
        response = staff_api_client.post_graphql(
            QUERY_CHECKOUTS_PAGINATION,
            variables,
            permissions=[permission_manage_checkouts],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        page_info = content["data"]["checkouts"]["pageInfo"]
        has_previous_page = page_info["hasPreviousPage"]
        start_cursor = page_info["startCursor"]
        checkout_count += len(content["data"]["checkouts"]["edges"])
    assert checkout_count == len(checkouts_for_pagination)


def test_checkouts_pagination_order(
    staff_api_client, permission_manage_checkouts, checkouts_for_pagination,
):
    page_size = len(checkouts_for_pagination)

    variables = {"first": page_size, "after": None}
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUTS_PAGINATION,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    edges_forward = content["data"]["checkouts"]["edges"]

    variables = {"last": page_size, "before": None}
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUTS_PAGINATION,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    edges_backward = content["data"]["checkouts"]["edges"]

    assert edges_forward == edges_backward


def test_checkouts_pagination_previous_page_using_last(
    staff_api_client, permission_manage_checkouts, checkouts_for_pagination
):
    page_size = 2

    variables = {"first": page_size, "after": None}
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUTS_PAGINATION,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    first_page_edges_forward = content["data"]["checkouts"]["edges"]
    first_page_info = content["data"]["checkouts"]["pageInfo"]

    variables = {"first": page_size, "after": first_page_info["endCursor"]}
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUTS_PAGINATION,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    second_page_info = content["data"]["checkouts"]["pageInfo"]

    variables = {"last": page_size, "before": second_page_info["startCursor"]}
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUTS_PAGINATION,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    first_page_edges_backward = content["data"]["checkouts"]["edges"]

    assert first_page_edges_forward == first_page_edges_backward
