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
def test_products_query_with_attr_slug_and_attribute_value_reference_to_collections(
    query,
    filter_type,
    expected_count,
    staff_api_client,
    product_type,
    product_list,
    collection_list,
    product_type_collection_reference_attribute,
    channel_USD,
):
    # given
    product_type.product_attributes.add(product_type_collection_reference_attribute)

    first_collection = collection_list[0]
    second_collection = collection_list[1]

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_collection_reference_attribute,
                name=f"Category {first_collection.pk}",
                slug=f"collection-{first_collection.pk}",
                reference_collection=first_collection,
            ),
            AttributeValue(
                attribute=product_type_collection_reference_attribute,
                name=f"Category {second_collection.pk}",
                slug=f"collection-{second_collection.pk}",
                reference_collection=second_collection,
            ),
        ]
    )
    product_with_both_references = product_list[0]
    associate_attribute_values_to_instance(
        product_with_both_references,
        {
            product_type_collection_reference_attribute.pk: [
                attribute_value_1,
                attribute_value_2,
            ]
        },
    )

    product_with_single_reference = product_list[1]
    associate_attribute_values_to_instance(
        product_with_single_reference,
        {product_type_collection_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": "collection-reference",
                    "value": {
                        "reference": {
                            "collectionSlugs": {
                                filter_type: [
                                    first_collection.slug,
                                    second_collection.slug,
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


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 2), ("containsAll", 1)]
)
def test_products_query_with_attribute_value_reference_to_collections(
    query,
    filter_type,
    expected_count,
    staff_api_client,
    product_list,
    product_type,
    collection_list,
    product_type_collection_reference_attribute,
    channel_USD,
):
    # given
    second_collection_reference_attribute = Attribute.objects.create(
        slug="second-collection-reference",
        name="Category reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.COLLECTION,
    )
    product_type.product_attributes.add(
        product_type_collection_reference_attribute,
        second_collection_reference_attribute,
    )
    first_collection = collection_list[0]
    second_collection = collection_list[1]

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_collection_reference_attribute,
                name=f"Category {first_collection.pk}",
                slug=f"collection-{first_collection.pk}",
                reference_collection=first_collection,
            ),
            AttributeValue(
                attribute=second_collection_reference_attribute,
                name=f"Category {second_collection.pk}",
                slug=f"collection-{second_collection.pk}",
                reference_collection=second_collection,
            ),
        ]
    )
    product_with_both_references = product_list[0]
    associate_attribute_values_to_instance(
        product_with_both_references,
        {
            product_type_collection_reference_attribute.pk: [attribute_value_1],
            second_collection_reference_attribute.pk: [attribute_value_2],
        },
    )

    product_with_single_reference = product_list[1]
    associate_attribute_values_to_instance(
        product_with_single_reference,
        {second_collection_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "value": {
                        "reference": {
                            "collectionSlugs": {
                                filter_type: [
                                    first_collection.slug,
                                    second_collection.slug,
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


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 3), ("containsAll", 2)]
)
def test_products_query_with_attr_slug_and_attribute_value_referenced_collection_ids(
    query,
    filter_type,
    expected_count,
    staff_api_client,
    product_list,
    product_type,
    collection_list,
    product_type_collection_reference_attribute,
    channel_USD,
):
    # given
    product_type.product_attributes.add(product_type_collection_reference_attribute)

    first_collection = collection_list[0]
    second_collection = collection_list[1]
    third_collection = collection_list[2]

    first_attr_value, second_attr_value, third_attr_value = (
        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=product_type_collection_reference_attribute,
                    name=f"Category {first_collection.pk}",
                    slug=f"collection-{first_collection.pk}",
                    reference_collection=first_collection,
                ),
                AttributeValue(
                    attribute=product_type_collection_reference_attribute,
                    name=f"Category {second_collection.pk}",
                    slug=f"collection-{second_collection.pk}",
                    reference_collection=second_collection,
                ),
                AttributeValue(
                    attribute=product_type_collection_reference_attribute,
                    name=f"Category {third_collection.pk}",
                    slug=f"collection-{third_collection.pk}",
                    reference_collection=third_collection,
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
            product_type_collection_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        second_product_with_all_ids,
        {
            product_type_collection_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        product_with_single_id,
        {product_type_collection_reference_attribute.pk: [first_attr_value]},
    )

    referenced_first_global_id = to_global_id_or_none(first_collection)
    referenced_second_global_id = to_global_id_or_none(second_collection)
    referenced_third_global_id = to_global_id_or_none(third_collection)

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": product_type_collection_reference_attribute.slug,
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
