import graphene
import pytest

from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import PRODUCTS_FILTER_QUERY, PRODUCTS_WHERE_QUERY


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
def test_products_query_with_attribute_slug(
    query, staff_api_client, product_list, size_attribute, channel_USD
):
    # given
    product_list[0].product_type.product_attributes.add(size_attribute)
    product_attr_value = size_attribute.values.first()

    associate_attribute_values_to_instance(
        product_list[0], {size_attribute.pk: [product_attr_value]}
    )

    variables = {
        "where": {"attributes": [{"slug": size_attribute.slug}]},
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    assert len(products_nodes) == 1
    assert products_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_list[0].pk
    )


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("attribute_input", "expected_count"),
    [
        ({"value": {"slug": {"eq": "test-slug-1"}}}, 1),
        ({"value": {"slug": {"oneOf": ["test-slug-1", "test-slug-2"]}}}, 2),
        ({"slug": "size_attribute", "value": {"slug": {"eq": "test-slug-1"}}}, 1),
        (
            {
                "slug": "size_attribute",
                "value": {"slug": {"oneOf": ["test-slug-1", "test-slug-2"]}},
            },
            2,
        ),
    ],
)
def test_products_query_with_attribute_value_slug(
    query,
    attribute_input,
    expected_count,
    staff_api_client,
    product_list,
    size_attribute,
    channel_USD,
):
    # given
    size_attribute.slug = "size_attribute"
    size_attribute.save()

    product_list[0].product_type.product_attributes.add(size_attribute)

    attr_value_1 = size_attribute.values.first()
    attr_value_1.slug = "test-slug-1"
    attr_value_1.save()

    attr_value_2 = size_attribute.values.last()
    attr_value_2.slug = "test-slug-2"
    attr_value_2.save()

    associate_attribute_values_to_instance(
        product_list[0], {size_attribute.pk: [attr_value_1]}
    )

    associate_attribute_values_to_instance(
        product_list[1], {size_attribute.pk: [attr_value_2]}
    )

    variables = {
        "where": {"attributes": [attribute_input]},
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    assert len(products_nodes) == expected_count


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("attribute_input", "expected_count"),
    [
        ({"value": {"name": {"eq": "test-name-1"}}}, 1),
        ({"value": {"name": {"oneOf": ["test-name-1", "test-name-2"]}}}, 2),
        ({"slug": "size_attribute", "value": {"name": {"eq": "test-name-1"}}}, 1),
        (
            {
                "slug": "size_attribute",
                "value": {"name": {"oneOf": ["test-name-1", "test-name-2"]}},
            },
            2,
        ),
    ],
)
def test_products_query_with_attribute_value_name(
    query,
    attribute_input,
    expected_count,
    staff_api_client,
    product_list,
    size_attribute,
    channel_USD,
):
    # given
    size_attribute.slug = "size_attribute"
    size_attribute.save()

    product_list[0].product_type.product_attributes.add(size_attribute)

    attr_value_1 = size_attribute.values.first()
    attr_value_1.name = "test-name-1"
    attr_value_1.save()

    attr_value_2 = size_attribute.values.last()
    attr_value_2.name = "test-name-2"
    attr_value_2.save()

    associate_attribute_values_to_instance(
        product_list[0], {size_attribute.pk: [attr_value_1]}
    )

    associate_attribute_values_to_instance(
        product_list[1], {size_attribute.pk: [attr_value_2]}
    )

    variables = {
        "where": {"attributes": [attribute_input]},
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    assert len(products_nodes) == expected_count
