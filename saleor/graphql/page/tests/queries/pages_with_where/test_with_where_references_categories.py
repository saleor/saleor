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
def test_pages_query_with_attr_slug_and_attribute_value_reference_to_categories(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_category_reference_attribute,
    category_list,
):
    # given
    page_type.page_attributes.add(page_type_category_reference_attribute)

    first_category = category_list[0]
    second_category = category_list[1]

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_category_reference_attribute,
                name=f"Category {first_category.pk}",
                slug=f"category-{first_category.pk}",
                reference_category=first_category,
            ),
            AttributeValue(
                attribute=page_type_category_reference_attribute,
                name=f"Category {second_category.pk}",
                slug=f"category-{second_category.pk}",
                reference_category=second_category,
            ),
        ]
    )

    page_with_both_references = page_list[0]
    associate_attribute_values_to_instance(
        page_with_both_references,
        {
            page_type_category_reference_attribute.pk: [
                attribute_value_1,
                attribute_value_2,
            ]
        },
    )

    page_with_single_reference = page_list[1]
    associate_attribute_values_to_instance(
        page_with_single_reference,
        {page_type_category_reference_attribute.pk: [attribute_value_2]},
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
def test_pages_query_with_attribute_value_reference_to_category(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_category_reference_attribute,
    category_list,
):
    # given
    second_category_reference_attribute = Attribute.objects.create(
        slug="second-category-reference",
        name="category reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.CATEGORY,
    )

    page_type.page_attributes.add(page_type_category_reference_attribute)
    page_type.page_attributes.add(second_category_reference_attribute)

    first_category = category_list[0]
    second_category = category_list[1]

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_category_reference_attribute,
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

    page_with_both_references = page_list[0]
    associate_attribute_values_to_instance(
        page_with_both_references,
        {
            page_type_category_reference_attribute.pk: [
                attribute_value_1,
            ],
            second_category_reference_attribute.pk: [attribute_value_2],
        },
    )

    page_with_single_reference = page_list[1]
    associate_attribute_values_to_instance(
        page_with_single_reference,
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
def test_pages_query_with_attr_slug_and_attribute_value_referenced_category_ids(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_category_reference_attribute,
    category_list,
):
    # given
    page_type.page_attributes.add(
        page_type_category_reference_attribute,
    )
    first_category = category_list[0]
    second_category = category_list[1]
    third_category = category_list[2]

    first_attr_value, second_attr_value, third_attr_value = (
        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=page_type_category_reference_attribute,
                    name=f"Category {first_category.pk}",
                    slug=f"category-{first_category.pk}",
                    reference_category=first_category,
                ),
                AttributeValue(
                    attribute=page_type_category_reference_attribute,
                    name=f"Category {second_category.pk}",
                    slug=f"category-{second_category.pk}",
                    reference_category=second_category,
                ),
                AttributeValue(
                    attribute=page_type_category_reference_attribute,
                    name=f"Category {third_category.pk}",
                    slug=f"category-{third_category.pk}",
                    reference_category=third_category,
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
            page_type_category_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        second_page_with_all_ids,
        {
            page_type_category_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        page_with_single_id,
        {
            page_type_category_reference_attribute.pk: [
                first_attr_value,
            ],
        },
    )
    referenced_first_global_id = to_global_id_or_none(first_category)
    referenced_second_global_id = to_global_id_or_none(second_category)
    referenced_third_global_id = to_global_id_or_none(third_category)

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": page_type_category_reference_attribute.slug,
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
