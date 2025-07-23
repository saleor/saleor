import graphene
import pytest

from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import QUERY_PAGES_WITH_WHERE


def test_pages_query_with_attribute_slug(
    staff_api_client, page_list, page_type, size_page_attribute
):
    # given
    page_type.page_attributes.add(size_page_attribute)
    page_attr_value = size_page_attribute.values.first()

    associate_attribute_values_to_instance(
        page_list[0], {size_page_attribute.pk: [page_attr_value]}
    )

    variables = {"where": {"attributes": [{"slug": size_page_attribute.slug}]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == 1
    assert pages_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Page", page_list[0].pk
    )


@pytest.mark.parametrize(
    ("attribute_input", "expected_count"),
    [
        ({"value": {"slug": {"eq": "test-slug-1"}}}, 1),
        ({"value": {"slug": {"oneOf": ["test-slug-1", "test-slug-2"]}}}, 2),
        ({"slug": "size_page_attribute", "value": {"slug": {"eq": "test-slug-1"}}}, 1),
        (
            {
                "slug": "size_page_attribute",
                "value": {"slug": {"oneOf": ["test-slug-1", "test-slug-2"]}},
            },
            2,
        ),
    ],
)
def test_pages_query_with_attribute_value_slug(
    attribute_input,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    size_page_attribute,
):
    # given
    size_page_attribute.slug = "size_page_attribute"
    size_page_attribute.save()

    page_type.page_attributes.add(size_page_attribute)

    attr_value_1 = size_page_attribute.values.first()
    attr_value_1.slug = "test-slug-1"
    attr_value_1.save()

    attr_value_2 = size_page_attribute.values.last()
    attr_value_2.slug = "test-slug-2"
    attr_value_2.save()

    associate_attribute_values_to_instance(
        page_list[0], {size_page_attribute.pk: [attr_value_1]}
    )

    associate_attribute_values_to_instance(
        page_list[1], {size_page_attribute.pk: [attr_value_2]}
    )

    variables = {"where": {"attributes": [attribute_input]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    ("attribute_input", "expected_count"),
    [
        ({"value": {"name": {"eq": "test-name-1"}}}, 1),
        ({"value": {"name": {"oneOf": ["test-name-1", "test-name-2"]}}}, 2),
        ({"slug": "size_page_attribute", "value": {"name": {"eq": "test-name-1"}}}, 1),
        (
            {
                "slug": "size_page_attribute",
                "value": {"name": {"oneOf": ["test-name-1", "test-name-2"]}},
            },
            2,
        ),
    ],
)
def test_pages_query_with_attribute_value_name(
    attribute_input,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    size_page_attribute,
):
    # given
    size_page_attribute.slug = "size_page_attribute"
    size_page_attribute.save()

    page_type.page_attributes.add(size_page_attribute)

    attr_value_1 = size_page_attribute.values.first()
    attr_value_1.name = "test-name-1"
    attr_value_1.save()

    attr_value_2 = size_page_attribute.values.last()
    attr_value_2.name = "test-name-2"
    attr_value_2.save()

    associate_attribute_values_to_instance(
        page_list[0], {size_page_attribute.pk: [attr_value_1]}
    )

    associate_attribute_values_to_instance(
        page_list[1], {size_page_attribute.pk: [attr_value_2]}
    )

    variables = {"where": {"attributes": [attribute_input]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count
