import graphene
import pytest

from ......attribute import AttributeEntityType, AttributeType
from ......attribute.models import Attribute, AttributeValue
from ......attribute.utils import associate_attribute_values_to_instance
from ......page.models import Page
from .....core.utils import to_global_id_or_none
from .....tests.utils import get_graphql_content
from .shared import PRODUCTS_FILTER_QUERY, PRODUCTS_WHERE_QUERY


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    "scenario",
    [
        {
            "attr_fixture": "product_type_page_reference_attribute",
            "filter": "containsAny",
            "expected": 2,
            "product_assignments": {
                "product_with_both_pages": ["ref-1", "ref-2"],
                "product_with_second_page_only": ["ref-2"],
            },
            "search": ["ref-1", "ref-2"],
        },
        {
            "attr_fixture": "product_type_page_reference_attribute",
            "filter": "containsAll",
            "expected": 1,
            "product_assignments": {
                "product_with_both_pages": ["ref-1", "ref-2"],
                "product_with_second_page_only": ["ref-2"],
            },
            "search": ["ref-1", "ref-2"],
        },
        {
            "attr_fixture": "product_type_page_single_reference_attribute",
            "filter": "containsAny",
            "expected": 2,
            "product_assignments": {
                "product_with_first_page": ["ref-1"],
                "product_with_second_page": ["ref-2"],
            },
            "search": ["ref-1", "ref-2"],
        },
        {
            "attr_fixture": "product_type_page_single_reference_attribute",
            "filter": "containsAll",
            "expected": 2,
            "product_assignments": {
                "product_with_first_page": ["ref-1"],
                "product_second_overridden": ["ref-1"],
            },
            "search": ["ref-1"],
        },
    ],
)
def test_products_query_with_attr_slug_and_attribute_value_reference_to_pages(
    query,
    scenario,
    request,
    staff_api_client,
    product_list,
    product_type,
    page_type,
    channel_USD,
):
    # given
    reference_attribute = request.getfixturevalue(scenario["attr_fixture"])
    product_type.product_attributes.add(reference_attribute)

    ref_page_1, ref_page_2 = Page.objects.bulk_create(
        [
            Page(
                title="Reference Page 1",
                slug="ref-1",
                page_type=page_type,
                is_published=True,
            ),
            Page(
                title="Reference Page 2",
                slug="ref-2",
                page_type=page_type,
                is_published=True,
            ),
        ]
    )

    attribute_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=reference_attribute,
                name=f"Page {ref_page_1.pk}",
                slug=f"page-{ref_page_1.pk}",
                reference_page=ref_page_1,
            ),
            AttributeValue(
                attribute=reference_attribute,
                name=f"Page {ref_page_2.pk}",
                slug=f"page-{ref_page_2.pk}",
                reference_page=ref_page_2,
            ),
        ]
    )

    slug_to_value = {
        ref_page_1.slug: attribute_values[0],
        ref_page_2.slug: attribute_values[1],
    }

    for product, slugs in zip(
        product_list, scenario["product_assignments"].values(), strict=False
    ):
        associate_attribute_values_to_instance(
            product,
            {reference_attribute.pk: [slug_to_value[slug] for slug in slugs]},
        )

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": reference_attribute.slug,
                    "value": {
                        "reference": {
                            "pageSlugs": {scenario["filter"]: scenario["search"]}
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
    assert products_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_list[0].pk
    )


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("reference_attribute_fixture", "filter_type", "expected_count"),
    [
        # REFERENCE type - searches across all reference attributes
        ("product_type_page_reference_attribute", "containsAny", 2),
        ("product_type_page_reference_attribute", "containsAll", 1),
        # SINGLE_REFERENCE - product has page1 in attr1 and page2 in attr2
        ("product_type_page_single_reference_attribute", "containsAny", 2),
        ("product_type_page_single_reference_attribute", "containsAll", 1),
    ],
)
def test_products_query_with_attribute_value_reference_to_pages(
    query,
    reference_attribute_fixture,
    filter_type,
    expected_count,
    request,
    staff_api_client,
    product_list,
    product_type,
    page_type,
    channel_USD,
):
    # given
    reference_attribute = request.getfixturevalue(reference_attribute_fixture)
    second_page_reference_attribute = Attribute.objects.create(
        slug="second-page-reference",
        name="Page reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=reference_attribute.input_type,
        entity_type=AttributeEntityType.PAGE,
    )

    product_type.product_attributes.add(
        reference_attribute,
        second_page_reference_attribute,
    )

    ref_page_1, ref_page_2 = Page.objects.bulk_create(
        [
            Page(
                title="Reference Page 1",
                slug="ref-1",
                page_type=page_type,
                is_published=True,
            ),
            Page(
                title="Reference Page 2",
                slug="ref-2",
                page_type=page_type,
                is_published=True,
            ),
        ]
    )

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=reference_attribute,
                name=f"Page {ref_page_1.pk}",
                slug=f"page-{ref_page_1.pk}",
                reference_page=ref_page_1,
            ),
            AttributeValue(
                attribute=second_page_reference_attribute,
                name=f"Page {ref_page_2.pk}",
                slug=f"page-{ref_page_2.pk}",
                reference_page=ref_page_2,
            ),
        ]
    )

    product_with_both_references = product_list[0]

    # Always assign one value per attribute for this test (no slug test)
    associate_attribute_values_to_instance(
        product_with_both_references,
        {
            reference_attribute.pk: [attribute_value_1],
            second_page_reference_attribute.pk: [attribute_value_2],
        },
    )

    product_with_single_reference = product_list[1]
    associate_attribute_values_to_instance(
        product_with_single_reference,
        {second_page_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "value": {
                        "reference": {
                            "pageSlugs": {
                                filter_type: [ref_page_1.slug, ref_page_2.slug]
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
    "scenario",
    [
        {
            "attr_fixture": "product_type_page_reference_attribute",
            "filter": "containsAny",
            "expected": 3,
            "product_assignments": {
                "product_with_all_pages": ["ref-1", "ref-2", "ref-3"],
                "product_with_same_all_pages": ["ref-1", "ref-2", "ref-3"],
                "product_with_first_page_only": ["ref-1"],
            },
            "search": ["ref-1", "ref-2", "ref-3"],
        },
        {
            "attr_fixture": "product_type_page_reference_attribute",
            "filter": "containsAll",
            "expected": 2,
            "product_assignments": {
                "product_with_all_pages": ["ref-1", "ref-2", "ref-3"],
                "product_with_same_all_pages": ["ref-1", "ref-2", "ref-3"],
                "product_with_first_page_only": ["ref-1"],
            },
            "search": ["ref-1", "ref-2", "ref-3"],
        },
        {
            "attr_fixture": "product_type_page_single_reference_attribute",
            "filter": "containsAny",
            "expected": 3,
            "product_assignments": {
                "product_with_first_page": ["ref-1"],
                "product_with_second_page": ["ref-2"],
                "product_with_third_page": ["ref-3"],
            },
            "search": ["ref-1", "ref-2", "ref-3"],
        },
        {
            "attr_fixture": "product_type_page_single_reference_attribute",
            "filter": "containsAll",
            "expected": 1,
            "product_assignments": {
                "product_with_first_page": ["ref-1"],
                "product_with_second_page": ["ref-2"],
                "product_with_third_page": ["ref-3"],
            },
            "search": ["ref-1"],
        },
    ],
)
def test_products_query_with_attr_slug_and_attribute_value_referenced_page_ids(
    query,
    scenario,
    request,
    staff_api_client,
    product_list,
    product_type,
    page_type,
    channel_USD,
):
    # given
    reference_attribute = request.getfixturevalue(scenario["attr_fixture"])
    product_type.product_attributes.add(
        reference_attribute,
    )

    ref_page_1, ref_page_2, ref_page_3 = Page.objects.bulk_create(
        [
            Page(
                title="Reference Page 1",
                slug="ref-1",
                page_type=page_type,
                is_published=True,
            ),
            Page(
                title="Reference Page 2",
                slug="ref-2",
                page_type=page_type,
                is_published=True,
            ),
            Page(
                title="Reference Page 3",
                slug="ref-3",
                page_type=page_type,
                is_published=True,
            ),
        ]
    )

    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=reference_attribute,
                name=f"Page {ref_page_1.pk}",
                slug=f"page-{ref_page_1.pk}",
                reference_page=ref_page_1,
            ),
            AttributeValue(
                attribute=reference_attribute,
                name=f"Page {ref_page_2.pk}",
                slug=f"page-{ref_page_2.pk}",
                reference_page=ref_page_2,
            ),
            AttributeValue(
                attribute=reference_attribute,
                name=f"Page {ref_page_3.pk}",
                slug=f"page-{ref_page_3.pk}",
                reference_page=ref_page_3,
            ),
        ]
    )

    slug_to_value = {
        ref_page_1.slug: attr_values[0],
        ref_page_2.slug: attr_values[1],
        ref_page_3.slug: attr_values[2],
    }

    for product, slugs in zip(
        product_list, scenario["product_assignments"].values(), strict=False
    ):
        associate_attribute_values_to_instance(
            product,
            {reference_attribute.pk: [slug_to_value[slug] for slug in slugs]},
        )

    ref_lookup = {page.slug: page for page in [ref_page_1, ref_page_2, ref_page_3]}
    search_ids = [to_global_id_or_none(ref_lookup[slug]) for slug in scenario["search"]]

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": reference_attribute.slug,
                    "value": {
                        "reference": {"referencedIds": {scenario["filter"]: search_ids}}
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
    assert len(products_nodes) == scenario["expected"]
