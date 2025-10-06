import pytest

from ......attribute import AttributeEntityType, AttributeInputType, AttributeType
from ......attribute.models import Attribute, AttributeValue
from ......attribute.utils import associate_attribute_values_to_instance
from .....core.utils import to_global_id_or_none
from .....tests.utils import get_graphql_content
from .shared import PRODUCT_VARIANTS_WHERE_QUERY


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 2), ("containsAll", 1)]
)
def test_product_variants_query_with_attr_slug_and_attribute_value_reference_to_categories(
    filter_type,
    expected_count,
    staff_api_client,
    product_variant_list,
    product_type_category_reference_attribute,
    channel_USD,
    category_list,
):
    # given
    product_type = product_variant_list[0].product.product_type
    product_type.variant_attributes.add(product_type_category_reference_attribute)

    first_category = category_list[0]
    second_category = category_list[1]

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_category_reference_attribute,
                name=f"Category {first_category.pk}",
                slug=f"category-{first_category.pk}",
                reference_category=first_category,
            ),
            AttributeValue(
                attribute=product_type_category_reference_attribute,
                name=f"Category {second_category.pk}",
                slug=f"category-{second_category.pk}",
                reference_category=second_category,
            ),
        ]
    )
    product_variant_with_both_references = product_variant_list[0]
    associate_attribute_values_to_instance(
        product_variant_with_both_references,
        {
            product_type_category_reference_attribute.pk: [
                attribute_value_1,
                attribute_value_2,
            ]
        },
    )

    product_variant_with_single_reference = product_variant_list[1]
    associate_attribute_values_to_instance(
        product_variant_with_single_reference,
        {product_type_category_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": "category-reference",
                    "value": {
                        "reference": {
                            "categorySlugs": {
                                filter_type: [first_category.slug, second_category.slug]
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
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    product_variants_nodes = content["data"]["productVariants"]["edges"]
    assert len(product_variants_nodes) == expected_count


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 2), ("containsAll", 1)]
)
def test_product_variants_query_with_attribute_value_reference_to_categories(
    filter_type,
    expected_count,
    staff_api_client,
    product_variant_list,
    product_type,
    product_type_category_reference_attribute,
    channel_USD,
    category_list,
):
    # given
    second_category_reference_attribute = Attribute.objects.create(
        slug="second-category-reference",
        name="Category reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.CATEGORY,
    )
    product_type.variant_attributes.add(
        product_type_category_reference_attribute,
        second_category_reference_attribute,
    )

    first_category = category_list[0]
    second_category = category_list[1]

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_category_reference_attribute,
                name=f"Category {first_category.pk}",
                slug=f"category-{first_category.pk}",
                reference_category=first_category,
            ),
            AttributeValue(
                attribute=second_category_reference_attribute,
                name=f"Category {second_category.pk}",
                slug=f"category-{second_category.pk}",
                reference_category=second_category,
            ),
        ]
    )

    product_variant_with_both_references = product_variant_list[0]
    associate_attribute_values_to_instance(
        product_variant_with_both_references,
        {
            product_type_category_reference_attribute.pk: [attribute_value_1],
            second_category_reference_attribute.pk: [attribute_value_2],
        },
    )

    product_variant_with_single_reference = product_variant_list[1]
    associate_attribute_values_to_instance(
        product_variant_with_single_reference,
        {second_category_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "value": {
                        "reference": {
                            "categorySlugs": {
                                filter_type: [first_category.slug, second_category.slug]
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
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    product_variants_nodes = content["data"]["productVariants"]["edges"]
    assert len(product_variants_nodes) == expected_count


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 3), ("containsAll", 2)]
)
def test_product_variants_query_with_attr_slug_and_attribute_value_referenced_category_ids(
    filter_type,
    expected_count,
    staff_api_client,
    product_variant_list,
    product_type,
    product_type_category_reference_attribute,
    channel_USD,
    category_list,
):
    # given
    product_type.variant_attributes.add(product_type_category_reference_attribute)

    first_category = category_list[0]
    second_category = category_list[1]
    third_category = category_list[2]

    first_attr_value, second_attr_value, third_attr_value = (
        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=product_type_category_reference_attribute,
                    name=f"Category {first_category.pk}",
                    slug=f"category-{first_category.pk}",
                    reference_category=first_category,
                ),
                AttributeValue(
                    attribute=product_type_category_reference_attribute,
                    name=f"Category {second_category.pk}",
                    slug=f"category-{second_category.pk}",
                    reference_category=second_category,
                ),
                AttributeValue(
                    attribute=product_type_category_reference_attribute,
                    name=f"Category {third_category.pk}",
                    slug=f"category-{third_category.pk}",
                    reference_category=third_category,
                ),
            ]
        )
    )
    first_product_variant_with_all_ids = product_variant_list[0]
    second_product_variant_with_all_ids = product_variant_list[1]
    product_variant_with_single_id = product_variant_list[3]
    associate_attribute_values_to_instance(
        first_product_variant_with_all_ids,
        {
            product_type_category_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        second_product_variant_with_all_ids,
        {
            product_type_category_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        product_variant_with_single_id,
        {product_type_category_reference_attribute.pk: [first_attr_value]},
    )

    referenced_first_global_id = to_global_id_or_none(first_category)
    referenced_second_global_id = to_global_id_or_none(second_category)
    referenced_third_global_id = to_global_id_or_none(third_category)

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": product_type_category_reference_attribute.slug,
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
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    product_variants_nodes = content["data"]["productVariants"]["edges"]
    assert len(product_variants_nodes) == expected_count
