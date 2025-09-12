import pytest

from ......attribute import AttributeEntityType, AttributeInputType, AttributeType
from ......attribute.models import Attribute, AttributeValue
from ......attribute.utils import associate_attribute_values_to_instance
from ......page.models import Page
from .....core.utils import to_global_id_or_none
from .....tests.utils import get_graphql_content
from .shared import PRODUCT_VARIANTS_WHERE_QUERY


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 2), ("containsAll", 1)]
)
def test_product_variants_query_with_attr_slug_and_attribute_value_reference_to_pages(
    filter_type,
    expected_count,
    staff_api_client,
    product_variant_list,
    page_type,
    product_type_page_reference_attribute,
    channel_USD,
):
    # given
    product_type = product_variant_list[0].product.product_type
    product_type.variant_attributes.add(product_type_page_reference_attribute)

    reference_page_1_slug = "referenced-page-1"
    reference_page_2_slug = "referenced-page-2"
    referenced_page_1, referenced_page_2 = Page.objects.bulk_create(
        [
            Page(
                title="Referenced Page 1",
                slug=reference_page_1_slug,
                page_type=page_type,
                is_published=True,
            ),
            Page(
                title="Referenced Page 2",
                slug=reference_page_2_slug,
                page_type=page_type,
                is_published=True,
            ),
        ]
    )

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                name=f"Page {referenced_page_1.pk}",
                slug=f"page-{referenced_page_1.pk}",
                reference_page=referenced_page_1,
            ),
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                name=f"Page {referenced_page_2.pk}",
                slug=f"page-{referenced_page_2.pk}",
                reference_page=referenced_page_2,
            ),
        ]
    )
    product_variant_with_both_references = product_variant_list[0]
    associate_attribute_values_to_instance(
        product_variant_with_both_references,
        {
            product_type_page_reference_attribute.pk: [
                attribute_value_1,
                attribute_value_2,
            ]
        },
    )

    product_variant_with_single_reference = product_variant_list[1]
    associate_attribute_values_to_instance(
        product_variant_with_single_reference,
        {product_type_page_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": "product-page-reference",
                    "value": {
                        "reference": {
                            "pageSlugs": {
                                filter_type: [
                                    reference_page_1_slug,
                                    reference_page_2_slug,
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


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 2), ("containsAll", 1)]
)
def test_product_variants_query_with_attribute_value_reference_to_pages(
    filter_type,
    expected_count,
    staff_api_client,
    product_variant_list,
    product_type,
    page_type,
    product_type_page_reference_attribute,
    channel_USD,
):
    # given
    second_page_reference_attribute = Attribute.objects.create(
        slug="second-page-reference",
        name="Page reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PAGE,
    )
    product_type.variant_attributes.add(
        product_type_page_reference_attribute,
        second_page_reference_attribute,
    )

    reference_1 = "referenced-page-1"
    reference_2 = "referenced-page-2"
    referenced_page_1, referenced_page_2 = Page.objects.bulk_create(
        [
            Page(
                title="Referenced Page 1",
                slug=reference_1,
                page_type=page_type,
                is_published=True,
            ),
            Page(
                title="Referenced Page 2",
                slug=reference_2,
                page_type=page_type,
                is_published=True,
            ),
        ]
    )

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                name=f"Page {referenced_page_1.pk}",
                slug=f"page-{referenced_page_1.pk}",
                reference_page=referenced_page_1,
            ),
            AttributeValue(
                attribute=second_page_reference_attribute,
                name=f"Page {referenced_page_2.pk}",
                slug=f"page-{referenced_page_2.pk}",
                reference_page=referenced_page_2,
            ),
        ]
    )
    product_variant_with_both_references = product_variant_list[0]
    associate_attribute_values_to_instance(
        product_variant_with_both_references,
        {
            product_type_page_reference_attribute.pk: [attribute_value_1],
            second_page_reference_attribute.pk: [attribute_value_2],
        },
    )

    product_variant_with_single_reference = product_variant_list[1]
    associate_attribute_values_to_instance(
        product_variant_with_single_reference,
        {second_page_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "value": {
                        "reference": {
                            "pageSlugs": {filter_type: [reference_1, reference_2]}
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
def test_product_variants_query_with_attr_slug_and_attribute_value_referenced_page_ids(
    filter_type,
    expected_count,
    staff_api_client,
    product_variant_list,
    product_type,
    page_type,
    product_type_page_reference_attribute,
    channel_USD,
):
    # given
    product_type.variant_attributes.add(product_type_page_reference_attribute)

    referenced_first_page, referenced_second_page, referenced_third_page = (
        Page.objects.bulk_create(
            [
                Page(
                    title="Referenced Page",
                    slug="referenced-page",
                    page_type=page_type,
                    is_published=True,
                ),
                Page(
                    title="Referenced Page",
                    slug="referenced-page2",
                    page_type=page_type,
                    is_published=True,
                ),
                Page(
                    title="Referenced Page",
                    slug="referenced-page3",
                    page_type=page_type,
                    is_published=True,
                ),
            ]
        )
    )

    first_attr_value, second_attr_value, third_attr_value = (
        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=product_type_page_reference_attribute,
                    name=f"Page {referenced_first_page.pk}",
                    slug=f"page-{referenced_first_page.pk}",
                    reference_page=referenced_first_page,
                ),
                AttributeValue(
                    attribute=product_type_page_reference_attribute,
                    name=f"Page {referenced_second_page.pk}",
                    slug=f"page-{referenced_second_page.pk}",
                    reference_page=referenced_second_page,
                ),
                AttributeValue(
                    attribute=product_type_page_reference_attribute,
                    name=f"Page {referenced_third_page.pk}",
                    slug=f"page-{referenced_third_page.pk}",
                    reference_page=referenced_third_page,
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
            product_type_page_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        second_product_variant_with_all_ids,
        {
            product_type_page_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        product_variant_with_single_id,
        {product_type_page_reference_attribute.pk: [first_attr_value]},
    )

    referenced_first_global_id = to_global_id_or_none(referenced_first_page)
    referenced_second_global_id = to_global_id_or_none(referenced_second_page)
    referenced_third_global_id = to_global_id_or_none(referenced_third_page)

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": product_type_page_reference_attribute.slug,
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
