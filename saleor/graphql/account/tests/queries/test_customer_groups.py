from ....tests.utils import get_graphql_content

QUERY_CUSTOMER_GROUPS = """
query ($query: String!, $first: Int!, $after: String) {
    customerGroups(first: $first, filter: { search: $query }, after: $after) {
        edges {
            node {
                id
                name
            }
        }
        pageInfo {
            endCursor
            hasNextPage
            hasPreviousPage
            startCursor
        }
    }
}
"""


def test_query_customer_groups(
    staff_api_client,
    customer_group_list,
):
    page_size = 2
    variables = {"first": page_size, "after": None, "query": ""}
    response = staff_api_client.post_graphql(
        QUERY_CUSTOMER_GROUPS,
        variables,
    )
    content = get_graphql_content(response)
    nodes = content["data"]["customerGroups"]["edges"]
    assert len(nodes) == page_size
