import pytest

from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import PRODUCTS_FILTER_QUERY, PRODUCTS_WHERE_QUERY


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    "attribute_filter",
    [
        # Non-existing attribute slug
        [{"slug": "non-existing-attribute"}],
        # Existing attribute with non-existing value name
        [{"slug": "tag", "value": {"name": {"eq": "Non-existing Name"}}}],
        [{"value": {"name": {"eq": "Non-existing Name"}}}],
        # Existing numeric attribute with out-of-range value
        [{"slug": "count", "value": {"numeric": {"eq": 999}}}],
        [{"value": {"numeric": {"eq": 999}}}],
        # Existing boolean attribute with no matching boolean value
        [{"slug": "boolean", "value": {"boolean": False}}],
        [{"value": {"boolean": False}}],
        # Multiple attributes where one doesn't exist
        [
            {"slug": "size", "value": {"slug": {"eq": "large"}}},
            {"slug": "non-existing-attr", "value": {"slug": {"eq": "some-value"}}},
        ],
        [
            {"value": {"slug": {"eq": "large"}}},
            {"slug": "non-existing-attr", "value": {"slug": {"eq": "some-value"}}},
        ],
    ],
)
def test_products_query_with_non_matching_records(
    query,
    attribute_filter,
    staff_api_client,
    product_list,
    size_attribute,
    tag_page_attribute,
    boolean_attribute,
    numeric_attribute_without_unit,
    date_attribute,
    date_time_attribute,
    channel_USD,
):
    # given
    tag_attribute = tag_page_attribute
    tag_attribute.type = "PRODUCT_TYPE"
    tag_attribute.save()

    product_type = product_list[0].product_type
    product_type.product_attributes.set(
        [
            size_attribute,
            tag_attribute,
            boolean_attribute,
            numeric_attribute_without_unit,
            date_attribute,
            date_time_attribute,
        ]
    )

    size_value = size_attribute.values.get(slug="small")
    tag_value = tag_attribute.values.get(name="About")
    boolean_value = boolean_attribute.values.filter(boolean=True).first()
    numeric_value = numeric_attribute_without_unit.values.first()
    date_time_value = date_time_attribute.values.first()
    date_value = date_attribute.values.first()

    date_attribute.slug = "date"
    date_attribute.save()
    date_time_attribute.slug = "date_time"
    date_time_attribute.save()

    associate_attribute_values_to_instance(
        product_list[0],
        {
            size_attribute.pk: [size_value],
            tag_attribute.pk: [tag_value],
            boolean_attribute.pk: [boolean_value],
            numeric_attribute_without_unit.pk: [numeric_value],
            date_attribute.pk: [date_value],
            date_time_attribute.pk: [date_time_value],
        },
    )

    variables = {
        "where": {"attributes": attribute_filter},
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
    assert len(products_nodes) == 0


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("attribute_where_input", "expected_count_result"),
    [
        (
            [
                {"slug": "size", "value": {"slug": {"eq": "big"}}},
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
                {"slug": "color", "value": {"slug": {"oneOf": ["red"]}}},
                {"slug": "boolean", "value": {"boolean": True}},
            ],
            1,
        ),
        (
            [
                {"slug": "size", "value": {"slug": {"eq": "big"}}},
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
            ],
            1,
        ),
        (
            [
                {"slug": "size", "value": {"slug": {"eq": "big"}}},
                {"slug": "boolean", "value": {"boolean": False}},
            ],
            0,
        ),
        (
            [
                {"slug": "tag", "value": {"name": {"eq": "About"}}},
                {"slug": "size", "value": {"slug": {"eq": "big"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "size", "value": {"slug": {"eq": "small"}}},
                {"slug": "tag", "value": {"name": {"eq": "Help"}}},
                {"slug": "boolean", "value": {"boolean": False}},
            ],
            0,
        ),
        (
            [
                {
                    "slug": "color",
                    "value": {"slug": {"oneOf": ["red", "blue"]}},
                },
                {"slug": "size", "value": {"slug": {"eq": "big"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "size", "value": {"slug": {"eq": "big"}}},
                {"slug": "color", "value": {"name": {"eq": "Red"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "size", "value": {"slug": {"eq": "big"}}},
                {"slug": "tag", "value": {"name": {"eq": "About"}}},
                {"slug": "color", "value": {"slug": {"eq": "red"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "size", "value": {"slug": {"oneOf": ["big", "small"]}}},
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
            ],
            2,
        ),
        (
            [
                {"slug": "size", "value": {"slug": {"oneOf": ["big", "small"]}}},
                {"slug": "boolean", "value": {"boolean": True}},
            ],
            1,
        ),
        ([{"value": {"slug": {"oneOf": ["red", "blue"]}}}], 3),
        (
            [
                {"value": {"slug": {"oneOf": ["big", "small"]}}},
                {"value": {"boolean": True}},
            ],
            1,
        ),
    ],
)
def test_products_query_with_multiple_attribute_filters(
    query,
    attribute_where_input,
    expected_count_result,
    staff_api_client,
    product_list,
    size_attribute,
    tag_page_attribute,
    color_attribute,
    boolean_attribute,
    channel_USD,
):
    # given
    tag_attribute = tag_page_attribute
    tag_attribute.slug = "tag"
    tag_attribute.type = "PRODUCT_TYPE"
    tag_attribute.save()

    product_type = product_list[0].product_type
    product_type.product_attributes.set(
        [size_attribute, tag_attribute, color_attribute, boolean_attribute]
    )

    size_value = size_attribute.values.get(slug="big")
    tag_value = tag_attribute.values.get(name="About")
    color_value = color_attribute.values.get(slug="red")
    second_color_value = color_attribute.values.get(slug="blue")

    boolean_value = boolean_attribute.values.filter(boolean=True).first()

    associate_attribute_values_to_instance(
        product_list[0],
        {
            size_attribute.pk: [size_value],
            tag_attribute.pk: [tag_value],
            color_attribute.pk: [color_value],
            boolean_attribute.pk: [boolean_value],
        },
    )

    tag_value_2 = tag_attribute.values.get(name="Help")
    size_value_small = size_attribute.values.get(slug="small")

    associate_attribute_values_to_instance(
        product_list[1],
        {
            size_attribute.pk: [size_value_small],
            tag_attribute.pk: [tag_value_2],
            color_attribute.pk: [second_color_value],
        },
    )

    variables = {
        "where": {"attributes": attribute_where_input},
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
    assert len(products_nodes) == expected_count_result
