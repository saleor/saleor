import pytest

from .....product.models import Category, Product
from .....tests.utils import dummy_editorjs
from ....tests.utils import (
    get_graphql_content,
)

LEVELED_CATEGORIES_QUERY = """
    query leveled_categories($level: Int) {
        categories(level: $level, first: 20) {
            edges {
                node {
                    name
                    parent {
                        name
                    }
                }
            }
        }
    }
    """


def test_category_level(user_api_client, category):
    query = LEVELED_CATEGORIES_QUERY
    child = Category.objects.create(name="child", slug="chi-ld", parent=category)
    variables = {"level": 0}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    category_data = content["data"]["categories"]["edges"][0]["node"]
    assert category_data["name"] == category.name
    assert category_data["parent"] is None

    variables = {"level": 1}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    category_data = content["data"]["categories"]["edges"][0]["node"]
    assert category_data["name"] == child.name
    assert category_data["parent"]["name"] == category.name


NOT_EXISTS_IDS_CATEGORIES_QUERY = """
    query ($filter: CategoryFilterInput!) {
        categories(first: 5, filter: $filter) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
"""


def test_categories_query_ids_not_exists(user_api_client, category):
    query = NOT_EXISTS_IDS_CATEGORIES_QUERY
    variables = {"filter": {"ids": ["W3KATGDn3fq3ZH4=", "zH9pYmz7yWD3Hy8="]}}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response, ignore_errors=True)
    message_error = '{"ids": [{"message": "Invalid ID specified.", "code": ""}]}'
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["categories"] is None


QUERY_CATEGORIES_WITH_SORT = """
    query ($sort_by: CategorySortingInput!) {
        categories(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    ("category_sort", "result_order"),
    [
        (
            {"field": "NAME", "direction": "ASC"},
            ["Cat1", "Cat2", "SubCat", "SubSubCat"],
        ),
        (
            {"field": "NAME", "direction": "DESC"},
            ["SubSubCat", "SubCat", "Cat2", "Cat1"],
        ),
        (
            {"field": "SUBCATEGORY_COUNT", "direction": "ASC"},
            ["Cat2", "SubSubCat", "Cat1", "SubCat"],
        ),
        (
            {"field": "SUBCATEGORY_COUNT", "direction": "DESC"},
            ["SubCat", "Cat1", "SubSubCat", "Cat2"],
        ),
        (
            {"field": "PRODUCT_COUNT", "direction": "ASC"},
            ["Cat2", "SubCat", "SubSubCat", "Cat1"],
        ),
        (
            {"field": "PRODUCT_COUNT", "direction": "DESC"},
            ["Cat1", "SubSubCat", "SubCat", "Cat2"],
        ),
    ],
)
def test_categories_query_with_sort(
    category_sort,
    result_order,
    staff_api_client,
    permission_manage_products,
    product_type,
):
    cat1 = Category.objects.create(
        name="Cat1",
        slug="slug_category1",
        description=dummy_editorjs("Description cat1."),
    )
    Product.objects.create(
        name="Test",
        slug="test",
        product_type=product_type,
        category=cat1,
    )
    Category.objects.create(
        name="Cat2",
        slug="slug_category2",
        description=dummy_editorjs("Description cat2."),
    )
    Category.objects.create(
        name="SubCat",
        slug="slug_subcategory1",
        parent=Category.objects.get(name="Cat1"),
        description=dummy_editorjs("Subcategory_description of cat1."),
    )
    subsubcat = Category.objects.create(
        name="SubSubCat",
        slug="slug_subcategory2",
        parent=Category.objects.get(name="SubCat"),
        description=dummy_editorjs("Subcategory_description of cat1."),
    )
    Product.objects.create(
        name="Test2",
        slug="test2",
        product_type=product_type,
        category=subsubcat,
    )
    variables = {"sort_by": category_sort}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_CATEGORIES_WITH_SORT, variables)
    content = get_graphql_content(response)
    categories = content["data"]["categories"]["edges"]

    for order, category_name in enumerate(result_order):
        assert categories[order]["node"]["name"] == category_name
