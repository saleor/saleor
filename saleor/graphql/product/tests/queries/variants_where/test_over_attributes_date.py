import datetime

import pytest

from ......attribute import AttributeInputType, AttributeType
from ......attribute.models import Attribute
from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import PRODUCT_VARIANTS_WHERE_QUERY


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
def test_product_variants_query_with_attribute_value_date(
    date_input,
    expected_count,
    staff_api_client,
    product_variant_list,
    date_attribute,
    channel_USD,
):
    # given
    product = product_variant_list[0].product
    product_type = product.product_type

    date_attribute.type = "PRODUCT_TYPE"
    date_attribute.slug = "date"
    date_attribute.save()

    second_date_attribute = Attribute.objects.create(
        slug="second_date",
        name="Second date",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.DATE,
    )
    product_type.variant_attributes.add(date_attribute, second_date_attribute)

    attr_value_1 = date_attribute.values.first()
    attr_value_1.date_time = datetime.datetime(2021, 1, 3, tzinfo=datetime.UTC)
    attr_value_1.name = "date-name-1"
    attr_value_1.slug = "date-slug-1"
    attr_value_1.save()

    variant_1 = product_variant_list[0]
    associate_attribute_values_to_instance(
        variant_1, {date_attribute.pk: [attr_value_1]}
    )

    second_attr_value = second_date_attribute.values.create(
        date_time=datetime.datetime(2021, 1, 2, tzinfo=datetime.UTC),
        name="date-name-2",
        slug="date-slug-2",
    )

    variant_2 = product_variant_list[1]
    associate_attribute_values_to_instance(
        variant_2, {second_date_attribute.pk: [second_attr_value]}
    )

    variables = {"where": {"attributes": [date_input]}, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    variants_nodes = content["data"]["productVariants"]["edges"]
    assert len(variants_nodes) == expected_count
