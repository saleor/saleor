import pytest

from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import QUERY_PAGES_WITH_WHERE


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
            {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
            {"slug": "non-existing-attr", "value": {"slug": {"eq": "some-value"}}},
        ],
        [
            {"value": {"slug": {"eq": "10"}}},
            {"slug": "non-existing-attr", "value": {"slug": {"eq": "some-value"}}},
        ],
    ],
)
def test_pages_query_with_non_matching_records(
    attribute_filter,
    staff_api_client,
    page_list,
    page_type,
    size_page_attribute,
    tag_page_attribute,
    boolean_attribute,
    numeric_attribute_without_unit,
    date_attribute,
    date_time_attribute,
):
    # given
    boolean_attribute.type = "PAGE_TYPE"
    boolean_attribute.save()
    numeric_attribute_without_unit.type = "PAGE_TYPE"
    numeric_attribute_without_unit.save()

    page_type.page_attributes.add(size_page_attribute)
    page_type.page_attributes.add(tag_page_attribute)
    page_type.page_attributes.add(boolean_attribute)
    page_type.page_attributes.add(numeric_attribute_without_unit)
    page_type.page_attributes.add(date_attribute)
    page_type.page_attributes.add(date_time_attribute)

    size_value = size_page_attribute.values.get(slug="10")
    tag_value = tag_page_attribute.values.get(name="About")
    boolean_value = boolean_attribute.values.filter(boolean=True).first()
    numeric_value = numeric_attribute_without_unit.values.first()
    date_time_value = date_time_attribute.values.first()
    date_value = date_attribute.values.first()

    date_attribute.slug = "date"
    date_attribute.save()
    date_time_attribute.slug = "date_time"
    date_time_attribute.save()

    associate_attribute_values_to_instance(
        page_list[0],
        {
            size_page_attribute.pk: [size_value],
            tag_page_attribute.pk: [tag_value],
            boolean_attribute.pk: [boolean_value],
            numeric_attribute_without_unit.pk: [numeric_value],
            date_attribute.pk: [date_value],
            date_time_attribute.pk: [date_time_value],
        },
    )

    variables = {"where": {"attributes": attribute_filter}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == 0


@pytest.mark.parametrize(
    ("attribute_where_input", "expected_count_result"),
    [
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
                {"slug": "author", "value": {"slug": {"oneOf": ["test-author-1"]}}},
                {"slug": "boolean", "value": {"boolean": True}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
                {"slug": "boolean", "value": {"boolean": False}},
            ],
            0,
        ),
        (
            [
                {"slug": "tag", "value": {"name": {"eq": "About"}}},
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "15"}}},
                {"slug": "tag", "value": {"name": {"eq": "Help"}}},
                {"slug": "boolean", "value": {"boolean": False}},
            ],
            0,
        ),
        (
            [
                {
                    "slug": "author",
                    "value": {"slug": {"oneOf": ["test-author-1", "test-author-2"]}},
                },
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
                {"slug": "author", "value": {"name": {"eq": "Test author 1"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
                {"slug": "tag", "value": {"name": {"eq": "About"}}},
                {"slug": "author", "value": {"slug": {"eq": "test-author-1"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"oneOf": ["10", "15"]}}},
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
            ],
            2,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"oneOf": ["10", "15"]}}},
                {"slug": "boolean", "value": {"boolean": True}},
            ],
            1,
        ),
        ([{"value": {"slug": {"oneOf": ["test-author-1", "test-author-2"]}}}], 2),
        (
            [
                {"value": {"slug": {"oneOf": ["10", "15"]}}},
                {"value": {"boolean": True}},
            ],
            1,
        ),
    ],
)
def test_pages_query_with_multiple_attribute_filters(
    attribute_where_input,
    expected_count_result,
    staff_api_client,
    page_list,
    page_type,
    size_page_attribute,
    tag_page_attribute,
    author_page_attribute,
    boolean_attribute,
):
    # given
    boolean_attribute.type = "PAGE_TYPE"
    boolean_attribute.save()

    page_type.page_attributes.add(size_page_attribute)
    page_type.page_attributes.add(tag_page_attribute)
    page_type.page_attributes.add(author_page_attribute)
    page_type.page_attributes.add(boolean_attribute)

    size_value = size_page_attribute.values.get(slug="10")
    tag_value = tag_page_attribute.values.get(name="About")
    author_value = author_page_attribute.values.get(slug="test-author-1")
    second_author_value = author_page_attribute.values.get(slug="test-author-2")

    boolean_value = boolean_attribute.values.filter(boolean=True).first()

    associate_attribute_values_to_instance(
        page_list[0],
        {
            size_page_attribute.pk: [size_value],
            tag_page_attribute.pk: [tag_value],
            author_page_attribute.pk: [author_value],
            boolean_attribute.pk: [boolean_value],
        },
    )

    tag_value_2 = tag_page_attribute.values.get(name="Help")
    size_value_15 = size_page_attribute.values.get(slug="15")

    associate_attribute_values_to_instance(
        page_list[1],
        {
            size_page_attribute.pk: [size_value_15],
            tag_page_attribute.pk: [tag_value_2],
            author_page_attribute.pk: [second_author_value],
        },
    )

    variables = {"where": {"attributes": attribute_where_input}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count_result
