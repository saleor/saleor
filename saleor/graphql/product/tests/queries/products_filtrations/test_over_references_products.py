import graphene
import pytest

from ......attribute import AttributeEntityType, AttributeInputType, AttributeType
from ......attribute.models import Attribute, AttributeValue
from ......attribute.utils import associate_attribute_values_to_instance
from ......product.models import Product
from .....core.utils import to_global_id_or_none
from .....tests.utils import get_graphql_content
from .shared import PRODUCTS_FILTER_QUERY, PRODUCTS_WHERE_QUERY


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("filter_type", "expected_count"),
    [("containsAny", 2), ("containsAll", 1)],
)
def test_products_query_with_attr_slug_and_attribute_value_reference_to_products(
    query,
    filter_type,
    expected_count,
    staff_api_client,
    product_list,
    product_type,
    product_type_product_reference_attribute,
    channel_USD,
):
    # given
    product_type.product_attributes.add(product_type_product_reference_attribute)

    ref_product_1, ref_product_2 = Product.objects.bulk_create(
        [
            Product(
                name="Reference Product 1",
                slug="ref-1",
                product_type=product_type,
            ),
            Product(
                name="Reference Product 2",
                slug="ref-2",
                product_type=product_type,
            ),
        ]
    )

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_product_reference_attribute,
                name=f"Product {ref_product_1.pk}",
                slug=f"product-{ref_product_1.pk}",
                reference_product=ref_product_1,
            ),
            AttributeValue(
                attribute=product_type_product_reference_attribute,
                name=f"Product {ref_product_2.pk}",
                slug=f"product-{ref_product_2.pk}",
                reference_product=ref_product_2,
            ),
        ]
    )

    product_with_both_references = product_list[0]
    associate_attribute_values_to_instance(
        product_with_both_references,
        {
            product_type_product_reference_attribute.pk: [
                attribute_value_1,
                attribute_value_2,
            ]
        },
    )

    product_with_single_reference = product_list[1]
    associate_attribute_values_to_instance(
        product_with_single_reference,
        {product_type_product_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": "product-reference",
                    "value": {
                        "reference": {
                            "productSlugs": {
                                filter_type: [ref_product_1.slug, ref_product_2.slug]
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
    ("filter_type", "expected_count"),
    [("containsAny", 2), ("containsAll", 1)],
)
def test_products_query_with_attribute_value_reference_to_products(
    query,
    filter_type,
    expected_count,
    staff_api_client,
    product_list,
    product_type,
    product_type_product_reference_attribute,
    channel_USD,
):
    # given
    second_product_reference_attribute = Attribute.objects.create(
        slug="second-product-reference",
        name="Product reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT,
    )

    product_type.product_attributes.add(
        product_type_product_reference_attribute,
        second_product_reference_attribute,
    )

    ref_product_1, ref_product_2 = Product.objects.bulk_create(
        [
            Product(
                name="Reference Product 1",
                slug="ref-1",
                product_type=product_type,
            ),
            Product(
                name="Reference Product 2",
                slug="ref-2",
                product_type=product_type,
            ),
        ]
    )

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_product_reference_attribute,
                name=f"Product {ref_product_1.pk}",
                slug=f"product-{ref_product_1.pk}",
                reference_product=ref_product_1,
            ),
            AttributeValue(
                attribute=second_product_reference_attribute,
                name=f"Product {ref_product_2.pk}",
                slug=f"product-{ref_product_2.pk}",
                reference_product=ref_product_2,
            ),
        ]
    )

    product_with_both_references = product_list[0]
    associate_attribute_values_to_instance(
        product_with_both_references,
        {
            product_type_product_reference_attribute.pk: [attribute_value_1],
            second_product_reference_attribute.pk: [attribute_value_2],
        },
    )

    product_with_single_reference = product_list[1]
    associate_attribute_values_to_instance(
        product_with_single_reference,
        {second_product_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "value": {
                        "reference": {
                            "productSlugs": {
                                filter_type: [ref_product_1.slug, ref_product_2.slug]
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
def test_products_query_with_attr_slug_and_attribute_value_referenced_product_ids(
    query,
    filter_type,
    expected_count,
    staff_api_client,
    product_list,
    product_type,
    product_type_product_reference_attribute,
    channel_USD,
):
    # given
    product_type.product_attributes.add(
        product_type_product_reference_attribute,
    )
    # Create additional products to use as references
    ref_product_1, ref_product_2, ref_product_3 = Product.objects.bulk_create(
        [
            Product(
                name="Reference Product 1",
                slug="ref-1",
                product_type=product_type,
            ),
            Product(
                name="Reference Product 2",
                slug="ref-2",
                product_type=product_type,
            ),
            Product(
                name="Reference Product 3",
                slug="ref-3",
                product_type=product_type,
            ),
        ]
    )

    first_attr_value, second_attr_value, third_attr_value = (
        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=product_type_product_reference_attribute,
                    name=f"Product {ref_product_1.pk}",
                    slug=f"product-{ref_product_1.pk}",
                    reference_product=ref_product_1,
                ),
                AttributeValue(
                    attribute=product_type_product_reference_attribute,
                    name=f"Product {ref_product_2.pk}",
                    slug=f"product-{ref_product_2.pk}",
                    reference_product=ref_product_2,
                ),
                AttributeValue(
                    attribute=product_type_product_reference_attribute,
                    name=f"Product {ref_product_3.pk}",
                    slug=f"product-{ref_product_3.pk}",
                    reference_product=ref_product_3,
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
            product_type_product_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        second_product_with_all_ids,
        {
            product_type_product_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        product_with_single_id,
        {
            product_type_product_reference_attribute.pk: [
                first_attr_value,
            ],
        },
    )
    ref_1_global_id = to_global_id_or_none(ref_product_1)
    ref_2_global_id = to_global_id_or_none(ref_product_2)
    ref_3_global_id = to_global_id_or_none(ref_product_3)

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": product_type_product_reference_attribute.slug,
                    "value": {
                        "reference": {
                            "referencedIds": {
                                filter_type: [
                                    ref_1_global_id,
                                    ref_2_global_id,
                                    ref_3_global_id,
                                ]
                            }
                        }
                    },
                },
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
