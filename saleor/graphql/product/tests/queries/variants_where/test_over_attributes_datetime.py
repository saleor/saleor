import datetime

import pytest

from ......attribute import AttributeInputType, AttributeType
from ......attribute.models import Attribute
from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import PRODUCT_VARIANTS_WHERE_QUERY


@pytest.mark.parametrize(
    ("date_time_input", "expected_count"),
    [
        ({"slug": "dt", "value": {"name": {"eq": "datetime-name-1"}}}, 1),
        ({"slug": "dt", "value": {"slug": {"eq": "datetime-slug-1"}}}, 1),
        (
            {
                "slug": "dt",
                "value": {"name": {"oneOf": ["datetime-name-1", "datetime-name-2"]}},
            },
            2,
        ),
        (
            {
                "slug": "dt",
                "value": {"slug": {"oneOf": ["datetime-slug-1", "datetime-slug-2"]}},
            },
            2,
        ),
        ({"slug": "dt", "value": {"dateTime": {"gte": "2021-01-01T00:00:00Z"}}}, 2),
        (
            {
                "slug": "dt",
                "value": {
                    "dateTime": {
                        "gte": "2021-01-01T00:00:00Z",
                        "lte": "2021-01-02T00:00:00Z",
                    }
                },
            },
            1,
        ),
        ({"value": {"name": {"eq": "datetime-name-1"}}}, 1),
        ({"value": {"slug": {"eq": "datetime-slug-1"}}}, 1),
        ({"value": {"name": {"oneOf": ["datetime-name-1", "datetime-name-2"]}}}, 2),
        ({"value": {"slug": {"oneOf": ["datetime-slug-1", "datetime-slug-2"]}}}, 2),
        ({"value": {"dateTime": {"gte": "2021-01-01T00:00:00Z"}}}, 3),
        (
            {
                "value": {
                    "dateTime": {
                        "gte": "2021-01-01T00:00:00Z",
                        "lte": "2021-01-02T00:00:00Z",
                    }
                }
            },
            2,
        ),
    ],
)
def test_product_variants_query_with_attribute_value_date_time(
    date_time_input,
    expected_count,
    staff_api_client,
    product_variant_list,
    date_time_attribute,
    channel_USD,
):
    # given
    product = product_variant_list[0].product
    product_type = product.product_type

    date_time_attribute.slug = "dt"
    date_time_attribute.type = "PRODUCT_TYPE"
    date_time_attribute.save()

    second_date_attribute = Attribute.objects.create(
        slug="second_dt",
        name="Second dt",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.DATE_TIME,
    )

    product_type.variant_attributes.set([date_time_attribute, second_date_attribute])

    attr_value_1 = date_time_attribute.values.first()
    attr_value_1.date_time = datetime.datetime(2021, 1, 3, tzinfo=datetime.UTC)
    attr_value_1.name = "datetime-name-1"
    attr_value_1.slug = "datetime-slug-1"
    attr_value_1.save()

    associate_attribute_values_to_instance(
        product_variant_list[0], {date_time_attribute.pk: [attr_value_1]}
    )

    second_attr_value = date_time_attribute.values.last()
    second_attr_value.date_time = datetime.datetime(2021, 1, 1, tzinfo=datetime.UTC)
    second_attr_value.name = "datetime-name-2"
    second_attr_value.slug = "datetime-slug-2"
    second_attr_value.save()

    associate_attribute_values_to_instance(
        product_variant_list[1], {date_time_attribute.pk: [second_attr_value]}
    )

    value_for_second_attr = second_date_attribute.values.create(
        date_time=datetime.datetime(2021, 1, 1, tzinfo=datetime.UTC),
        name="second-datetime-name",
        slug="second-datetime-slug",
    )

    associate_attribute_values_to_instance(
        product_variant_list[3], {second_date_attribute.pk: [value_for_second_attr]}
    )

    variables = {
        "where": {"attributes": [date_time_input]},
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    variants_nodes = content["data"]["productVariants"]["edges"]
    assert len(variants_nodes) == expected_count
