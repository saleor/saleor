import pytest
from prices import Money

from saleor.product.models import Category, Product

from ..utils import get_graphql_content


@pytest.fixture
def categories_for_pagination(product_type):
    categories = Category.tree.build_tree_nodes(
        {
            "name": "Category2",
            "slug": "cat1",
            "children": [
                {"name": "CategoryCategory1", "slug": "cat_cat1"},
                {"name": "CategoryCategory2", "slug": "cat_cat2"},
                {"name": "Category1", "slug": "cat2"},
                {"name": "Category3", "slug": "cat3"},
            ],
        }
    )
    categories = Category.objects.bulk_create(categories)
    Product.objects.bulk_create(
        [
            Product(
                name="Prod1",
                slug="prod1",
                product_type=product_type,
                price=Money("10.00", "USD"),
                category=categories[4],
            ),
            Product(
                name="Prod2",
                slug="prod2",
                product_type=product_type,
                price=Money("10.00", "USD"),
                category=categories[4],
            ),
            Product(
                name="Prod3",
                slug="prod3",
                product_type=product_type,
                price=Money("10.00", "USD"),
                category=categories[2],
            ),
        ]
    )
    return categories


QUERY_CATEGORIES_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: CategorySortingInput, $filter: CategoryFilterInput
    ){
        categories(
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


@pytest.mark.parametrize(
    "sort_by, categories_order",
    [
        (
            {"field": "NAME", "direction": "ASC"},
            ["Category1", "Category2", "Category3"],
        ),
        (
            {"field": "NAME", "direction": "DESC"},
            ["CategoryCategory2", "CategoryCategory1", "Category3"],
        ),
        (
            {"field": "SUBCATEGORY_COUNT", "direction": "ASC"},
            ["Category2", "CategoryCategory1", "CategoryCategory2"],
        ),
        (
            {"field": "PRODUCT_COUNT", "direction": "ASC"},
            ["CategoryCategory1", "Category1", "CategoryCategory2"],
        ),
    ],
)
def test_categories_pagination_with_sorting(
    sort_by, categories_order, staff_api_client, categories_for_pagination,
):
    page_size = 3

    variables = {"first": page_size, "after": None, "sortBy": sort_by}
    response = staff_api_client.post_graphql(QUERY_CATEGORIES_PAGINATION, variables,)
    content = get_graphql_content(response)
    categories_nodes = content["data"]["categories"]["edges"]
    assert categories_order[0] == categories_nodes[0]["node"]["name"]
    assert categories_order[1] == categories_nodes[1]["node"]["name"]
    assert categories_order[2] == categories_nodes[2]["node"]["name"]
    assert len(categories_nodes) == page_size


@pytest.mark.parametrize(
    "filter_by, categories_order",
    [
        ({"search": "CategoryCategory"}, ["CategoryCategory1", "CategoryCategory2"]),
        ({"search": "cat_cat"}, ["CategoryCategory1", "CategoryCategory2"]),
        ({"search": "Category1"}, ["CategoryCategory1", "Category1"]),
    ],
)
def test_categories_pagination_with_filtering(
    filter_by, categories_order, staff_api_client, categories_for_pagination,
):
    page_size = 2

    variables = {"first": page_size, "after": None, "filter": filter_by}
    response = staff_api_client.post_graphql(QUERY_CATEGORIES_PAGINATION, variables,)
    content = get_graphql_content(response)
    categories_nodes = content["data"]["categories"]["edges"]
    assert categories_order[0] == categories_nodes[0]["node"]["name"]
    assert categories_order[1] == categories_nodes[1]["node"]["name"]
    assert len(categories_nodes) == page_size
