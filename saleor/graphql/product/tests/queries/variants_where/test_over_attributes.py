import graphene
import pytest

from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import PRODUCT_VARIANTS_WHERE_QUERY


def test_product_variants_query_with_attribute_slug(
    staff_api_client, product_variant_list, weight_attribute, channel_USD
):
    # given
    product_type = product_variant_list[0].product.product_type
    product_type.variant_attributes.add(weight_attribute)
    attr_value = weight_attribute.values.first()

    associate_attribute_values_to_instance(
        product_variant_list[0], {weight_attribute.pk: [attr_value]}
    )

    variables = {
        "where": {"attributes": [{"slug": weight_attribute.slug}]},
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
    assert len(product_variants_nodes) == 1
    assert product_variants_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "ProductVariant", product_variant_list[0].pk
    )


@pytest.mark.parametrize(
    ("attribute_input", "expected_count"),
    [
        ({"value": {"slug": {"eq": "test-slug-1"}}}, 1),
        ({"value": {"slug": {"oneOf": ["test-slug-1", "test-slug-2"]}}}, 2),
        ({"slug": "weight_attribute", "value": {"slug": {"eq": "test-slug-1"}}}, 1),
        (
            {
                "slug": "weight_attribute",
                "value": {"slug": {"oneOf": ["test-slug-1", "test-slug-2"]}},
            },
            2,
        ),
    ],
)
def test_product_variants_query_with_attribute_value_slug(
    attribute_input,
    expected_count,
    staff_api_client,
    product_variant_list,
    weight_attribute,
    channel_USD,
):
    # given
    weight_attribute.slug = "weight_attribute"
    weight_attribute.save()

    product_variant_list[0].product.product_type.variant_attributes.add(
        weight_attribute
    )

    attr_value_1 = weight_attribute.values.first()
    attr_value_1.slug = "test-slug-1"
    attr_value_1.save()

    attr_value_2 = weight_attribute.values.last()
    attr_value_2.slug = "test-slug-2"
    attr_value_2.save()

    associate_attribute_values_to_instance(
        product_variant_list[0], {weight_attribute.pk: [attr_value_1]}
    )

    associate_attribute_values_to_instance(
        product_variant_list[1], {weight_attribute.pk: [attr_value_2]}
    )

    variables = {
        "where": {"attributes": [attribute_input]},
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
    assert len(product_variants_nodes) == expected_count


@pytest.mark.parametrize(
    ("attribute_input", "expected_count"),
    [
        ({"value": {"name": {"eq": "test-name-1"}}}, 1),
        ({"value": {"name": {"oneOf": ["test-name-1", "test-name-2"]}}}, 2),
        ({"slug": "weight_attribute", "value": {"name": {"eq": "test-name-1"}}}, 1),
        (
            {
                "slug": "weight_attribute",
                "value": {"name": {"oneOf": ["test-name-1", "test-name-2"]}},
            },
            2,
        ),
    ],
)
def test_product_variants_query_with_attribute_value_name(
    attribute_input,
    expected_count,
    staff_api_client,
    product_variant_list,
    weight_attribute,
    channel_USD,
):
    # given
    weight_attribute.slug = "weight_attribute"
    weight_attribute.save()

    product_variant_list[0].product.product_type.variant_attributes.add(
        weight_attribute
    )

    attr_value_1 = weight_attribute.values.first()
    attr_value_1.name = "test-name-1"
    attr_value_1.save()

    attr_value_2 = weight_attribute.values.last()
    attr_value_2.name = "test-name-2"
    attr_value_2.save()

    associate_attribute_values_to_instance(
        product_variant_list[0], {weight_attribute.pk: [attr_value_1]}
    )

    associate_attribute_values_to_instance(
        product_variant_list[1], {weight_attribute.pk: [attr_value_2]}
    )

    variables = {
        "where": {"attributes": [attribute_input]},
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
    assert len(product_variants_nodes) == expected_count
