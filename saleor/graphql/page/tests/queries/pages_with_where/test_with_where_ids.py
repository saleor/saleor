import graphene

from .....tests.utils import get_graphql_content
from .shared import QUERY_PAGES_WITH_WHERE


def test_pages_query_with_where_by_ids(
    staff_api_client, permission_manage_pages, page_list, page_list_unpublished
):
    # given
    query = QUERY_PAGES_WITH_WHERE

    page_ids = [
        graphene.Node.to_global_id("Page", page.pk)
        for page in [page_list[0], page_list_unpublished[-1]]
    ]
    variables = {"where": {"ids": page_ids}}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # then
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == len(page_ids)
