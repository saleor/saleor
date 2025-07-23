import datetime

import pytest

from ......attribute import AttributeInputType, AttributeType
from ......attribute.models import Attribute
from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import QUERY_PAGES_WITH_WHERE


@pytest.mark.parametrize(
    ("date_input", "expected_count"),
    [
        ({"slug": "date", "value": {"date": {"gte": "2021-01-01"}}}, 1),
        ({"slug": "date", "value": {"name": {"eq": "date-name-1"}}}, 1),
        ({"slug": "date", "value": {"slug": {"eq": "date-slug-1"}}}, 1),
        (
            {
                "slug": "date",
                "value": {"name": {"oneOf": ["date-name-1", "date-name-2"]}},
            },
            1,
        ),
        (
            {
                "slug": "date",
                "value": {"slug": {"oneOf": ["date-slug-1", "date-slug-2"]}},
            },
            1,
        ),
        (
            {
                "slug": "date",
                "value": {"date": {"gte": "2021-01-02", "lte": "2021-01-03"}},
            },
            1,
        ),
        ({"value": {"date": {"gte": "2021-01-01"}}}, 2),
        ({"value": {"name": {"eq": "date-name-1"}}}, 1),
        ({"value": {"slug": {"eq": "date-slug-1"}}}, 1),
        ({"value": {"name": {"oneOf": ["date-name-1", "date-name-2"]}}}, 2),
        ({"value": {"slug": {"oneOf": ["date-slug-1", "date-slug-2"]}}}, 2),
        ({"value": {"date": {"gte": "2021-01-01", "lte": "2021-01-02"}}}, 1),
    ],
)
def test_pages_query_with_attribute_value_date(
    date_input,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    date_attribute,
):
    # given
    date_attribute.type = "PAGE_TYPE"
    date_attribute.slug = "date"
    date_attribute.save()

    second_date_attribute = Attribute.objects.create(
        slug="second_date",
        name="Second date",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.DATE,
    )
    page_type.page_attributes.add(date_attribute)
    page_type.page_attributes.add(second_date_attribute)

    attr_value_1 = date_attribute.values.first()
    attr_value_1.date_time = datetime.datetime(2021, 1, 3, tzinfo=datetime.UTC)
    attr_value_1.name = "date-name-1"
    attr_value_1.slug = "date-slug-1"
    attr_value_1.save()

    associate_attribute_values_to_instance(
        page_list[0], {date_attribute.pk: [attr_value_1]}
    )

    second_attr_value = second_date_attribute.values.create(
        date_time=datetime.datetime(2021, 1, 2, tzinfo=datetime.UTC),
        name="date-name-2",
        slug="date-slug-2",
    )

    associate_attribute_values_to_instance(
        page_list[1], {second_date_attribute.pk: [second_attr_value]}
    )

    variables = {"where": {"attributes": [date_input]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count
