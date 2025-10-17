import graphene
import pytest

from ......attribute import AttributeEntityType, AttributeType
from ......attribute.models import Attribute, AttributeValue
from ......attribute.utils import associate_attribute_values_to_instance
from ......product.models import Product
from .....core.utils import to_global_id_or_none
from .....tests.utils import get_graphql_content
from .shared import PRODUCTS_FILTER_QUERY, PRODUCTS_WHERE_QUERY


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    (
        "reference_attribute_fixture",
        "filter_type",
        "expected_count",
        "product1_values",
        "product2_values",
        "search_values",
    ),
    [
        # REFERENCE type - can assign multiple values to one product
        (
            "product_type_product_reference_attribute",
            "containsAny",
            2,
            [0, 1],
            [1],
            [0, 1],
        ),
        (
            "product_type_product_reference_attribute",
            "containsAll",
            1,
            [0, 1],
            [1],
            [0, 1],
        ),
        # SINGLE_REFERENCE type - can only assign one value
        (
            "product_type_product_single_reference_attribute",
            "containsAny",
            2,
            [0],
            [1],
            [0, 1],
        ),
        # For SINGLE_REFERENCE containsAll, search for just one value that both products have
        (
            "product_type_product_single_reference_attribute",
            "containsAll",
            2,
            [0],
            [0],
            [0],
        ),
    ],
)
def test_products_query_with_attr_slug_and_attribute_value_reference_to_products(
    query,
    reference_attribute_fixture,
    filter_type,
    expected_count,
    product1_values,
    product2_values,
    search_values,
    request,
    staff_api_client,
    product_list,
    product_type,
    channel_USD,
):
    # given
    reference_attribute = request.getfixturevalue(reference_attribute_fixture)
    product_type.product_attributes.add(reference_attribute)

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

    attribute_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=reference_attribute,
                name=f"Product {ref_product_1.pk}",
                slug=f"product-{ref_product_1.pk}",
                reference_product=ref_product_1,
            ),
            AttributeValue(
                attribute=reference_attribute,
                name=f"Product {ref_product_2.pk}",
                slug=f"product-{ref_product_2.pk}",
                reference_product=ref_product_2,
            ),
        ]
    )

    product_with_both_references = product_list[0]
    # Assign values based on product1_values indices
    associate_attribute_values_to_instance(
        product_with_both_references,
        {reference_attribute.pk: [attribute_values[i] for i in product1_values]},
    )

    product_with_single_reference = product_list[1]
    associate_attribute_values_to_instance(
        product_with_single_reference,
        {reference_attribute.pk: [attribute_values[i] for i in product2_values]},
    )

    # Build search slugs based on search_values indices
    ref_products = [ref_product_1, ref_product_2]
    search_slugs = [ref_products[i].slug for i in search_values]

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": reference_attribute.slug,
                    "value": {
                        "reference": {"productSlugs": {filter_type: search_slugs}}
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
    # Verify first product when we expect results
    if expected_count > 0:
        assert products_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
            "Product", product_list[0].pk
        )


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("reference_attribute_fixture", "filter_type", "expected_count"),
    [
        # REFERENCE type - searches across all reference attributes
        ("product_type_product_reference_attribute", "containsAny", 2),
        ("product_type_product_reference_attribute", "containsAll", 1),
        # SINGLE_REFERENCE - product has ref1 in attr1 and ref2 in attr2
        ("product_type_product_single_reference_attribute", "containsAny", 2),
        ("product_type_product_single_reference_attribute", "containsAll", 1),
    ],
)
def test_products_query_with_attribute_value_reference_to_products(
    query,
    reference_attribute_fixture,
    filter_type,
    expected_count,
    request,
    staff_api_client,
    product_list,
    product_type,
    channel_USD,
):
    # given
    reference_attribute = request.getfixturevalue(reference_attribute_fixture)
    second_product_reference_attribute = Attribute.objects.create(
        slug="second-product-reference",
        name="Product reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=reference_attribute.input_type,  # Use same type as main attribute
        entity_type=AttributeEntityType.PRODUCT,
    )

    product_type.product_attributes.add(
        reference_attribute,
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
                attribute=reference_attribute,
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
    # Always assign one value per attribute for this test (no slug test)
    associate_attribute_values_to_instance(
        product_with_both_references,
        {
            reference_attribute.pk: [attribute_value_1],
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
    # Verify first product when we expect results
    if expected_count > 0:
        assert products_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
            "Product", product_list[0].pk
        )


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    (
        "reference_attribute_fixture",
        "filter_type",
        "expected_count",
        "product_value_assignments",
        "search_indices",
    ),
    [
        # REFERENCE type - products can have multiple values
        (
            "product_type_product_reference_attribute",
            "containsAny",
            3,
            [[0, 1, 2], [0, 1, 2], [0]],
            [0, 1, 2],
        ),  # Search for all 3 refs
        (
            "product_type_product_reference_attribute",
            "containsAll",
            2,
            [[0, 1, 2], [0, 1, 2], [0]],
            [0, 1, 2],
        ),  # Search for all 3 refs
        # SINGLE_REFERENCE - each product has one value
        (
            "product_type_product_single_reference_attribute",
            "containsAny",
            3,
            [[0], [1], [2]],
            [0, 1, 2],
        ),  # Search for all 3 refs
        # For containsAll with SINGLE_REFERENCE, search for single value
        (
            "product_type_product_single_reference_attribute",
            "containsAll",
            1,
            [[0], [1], [2]],
            [0],
        ),  # Search for just ref[0], only product1 has it
    ],
)
def test_products_query_with_attr_slug_and_attribute_value_referenced_product_ids(
    query,
    reference_attribute_fixture,
    filter_type,
    expected_count,
    product_value_assignments,
    search_indices,
    request,
    staff_api_client,
    product_list,
    product_type,
    channel_USD,
):
    # given
    reference_attribute = request.getfixturevalue(reference_attribute_fixture)
    product_type.product_attributes.add(reference_attribute)

    # Create additional products to use as references
    ref_products = Product.objects.bulk_create(
        [
            Product(
                name=f"Reference Product {i + 1}",
                slug=f"ref-{i + 1}",
                product_type=product_type,
            )
            for i in range(3)
        ]
    )

    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=reference_attribute,
                name=f"Product {ref_product.pk}",
                slug=f"product-{ref_product.pk}",
                reference_product=ref_product,
            )
            for ref_product in ref_products
        ]
    )

    # Assign values based on product_value_assignments configuration
    for product, value_indices in zip(
        product_list, product_value_assignments, strict=False
    ):
        associate_attribute_values_to_instance(
            product,
            {reference_attribute.pk: [attr_values[i] for i in value_indices]},
        )

    ref_global_ids = [to_global_id_or_none(ref) for ref in ref_products]
    # Build search IDs based on search_indices
    search_ids = [ref_global_ids[i] for i in search_indices]

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": reference_attribute.slug,
                    "value": {
                        "reference": {"referencedIds": {filter_type: search_ids}}
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
