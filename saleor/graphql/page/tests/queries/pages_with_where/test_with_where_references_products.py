import graphene
import pytest

from ......attribute import AttributeEntityType, AttributeInputType, AttributeType
from ......attribute.models import Attribute, AttributeValue
from ......attribute.utils import associate_attribute_values_to_instance
from .....core.utils import to_global_id_or_none
from .....tests.utils import get_graphql_content
from .shared import QUERY_PAGES_WITH_WHERE


@pytest.mark.parametrize(
    ("filter_type", "expected_count"),
    [("containsAny", 2), ("containsAll", 1)],
)
def test_pages_query_with_attr_slug_and_attribute_value_reference_to_products(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_product_reference_attribute,
    product_list,
):
    # given
    page_type.page_attributes.add(page_type_product_reference_attribute)

    first_product = product_list[0]
    second_product = product_list[1]

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_product_reference_attribute,
                name=f"Product {first_product.pk}",
                slug=f"product-{first_product.pk}",
                reference_product=first_product,
            ),
            AttributeValue(
                attribute=page_type_product_reference_attribute,
                name=f"Product {second_product.pk}",
                slug=f"product-{second_product.pk}",
                reference_product=second_product,
            ),
        ]
    )

    page_with_both_references = page_list[0]
    associate_attribute_values_to_instance(
        page_with_both_references,
        {
            page_type_product_reference_attribute.pk: [
                attribute_value_1,
                attribute_value_2,
            ]
        },
    )

    page_with_single_reference = page_list[1]
    associate_attribute_values_to_instance(
        page_with_single_reference,
        {page_type_product_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": "product-reference",
                    "value": {
                        "reference": {
                            "productSlugs": {
                                filter_type: [first_product.slug, second_product.slug]
                            }
                        }
                    },
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count
    assert pages_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Page", page_list[0].pk
    )


@pytest.mark.parametrize(
    ("filter_type", "expected_count"),
    [("containsAny", 2), ("containsAll", 1)],
)
def test_pages_query_with_attribute_value_reference_to_products(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_product_reference_attribute,
    product_list,
):
    # given
    second_product_reference_attribute = Attribute.objects.create(
        slug="second-product-reference",
        name="Product reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT,
    )

    page_type.page_attributes.add(page_type_product_reference_attribute)
    page_type.page_attributes.add(second_product_reference_attribute)

    first_product = product_list[0]
    second_product = product_list[1]

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_product_reference_attribute,
                name=f"Product {first_product.pk}",
                slug=f"product-{first_product.pk}",
                reference_product=first_product,
            ),
            AttributeValue(
                attribute=second_product_reference_attribute,
                name=f"Product {second_product.pk}",
                slug=f"product-{second_product.pk}",
                reference_product=second_product,
            ),
        ]
    )

    page_with_both_references = page_list[0]
    associate_attribute_values_to_instance(
        page_with_both_references,
        {
            page_type_product_reference_attribute.pk: [
                attribute_value_1,
            ],
            second_product_reference_attribute.pk: [attribute_value_2],
        },
    )

    page_with_single_reference = page_list[1]
    associate_attribute_values_to_instance(
        page_with_single_reference,
        {second_product_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "value": {
                        "reference": {
                            "productSlugs": {
                                filter_type: [first_product.slug, second_product.slug]
                            }
                        }
                    },
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count
    assert pages_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Page", page_list[0].pk
    )


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 3), ("containsAll", 2)]
)
def test_pages_query_with_attr_slug_and_attribute_value_referenced_product_ids(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_product_reference_attribute,
    product_list,
):
    # given
    page_type.page_attributes.add(
        page_type_product_reference_attribute,
    )
    first_product = product_list[0]
    second_product = product_list[1]
    third_product = product_list[2]

    first_attr_value, second_attr_value, third_attr_value = (
        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=page_type_product_reference_attribute,
                    name=f"Product {first_product.pk}",
                    slug=f"Product-{first_product.pk}",
                    reference_product=first_product,
                ),
                AttributeValue(
                    attribute=page_type_product_reference_attribute,
                    name=f"Product {second_product.pk}",
                    slug=f"product-{second_product.pk}",
                    reference_product=second_product,
                ),
                AttributeValue(
                    attribute=page_type_product_reference_attribute,
                    name=f"Product {third_product.pk}",
                    slug=f"Product-{third_product.pk}",
                    reference_product=third_product,
                ),
            ]
        )
    )
    fist_page_with_all_ids = page_list[0]
    second_page_with_all_ids = page_list[1]
    page_with_single_id = page_list[2]
    associate_attribute_values_to_instance(
        fist_page_with_all_ids,
        {
            page_type_product_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        second_page_with_all_ids,
        {
            page_type_product_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        page_with_single_id,
        {
            page_type_product_reference_attribute.pk: [
                first_attr_value,
            ],
        },
    )
    referenced_first_global_id = to_global_id_or_none(first_product)
    referenced_second_global_id = to_global_id_or_none(second_product)
    referenced_third_global_id = to_global_id_or_none(third_product)

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": page_type_product_reference_attribute.slug,
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
                },
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(page_list) > len(pages_nodes)
    assert len(pages_nodes) == expected_count
