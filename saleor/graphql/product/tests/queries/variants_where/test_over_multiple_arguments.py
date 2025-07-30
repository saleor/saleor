import pytest

from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import PRODUCT_VARIANTS_WHERE_QUERY


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
            {"slug": "weight_attribute", "value": {"slug": {"eq": "cotton"}}},
            {"slug": "non-existing-attr", "value": {"slug": {"eq": "some-value"}}},
        ],
        [
            {"value": {"slug": {"eq": "large"}}},
            {"slug": "non-existing-attr", "value": {"slug": {"eq": "some-value"}}},
        ],
    ],
)
def test_product_variants_query_with_non_matching_records(
    attribute_filter,
    staff_api_client,
    product_variant_list,
    weight_attribute,
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

    weight_attribute.slug = "weight_attribute"
    weight_attribute.save()

    product_type = product_variant_list[0].product.product_type
    product_type.variant_attributes.set(
        [
            weight_attribute,
            tag_attribute,
            boolean_attribute,
            numeric_attribute_without_unit,
            date_attribute,
            date_time_attribute,
        ]
    )

    weight_value = weight_attribute.values.get(slug="cotton")
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
        product_variant_list[0],
        {
            weight_attribute.pk: [weight_value],
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
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    product_variants_nodes = content["data"]["productVariants"]["edges"]
    assert len(product_variants_nodes) == 0


@pytest.mark.parametrize(
    ("attribute_where_input", "expected_count_result"),
    [
        (
            [
                {"slug": "material", "value": {"slug": {"eq": "cotton"}}},
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
                {"slug": "color", "value": {"slug": {"oneOf": ["red"]}}},
                {"slug": "boolean", "value": {"boolean": True}},
            ],
            1,
        ),
        (
            [
                {"slug": "material", "value": {"slug": {"eq": "cotton"}}},
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
            ],
            1,
        ),
        (
            [
                {"slug": "material", "value": {"slug": {"eq": "cotton"}}},
                {"slug": "boolean", "value": {"boolean": False}},
            ],
            0,
        ),
        (
            [
                {"slug": "tag", "value": {"name": {"eq": "About"}}},
                {"slug": "material", "value": {"slug": {"eq": "cotton"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "material", "value": {"slug": {"eq": "poliester"}}},
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
                {"slug": "material", "value": {"slug": {"eq": "cotton"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "material", "value": {"slug": {"eq": "cotton"}}},
                {"slug": "color", "value": {"name": {"eq": "Red"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "material", "value": {"slug": {"eq": "cotton"}}},
                {"slug": "tag", "value": {"name": {"eq": "About"}}},
                {"slug": "color", "value": {"slug": {"eq": "red"}}},
            ],
            1,
        ),
        (
            [
                {
                    "slug": "material",
                    "value": {"slug": {"oneOf": ["cotton", "poliester"]}},
                },
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
            ],
            2,
        ),
        (
            [
                {
                    "slug": "material",
                    "value": {"slug": {"oneOf": ["cotton", "poliester"]}},
                },
                {"slug": "boolean", "value": {"boolean": True}},
            ],
            1,
        ),
        ([{"value": {"slug": {"oneOf": ["red", "blue"]}}}], 2),
        (
            [
                {"value": {"slug": {"oneOf": ["cotton", "poliester"]}}},
                {"value": {"boolean": True}},
            ],
            1,
        ),
    ],
)
def test_product_variants_query_with_multiple_attribute_filters(
    attribute_where_input,
    expected_count_result,
    staff_api_client,
    product_variant_list,
    weight_attribute,
    tag_page_attribute,
    color_attribute,
    boolean_attribute,
    channel_USD,
):
    # given
    material_attribute = weight_attribute
    material_attribute.slug = "material"
    material_attribute.save()

    tag_attribute = tag_page_attribute
    tag_attribute.slug = "tag"
    tag_attribute.type = "PRODUCT_TYPE"
    tag_attribute.save()

    product_type = product_variant_list[0].product.product_type
    product_type.variant_attributes.set(
        [material_attribute, tag_attribute, color_attribute, boolean_attribute]
    )

    material_value = material_attribute.values.get(slug="cotton")
    tag_value = tag_attribute.values.get(name="About")
    color_value = color_attribute.values.get(slug="red")
    second_color_value = color_attribute.values.get(slug="blue")

    boolean_value = boolean_attribute.values.filter(boolean=True).first()

    associate_attribute_values_to_instance(
        product_variant_list[0],
        {
            material_attribute.pk: [material_value],
            tag_attribute.pk: [tag_value],
            color_attribute.pk: [color_value],
            boolean_attribute.pk: [boolean_value],
        },
    )

    tag_value_2 = tag_attribute.values.get(name="Help")
    second_material_value = material_attribute.values.get(slug="poliester")

    associate_attribute_values_to_instance(
        product_variant_list[1],
        {
            material_attribute.pk: [second_material_value],
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
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    product_variants_nodes = content["data"]["productVariants"]["edges"]
    assert len(product_variants_nodes) == expected_count_result
