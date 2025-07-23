import pytest

from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import QUERY_PAGES_WITH_WHERE


@pytest.mark.parametrize(
    ("numeric_input", "expected_count"),
    [
        ({"slug": "num-slug", "value": {"numeric": {"eq": 1.2}}}, 1),
        ({"slug": "num-slug", "value": {"numeric": {"oneOf": [1.2, 2]}}}, 2),
        (
            {"slug": "num-slug", "value": {"numeric": {"range": {"gte": 1, "lte": 2}}}},
            2,
        ),
        ({"slug": "num-slug", "value": {"name": {"eq": "1.2"}}}, 1),
        ({"slug": "num-slug", "value": {"slug": {"eq": "1.2"}}}, 1),
        ({"slug": "num-slug", "value": {"name": {"oneOf": ["1.2", "2"]}}}, 2),
        ({"slug": "num-slug", "value": {"slug": {"oneOf": ["1.2", "2"]}}}, 2),
        ({"value": {"numeric": {"eq": 1.2}}}, 1),
        ({"value": {"numeric": {"oneOf": [1.2, 2]}}}, 2),
        ({"value": {"numeric": {"range": {"gte": 1, "lte": 2}}}}, 2),
        ({"value": {"numeric": {"range": {"gte": 1}}}}, 3),
        ({"value": {"name": {"eq": "1.2"}}}, 1),
        ({"value": {"slug": {"eq": "1.2"}}}, 1),
        ({"value": {"name": {"oneOf": ["1.2", "2"]}}}, 2),
        ({"value": {"slug": {"oneOf": ["1.2", "2"]}}}, 2),
    ],
)
def test_pages_query_with_attribute_value_numeric(
    numeric_input,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    numeric_attribute_without_unit,
    numeric_attribute,
):
    # given
    numeric_attribute_without_unit.slug = "num-slug"
    numeric_attribute_without_unit.type = "PAGE_TYPE"
    numeric_attribute_without_unit.save()

    page_type.page_attributes.add(numeric_attribute_without_unit)
    page_type.page_attributes.add(numeric_attribute)

    attr_value_1 = numeric_attribute_without_unit.values.first()
    attr_value_1.name = "1.2"
    attr_value_1.slug = "1.2"
    attr_value_1.numeric = 1.2
    attr_value_1.save()

    attr_value_2 = numeric_attribute_without_unit.values.last()
    attr_value_2.name = "2"
    attr_value_2.slug = "2"
    attr_value_2.numeric = 2
    attr_value_2.save()

    second_attr_value = numeric_attribute.values.first()

    associate_attribute_values_to_instance(
        page_list[0],
        {
            numeric_attribute_without_unit.pk: [attr_value_1],
        },
    )

    associate_attribute_values_to_instance(
        page_list[1], {numeric_attribute_without_unit.pk: [attr_value_2]}
    )
    associate_attribute_values_to_instance(
        page_list[2], {numeric_attribute.pk: [second_attr_value]}
    )

    variables = {"where": {"attributes": [numeric_input]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count
