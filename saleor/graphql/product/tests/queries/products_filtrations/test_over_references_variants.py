import graphene
import pytest

from ......attribute import AttributeEntityType, AttributeInputType, AttributeType
from ......attribute.models import Attribute, AttributeValue
from ......attribute.utils import associate_attribute_values_to_instance
from .....core.utils import to_global_id_or_none
from .....tests.utils import get_graphql_content
from .shared import PRODUCTS_FILTER_QUERY, PRODUCTS_WHERE_QUERY


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 2), ("containsAll", 1)]
)
def test_products_query_with_attribute_value_reference_to_product_variants(
    query,
    filter_type,
    expected_count,
    staff_api_client,
    product_list,
    product_type,
    product_type_variant_reference_attribute,
    product_variant_list,
    channel_USD,
):
    # given
    product_type.product_attributes.add(product_type_variant_reference_attribute)
    second_variant_reference_attribute = Attribute.objects.create(
        slug="second-product-reference",
        name="Product reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT_VARIANT,
    )

    first_variant_sku = "test-variant-1"
    second_variant_sku = "test-variant-2"

    first_variant = product_variant_list[0]
    first_variant.sku = first_variant_sku
    first_variant.save()

    second_variant = product_variant_list[1]
    second_variant.sku = second_variant_sku
    second_variant.save()

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_variant_reference_attribute,
                name=f"Variant {first_variant.pk}",
                slug=f"variant-{first_variant.pk}",
                reference_variant=first_variant,
            ),
            AttributeValue(
                attribute=second_variant_reference_attribute,
                name=f"Variant {second_variant.pk}",
                slug=f"variant-{second_variant.pk}",
                reference_variant=second_variant,
            ),
        ]
    )

    product_with_both_references = product_list[0]
    associate_attribute_values_to_instance(
        product_with_both_references,
        {
            product_type_variant_reference_attribute.pk: [attribute_value_1],
            second_variant_reference_attribute.pk: [attribute_value_2],
        },
    )

    product_with_single_reference = product_list[1]
    associate_attribute_values_to_instance(
        product_with_single_reference,
        {second_variant_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "value": {
                        "reference": {
                            "productVariantSkus": {
                                filter_type: [
                                    first_variant_sku,
                                    second_variant_sku,
                                ]
                            }
                        }
                    },
                }
            ]
        },
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
    assert products_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_list[0].pk
    )


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 2), ("containsAll", 1)]
)
def test_products_query_with_attr_slug_and_attribute_value_reference_to_product_variants(
    query,
    filter_type,
    expected_count,
    staff_api_client,
    product_list,
    product_type,
    product_type_variant_reference_attribute,
    product_variant_list,
    channel_USD,
):
    # given
    product_type.product_attributes.add(product_type_variant_reference_attribute)

    first_variant_sku = "test-variant-1"
    second_variant_sku = "test-variant-2"

    first_variant = product_variant_list[0]
    first_variant.sku = first_variant_sku
    first_variant.save()

    second_variant = product_variant_list[1]
    second_variant.sku = second_variant_sku
    second_variant.save()

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_variant_reference_attribute,
                name=f"Variant {first_variant.pk}",
                slug=f"variant-{first_variant.pk}",
                reference_variant=first_variant,
            ),
            AttributeValue(
                attribute=product_type_variant_reference_attribute,
                name=f"Variant {second_variant.pk}",
                slug=f"variant-{second_variant.pk}",
                reference_variant=second_variant,
            ),
        ]
    )

    product_with_both_references = product_list[0]
    associate_attribute_values_to_instance(
        product_with_both_references,
        {
            product_type_variant_reference_attribute.pk: [
                attribute_value_1,
                attribute_value_2,
            ]
        },
    )

    product_with_single_reference = product_list[1]
    associate_attribute_values_to_instance(
        product_with_single_reference,
        {product_type_variant_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": "variant-reference",
                    "value": {
                        "reference": {
                            "productVariantSkus": {
                                filter_type: [
                                    first_variant_sku,
                                    second_variant_sku,
                                ]
                            }
                        }
                    },
                }
            ]
        },
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
    assert products_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_list[0].pk
    )


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 3), ("containsAll", 2)]
)
def test_products_query_with_attr_slug_attribute_value_referenced_variant_ids(
    query,
    filter_type,
    expected_count,
    staff_api_client,
    product_list,
    product_type,
    product_type_variant_reference_attribute,
    product_variant_list,
    channel_USD,
):
    # given
    product_type.product_attributes.add(
        product_type_variant_reference_attribute,
    )

    first_variant = product_variant_list[0]
    second_variant = product_variant_list[1]
    third_variant = product_variant_list[2]

    first_attr_value, second_attr_value, third_attr_value = (
        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=product_type_variant_reference_attribute,
                    name=f"Variant {first_variant.pk}",
                    slug=f"variant-{first_variant.pk}",
                    reference_variant=first_variant,
                ),
                AttributeValue(
                    attribute=product_type_variant_reference_attribute,
                    name=f"Variant {second_variant.pk}",
                    slug=f"variant-{second_variant.pk}",
                    reference_variant=second_variant,
                ),
                AttributeValue(
                    attribute=product_type_variant_reference_attribute,
                    name=f"Variant {third_variant.pk}",
                    slug=f"variant-{third_variant.pk}",
                    reference_variant=third_variant,
                ),
            ]
        )
    )
    first_product_with_all_ids = product_list[0]
    second_product_with_all_ids = product_list[1]
    product_with_single_id = product_list[2]
    associate_attribute_values_to_instance(
        first_product_with_all_ids,
        {
            product_type_variant_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        second_product_with_all_ids,
        {
            product_type_variant_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        product_with_single_id,
        {product_type_variant_reference_attribute.pk: [first_attr_value]},
    )
    referenced_first_global_id = to_global_id_or_none(first_variant)
    referenced_second_global_id = to_global_id_or_none(second_variant)
    referenced_third_global_id = to_global_id_or_none(third_variant)

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": product_type_variant_reference_attribute.slug,
                    "value": {
                        "reference": {
                            "referencedIds": {
                                filter_type: [
                                    referenced_first_global_id,
                                    referenced_second_global_id,
                                    referenced_third_global_id,
                                ]
                            }
                        }
                    },
                }
            ]
        },
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
