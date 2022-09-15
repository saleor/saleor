import pytest

from ....product.models import Category
from ...tests.utils import get_graphql_content


@pytest.fixture
def categories_for_filtering():
    return Category.objects.bulk_create(
        [
            Category(
                name="Category1", slug="category1", lft=0, rght=0, tree_id=0, level=0
            ),
            Category(
                name="Category2", slug="category2", lft=1, rght=2, tree_id=1, level=0
            ),
            Category(
                name="Category3", slug="category3", lft=1, rght=2, tree_id=2, level=0
            ),
        ]
    )


QUERY_CATEGORIES_WITH_FILTERING = """
    query (
        $filter: CategoryFilterInput
    ){
        categories (
            first: 10, filter: $filter
        ) {
            edges {
                node {
                    name
                    slug
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "filter_by, categories_count",
    [
        ({"slugs": ["category1"]}, 1),
        ({"slugs": ["category2", "category3"]}, 2),
        ({"slugs": []}, 3),
    ],
)
def test_categories_with_filtering(
    filter_by,
    categories_count,
    staff_api_client,
    categories_for_filtering,
):
    # given
    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CATEGORIES_WITH_FILTERING,
        variables,
    )

    # then
    content = get_graphql_content(response)
    categories_nodes = content["data"]["categories"]["edges"]
    assert len(categories_nodes) == categories_count
