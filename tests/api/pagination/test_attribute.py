import graphene
import pytest
from prices import Money

from saleor.product.models import (
    Attribute,
    AttributeProduct,
    AttributeVariant,
    Product,
    ProductType,
)

from ..utils import get_graphql_content


@pytest.fixture
def attributes_for_pagination(collection, category):
    attributes = Attribute.objects.bulk_create(
        [
            Attribute(
                name="Attr1",
                slug="attr1",
                value_required=True,
                storefront_search_position=4,
            ),
            Attribute(
                name="AttrAttr1",
                slug="attr_attr1",
                value_required=True,
                storefront_search_position=3,
            ),
            Attribute(
                name="AttrAttr2",
                slug="attr_attr2",
                value_required=True,
                storefront_search_position=2,
            ),
            Attribute(
                name="Attr2",
                slug="attr2",
                value_required=False,
                storefront_search_position=5,
            ),
            Attribute(
                name="Attr3",
                slug="attr3",
                value_required=False,
                storefront_search_position=1,
            ),
        ]
    )

    product_type = ProductType.objects.create(name="My Product Type")
    product = Product.objects.create(
        name="Test product",
        product_type=product_type,
        price=Money("10.00", "USD"),
        category=category,
    )
    collection.products.add(product)
    AttributeVariant.objects.bulk_create(
        [
            AttributeVariant(
                product_type=product_type, attribute=attributes[1], sort_order=1
            ),
            AttributeVariant(
                product_type=product_type, attribute=attributes[3], sort_order=2
            ),
            AttributeVariant(
                product_type=product_type, attribute=attributes[4], sort_order=3
            ),
        ]
    )
    AttributeProduct.objects.bulk_create(
        [
            AttributeProduct(
                product_type=product_type, attribute=attributes[2], sort_order=1
            ),
            AttributeProduct(
                product_type=product_type, attribute=attributes[0], sort_order=2
            ),
            AttributeProduct(
                product_type=product_type, attribute=attributes[1], sort_order=3
            ),
        ]
    )

    return attributes


QUERY_ATTRIBUTES_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: AttributeSortingInput, $filter: AttributeFilterInput
    ){
        attributes (
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
    "sort_by, attributes_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["Attr1", "Attr2", "Attr3"]),
        ({"field": "NAME", "direction": "DESC"}, ["AttrAttr2", "AttrAttr1", "Attr3"]),
        ({"field": "SLUG", "direction": "ASC"}, ["Attr1", "Attr2", "Attr3"]),
        ({"field": "VALUE_REQUIRED", "direction": "ASC"}, ["Attr2", "Attr3", "Attr1"],),
        (
            {"field": "STOREFRONT_SEARCH_POSITION", "direction": "ASC"},
            ["Attr3", "AttrAttr2", "AttrAttr1"],
        ),
    ],
)
def test_attributes_pagination_with_sorting(
    sort_by, attributes_order, staff_api_client, attributes_for_pagination,
):
    page_size = 3

    variables = {"first": page_size, "after": None, "sortBy": sort_by}
    response = staff_api_client.post_graphql(QUERY_ATTRIBUTES_PAGINATION, variables,)
    content = get_graphql_content(response)
    attributes_nodes = content["data"]["attributes"]["edges"]
    assert attributes_order[0] == attributes_nodes[0]["node"]["name"]
    assert attributes_order[1] == attributes_nodes[1]["node"]["name"]
    assert attributes_order[2] == attributes_nodes[2]["node"]["name"]
    assert len(attributes_nodes) == page_size


@pytest.mark.parametrize(
    "filter_by, attributes_order",
    [
        ({"search": "AttrAttr"}, ["AttrAttr2", "AttrAttr1"]),
        ({"search": "attr_attr"}, ["AttrAttr2", "AttrAttr1"]),
        ({"search": "Attr1"}, ["AttrAttr1", "Attr1"]),
        ({"valueRequired": False}, ["Attr3", "Attr2"]),
    ],
)
def test_attributes_pagination_with_filtering(
    filter_by, attributes_order, staff_api_client, attributes_for_pagination,
):
    page_size = 2

    variables = {"first": page_size, "after": None, "filter": filter_by}
    response = staff_api_client.post_graphql(QUERY_ATTRIBUTES_PAGINATION, variables)
    content = get_graphql_content(response)
    attributes_nodes = content["data"]["attributes"]["edges"]
    assert attributes_order[0] == attributes_nodes[0]["node"]["name"]
    assert attributes_order[1] == attributes_nodes[1]["node"]["name"]
    assert len(attributes_nodes) == page_size


def test_attributes_pagination_with_filtering_in_collection(
    staff_api_client, attributes_for_pagination, collection
):
    page_size = 2
    attributes_order = ["Attr3", "AttrAttr2"]
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    filter_by = {"inCollection": collection_id}

    variables = {"first": page_size, "after": None, "filter": filter_by}
    response = staff_api_client.post_graphql(QUERY_ATTRIBUTES_PAGINATION, variables)
    content = get_graphql_content(response)
    attributes_nodes = content["data"]["attributes"]["edges"]
    assert attributes_order[0] == attributes_nodes[0]["node"]["name"]
    assert attributes_order[1] == attributes_nodes[1]["node"]["name"]
    assert len(attributes_nodes) == page_size


def test_attributes_pagination_with_filtering_in_category(
    staff_api_client, attributes_for_pagination, category
):
    page_size = 2
    attributes_order = ["Attr3", "AttrAttr2"]
    category_id = graphene.Node.to_global_id("Category", category.id)
    filter_by = {"inCategory": category_id}

    variables = {"first": page_size, "after": None, "filter": filter_by}
    response = staff_api_client.post_graphql(QUERY_ATTRIBUTES_PAGINATION, variables)
    content = get_graphql_content(response)
    attributes_nodes = content["data"]["attributes"]["edges"]
    assert attributes_order[0] == attributes_nodes[0]["node"]["name"]
    assert attributes_order[1] == attributes_nodes[1]["node"]["name"]
    assert len(attributes_nodes) == page_size
