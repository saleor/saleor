import pytest

from saleor.graphql.core.connection import to_global_cursor
from saleor.account.models import User
from saleor.page.models import Page
from tests.api.utils import get_graphql_content


@pytest.mark.parametrize(
    "order_by, cursor_fields",
    [
        (
            {"field": "LAST_NAME", "direction": "ASC"},
            ["last_name", "first_name", "pk"],
        ),
        (None, ["email"]),
    ],
)
def test_user_pagination(
    order_by, cursor_fields, staff_api_client, permission_manage_users
):
    query = """
        query ($after: String, $sortBy: UserSortingInput){
          customers(first: 3, after: $after, sortBy: $sortBy) {
            edges {
              node {
                firstName
                lastName
                email
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
    user1 = User.objects.create_user("u1@m.com", first_name="Alan", last_name="Alker")
    user2 = User.objects.create_user("u2@m.com", first_name="Bob", last_name="Bylan")
    user3 = User.objects.create_user("u3@m.com", first_name="Clark", last_name="Cent")
    user4 = User.objects.create_user("u4@m.com", first_name="Danny", last_name="DeVito")
    user5 = User.objects.create_user("u5@m.com", first_name="Ellen", last_name="Egenes")

    user1_cursor = to_global_cursor([getattr(user1, field) for field in cursor_fields])
    user3_cursor = to_global_cursor([getattr(user3, field) for field in cursor_fields])
    user4_cursor = to_global_cursor([getattr(user4, field) for field in cursor_fields])
    user5_cursor = to_global_cursor([getattr(user5, field) for field in cursor_fields])
    variables = {"after": None, "sortBy": order_by}

    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    page_info = content["data"]["customers"]["pageInfo"]

    assert not page_info["hasPreviousPage"]
    assert page_info["hasNextPage"]
    assert page_info["startCursor"] == user1_cursor
    assert page_info["endCursor"] == user3_cursor

    variables = {"after": user3_cursor, "sortBy": order_by}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    page_info = content["data"]["customers"]["pageInfo"]

    assert page_info["hasPreviousPage"]
    assert not page_info["hasNextPage"]
    assert page_info["startCursor"] == user4_cursor
    assert page_info["endCursor"] == user5_cursor


@pytest.mark.parametrize(
    "order_by, cursor_fields",
    [
        (
            {"field": "VISIBILITY", "direction": "ASC"},
            ["is_published", "title", "slug"],
        ),
        (None, ["slug"]),
    ],
)
def test_page_pagination(
    order_by, cursor_fields, staff_api_client, permission_manage_pages
):
    query = """
        query ($after: String, $sortBy: PageSortingInput){
          pages(first: 3, after: $after, sortBy: $sortBy) {
            edges {
              node {
                  title
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
    page1 = Page.objects.create(title="About", slug="about", is_published=False)
    page2 = Page.objects.create(title="About2", slug="about2", is_published=False)
    page3 = Page.objects.create(title="About3", slug="about3", is_published=False)
    page4 = Page.objects.create(title="Page1", slug="slug_page_1", is_published=True)
    page5 = Page.objects.create(title="Page2", slug="slug_page_2", is_published=True)

    page1_cursor = to_global_cursor([getattr(page1, field) for field in cursor_fields])
    page3_cursor = to_global_cursor([getattr(page3, field) for field in cursor_fields])
    page4_cursor = to_global_cursor([getattr(page4, field) for field in cursor_fields])
    page5_cursor = to_global_cursor([getattr(page5, field) for field in cursor_fields])
    variables = {"after": None, "sortBy": order_by}

    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    page_info = content["data"]["pages"]["pageInfo"]

    assert not page_info["hasPreviousPage"]
    assert page_info["hasNextPage"]
    assert page_info["startCursor"] == page1_cursor
    assert page_info["endCursor"] == page3_cursor

    variables = {"after": page3_cursor, "sortBy": order_by}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    page_info = content["data"]["pages"]["pageInfo"]

    assert page_info["hasPreviousPage"]
    assert not page_info["hasNextPage"]
    assert page_info["startCursor"] == page4_cursor
    assert page_info["endCursor"] == page5_cursor
