import graphene
import pytest

from ......attribute import AttributeEntityType, AttributeType
from ......attribute.models import Attribute, AttributeValue
from ......attribute.utils import associate_attribute_values_to_instance
from .....core.utils import to_global_id_or_none
from .....tests.utils import get_graphql_content
from .shared import PRODUCTS_FILTER_QUERY, PRODUCTS_WHERE_QUERY


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("reference_attribute_fixture", "filter_type", "expected_count"),
    [
        # REFERENCE type - searches across all reference attributes
        ("product_type_variant_reference_attribute", "containsAny", 2),
        ("product_type_variant_reference_attribute", "containsAll", 1),
        # SINGLE_REFERENCE - product has variant1 in attr1 and variant2 in attr2
        ("product_type_variant_single_reference_attribute", "containsAny", 2),
        ("product_type_variant_single_reference_attribute", "containsAll", 1),
    ],
)
def test_products_query_with_attribute_value_reference_to_product_variants(
    query,
    reference_attribute_fixture,
    filter_type,
    expected_count,
    request,
    staff_api_client,
    product_list,
    product_type,
    product_variant_list,
    channel_USD,
):
    # given
    reference_attribute = request.getfixturevalue(reference_attribute_fixture)
    product_type.product_attributes.add(reference_attribute)
    second_variant_reference_attribute = Attribute.objects.create(
        slug="second-product-reference",
        name="Product reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=reference_attribute.input_type,
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
                attribute=reference_attribute,
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
            reference_attribute.pk: [attribute_value_1],
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
    # Verify first product when we expect results
    if expected_count > 0:
        assert products_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
            "Product", product_list[0].pk
        )


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    "scenario",
    [
        {
            "attr_fixture": "product_type_variant_reference_attribute",
            "filter": "containsAny",
            "expected": 2,
            "product_assignments": {
                "product_with_both_variants": ["test-variant-1", "test-variant-2"],
                "product_with_second_variant_only": ["test-variant-2"],
            },
            "search": ["test-variant-1", "test-variant-2"],
        },
        {
            "attr_fixture": "product_type_variant_reference_attribute",
            "filter": "containsAll",
            "expected": 1,
            "product_assignments": {
                "product_with_both_variants": ["test-variant-1", "test-variant-2"],
                "product_with_second_variant_only": ["test-variant-2"],
            },
            "search": ["test-variant-1", "test-variant-2"],
        },
        {
            "attr_fixture": "product_type_variant_single_reference_attribute",
            "filter": "containsAny",
            "expected": 2,
            "product_assignments": {
                "product_with_first_variant": ["test-variant-1"],
                "product_with_second_variant": ["test-variant-2"],
            },
            "search": ["test-variant-1", "test-variant-2"],
        },
        {
            "attr_fixture": "product_type_variant_single_reference_attribute",
            "filter": "containsAll",
            "expected": 2,
            "product_assignments": {
                "product_with_first_variant": ["test-variant-1"],
                "product_second_overridden": ["test-variant-1"],
            },
            "search": ["test-variant-1"],
        },
    ],
)
def test_products_query_with_attr_slug_and_attribute_value_reference_to_product_variants(
    query,
    scenario,
    request,
    staff_api_client,
    product_list,
    product_type,
    product_variant_list,
    channel_USD,
):
    # given
    reference_attribute = request.getfixturevalue(scenario["attr_fixture"])
    product_type.product_attributes.add(reference_attribute)

    first_variant_sku = "test-variant-1"
    second_variant_sku = "test-variant-2"

    first_variant = product_variant_list[0]
    first_variant.sku = first_variant_sku
    first_variant.save()

    second_variant = product_variant_list[1]
    second_variant.sku = second_variant_sku
    second_variant.save()

    attribute_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=reference_attribute,
                name=f"Variant {first_variant.pk}",
                slug=f"variant-{first_variant.pk}",
                reference_variant=first_variant,
            ),
            AttributeValue(
                attribute=reference_attribute,
                name=f"Variant {second_variant.pk}",
                slug=f"variant-{second_variant.pk}",
                reference_variant=second_variant,
            ),
        ]
    )

    sku_to_value = {
        first_variant_sku: attribute_values[0],
        second_variant_sku: attribute_values[1],
    }

    for product, skus in zip(
        product_list, scenario["product_assignments"].values(), strict=False
    ):
        associate_attribute_values_to_instance(
            product,
            {reference_attribute.pk: [sku_to_value[sku] for sku in skus]},
        )

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": reference_attribute.slug,
                    "value": {
                        "reference": {
                            "productVariantSkus": {
                                scenario["filter"]: scenario["search"]
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
    assert len(products_nodes) == scenario["expected"]
    # Verify first product when we expect results
    if scenario["expected"] > 0:
        assert products_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
            "Product", product_list[0].pk
        )


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    "scenario",
    [
        {
            "attr_fixture": "product_type_variant_reference_attribute",
            "filter": "containsAny",
            "expected": 3,
            "product_assignments": {
                "product_with_all_variants": [
                    "test-variant-1",
                    "test-variant-2",
                    "test-variant-3",
                ],
                "product_with_same_all_variants": [
                    "test-variant-1",
                    "test-variant-2",
                    "test-variant-3",
                ],
                "product_with_first_variant_only": ["test-variant-1"],
            },
            "search": ["test-variant-1", "test-variant-2", "test-variant-3"],
        },
        {
            "attr_fixture": "product_type_variant_reference_attribute",
            "filter": "containsAll",
            "expected": 2,
            "product_assignments": {
                "product_with_all_variants": [
                    "test-variant-1",
                    "test-variant-2",
                    "test-variant-3",
                ],
                "product_with_same_all_variants": [
                    "test-variant-1",
                    "test-variant-2",
                    "test-variant-3",
                ],
                "product_with_first_variant_only": ["test-variant-1"],
            },
            "search": ["test-variant-1", "test-variant-2", "test-variant-3"],
        },
        {
            "attr_fixture": "product_type_variant_single_reference_attribute",
            "filter": "containsAny",
            "expected": 3,
            "product_assignments": {
                "product_with_first_variant": ["test-variant-1"],
                "product_with_second_variant": ["test-variant-2"],
                "product_with_third_variant": ["test-variant-3"],
            },
            "search": ["test-variant-1", "test-variant-2", "test-variant-3"],
        },
        {
            "attr_fixture": "product_type_variant_single_reference_attribute",
            "filter": "containsAll",
            "expected": 1,
            "product_assignments": {
                "product_with_first_variant": ["test-variant-1"],
                "product_with_second_variant": ["test-variant-2"],
                "product_with_third_variant": ["test-variant-3"],
            },
            "search": ["test-variant-1"],
        },
    ],
)
def test_products_query_with_attr_slug_attribute_value_referenced_variant_ids(
    query,
    scenario,
    request,
    staff_api_client,
    product_list,
    product_type,
    product_variant_list,
    channel_USD,
):
    # given
    reference_attribute = request.getfixturevalue(scenario["attr_fixture"])
    product_type.product_attributes.add(reference_attribute)

    first_variant = product_variant_list[0]
    second_variant = product_variant_list[1]
    third_variant = product_variant_list[2]

    first_variant.sku = "test-variant-1"
    first_variant.save()

    second_variant.sku = "test-variant-2"
    second_variant.save()

    third_variant.sku = "test-variant-3"
    third_variant.save()

    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=reference_attribute,
                name=f"Variant {first_variant.pk}",
                slug=f"variant-{first_variant.pk}",
                reference_variant=first_variant,
            ),
            AttributeValue(
                attribute=reference_attribute,
                name=f"Variant {second_variant.pk}",
                slug=f"variant-{second_variant.pk}",
                reference_variant=second_variant,
            ),
            AttributeValue(
                attribute=reference_attribute,
                name=f"Variant {third_variant.pk}",
                slug=f"variant-{third_variant.pk}",
                reference_variant=third_variant,
            ),
        ]
    )

    # Assign values based on product_value_assignments configuration
    sku_to_value = {
        first_variant.sku: attr_values[0],
        second_variant.sku: attr_values[1],
        third_variant.sku: attr_values[2],
    }

    for product, skus in zip(
        product_list, scenario["product_assignments"].values(), strict=False
    ):
        associate_attribute_values_to_instance(
            product,
            {reference_attribute.pk: [sku_to_value[sku] for sku in skus]},
        )

    ref_lookup = {
        variant.sku: variant
        for variant in [first_variant, second_variant, third_variant]
    }
    search_ids = [to_global_id_or_none(ref_lookup[sku]) for sku in scenario["search"]]

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": reference_attribute.slug,
                    "value": {
                        "reference": {"referencedIds": {scenario["filter"]: search_ids}}
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
    assert len(products_nodes) == scenario["expected"]
