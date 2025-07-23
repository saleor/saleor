import graphene
import pytest

from ......page.models import Page
from .....tests.utils import get_graphql_content
from .shared import QUERY_PAGES_WITH_WHERE


@pytest.mark.parametrize(
    ("metadata", "expected_indexes"),
    [
        ({"key": "foo"}, [0, 1]),
        ({"key": "foo", "value": {"eq": "bar"}}, [0]),
        ({"key": "foo", "value": {"eq": "baz"}}, []),
        ({"key": "foo", "value": {"oneOf": ["bar", "zaz"]}}, [0, 1]),
        ({"key": "notfound"}, []),
        ({"key": "foo", "value": {"eq": None}}, []),
        ({"key": "foo", "value": {"oneOf": []}}, []),
        (None, []),
    ],
)
def test_pages_with_where_metadata(
    metadata,
    expected_indexes,
    page_list,
    page_type,
    staff_api_client,
):
    # given
    page_list[0].metadata = {"foo": "bar"}
    page_list[1].metadata = {"foo": "zaz"}
    Page.objects.bulk_update(page_list, ["metadata"])
    page_list.append(
        Page.objects.create(
            title="Test page",
            slug="test-url-3",
            is_published=True,
            page_type=page_type,
            metadata={},
        )
    )

    variables = {"where": {"metadata": metadata}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages = content["data"]["pages"]["edges"]
    assert len(pages) == len(expected_indexes)
    ids = {node["node"]["id"] for node in pages}
    assert ids == {
        graphene.Node.to_global_id("Page", page_list[i].pk) for i in expected_indexes
    }
