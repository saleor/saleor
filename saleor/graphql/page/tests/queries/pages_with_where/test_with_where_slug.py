import pytest

from .....tests.utils import get_graphql_content
from .shared import QUERY_PAGES_WITH_WHERE


@pytest.mark.parametrize(
    ("where", "pages_count"),
    [
        ({"slug": {"eq": "test-url-1"}}, 1),
        ({"slug": {"oneOf": ["test-url-1", "test-url-2"]}}, 2),
    ],
)
def test_pages_with_where_slug(where, pages_count, staff_api_client, page_list):
    # given
    variables = {"where": where}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == pages_count
