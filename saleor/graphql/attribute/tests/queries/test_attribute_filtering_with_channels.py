from decimal import Decimal

import graphene
import pytest

from .....attribute.models import Attribute, AttributeProduct, AttributeVariant
from .....product.models import (
    Product,
    ProductChannelListing,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ....channel.filters import LACK_OF_CHANNEL_IN_FILTERING_MSG
from ....tests.utils import assert_graphql_error_with_message, get_graphql_content


@pytest.fixture
def attributes_for_filtering_with_channels(
    collection, category, channel_USD, channel_PLN, other_channel_USD
):
    attributes = Attribute.objects.bulk_create(
        [
            Attribute(
                name="Attr1",
                slug="attr1",
                value_required=True,
                storefront_search_position=4,
            ),
            Attribute(
                name="AttrAttr1",
                slug="attr_attr1",
                value_required=True,
                storefront_search_position=3,
            ),
            Attribute(
                name="AttrAttr2",
                slug="attr_attr2",
                value_required=True,
                storefront_search_position=2,
            ),
            Attribute(
                name="Attr2",
                slug="attr2",
                value_required=False,
                storefront_search_position=5,
            ),
            Attribute(
                name="Attr3",
                slug="attr3",
                value_required=False,
                storefront_search_position=1,
            ),
        ]
    )

    product_type = ProductType.objects.create(name="My Product Type")
    product = Product.objects.create(
        name="Test product",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.bulk_create(
        [
            ProductChannelListing(
                channel=channel_USD,
                product=product,
                visible_in_listings=True,
                currency=channel_USD.currency_code,
                is_published=True,
            ),
            ProductChannelListing(
                channel=channel_PLN,
                product=product,
                visible_in_listings=False,
                currency=channel_PLN.currency_code,
                is_published=True,
            ),
            ProductChannelListing(
                channel=other_channel_USD,
                product=product,
                visible_in_listings=True,
                currency=other_channel_USD.currency_code,
                is_published=False,
            ),
        ]
    )
    variant = ProductVariant.objects.create(product=product)
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        cost_price_amount=Decimal(1),
        price_amount=Decimal(10),
        currency=channel_USD.currency_code,
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        cost_price_amount=Decimal(1),
        price_amount=Decimal(10),
        currency=channel_PLN.currency_code,
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=other_channel_USD,
        cost_price_amount=Decimal(1),
        price_amount=Decimal(10),
        currency=other_channel_USD.currency_code,
    )

    collection.products.add(product)
    AttributeVariant.objects.bulk_create(
        [
            AttributeVariant(
                product_type=product_type, attribute=attributes[1], sort_order=1
            ),
            AttributeVariant(
                product_type=product_type, attribute=attributes[3], sort_order=2
            ),
            AttributeVariant(
                product_type=product_type, attribute=attributes[4], sort_order=3
            ),
        ]
    )
    AttributeProduct.objects.bulk_create(
        [
            AttributeProduct(
                product_type=product_type, attribute=attributes[2], sort_order=1
            ),
            AttributeProduct(
                product_type=product_type, attribute=attributes[0], sort_order=2
            ),
            AttributeProduct(
                product_type=product_type, attribute=attributes[1], sort_order=3
            ),
        ]
    )

    return attributes


QUERY_ATTRIBUTES_FILTERING = """
    query (
        $filter: AttributeFilterInput
    ){
        attributes (
            first: 10, filter: $filter
        ) {
            edges {
                node {
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "tested_field",
    ["inCategory", "inCollection"],
)
def test_attributes_with_filtering_without_channel(
    tested_field,
    staff_api_client,
    permission_manage_products,
    category,
    collection,
):
    # given
    if "Collection" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Collection", collection.pk)
    elif "Category" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Category", category.pk)
    else:
        raise AssertionError(tested_field)
    filter_by = {tested_field: filtered_by_node_id}
    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ATTRIBUTES_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(response, LACK_OF_CHANNEL_IN_FILTERING_MSG)


@pytest.mark.parametrize(
    "tested_field, attribute_count",
    [("inCategory", 5), ("inCollection", 5)],
)
def test_products_with_filtering_with_as_staff_user(
    tested_field,
    attribute_count,
    staff_api_client,
    permission_manage_products,
    attributes_for_filtering_with_channels,
    category,
    collection,
    channel_USD,
):
    # given
    if "Collection" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Collection", collection.pk)
    elif "Category" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Category", category.pk)
    else:
        raise AssertionError(tested_field)
    filter_by = {tested_field: filtered_by_node_id, "channel": channel_USD.slug}

    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ATTRIBUTES_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    attribute_nodes = content["data"]["attributes"]["edges"]
    assert len(attribute_nodes) == attribute_count


@pytest.mark.parametrize(
    "tested_field, attribute_count",
    [("inCategory", 5), ("inCollection", 5)],
)
def test_products_with_filtering_as_anonymous_client(
    tested_field,
    attribute_count,
    api_client,
    attributes_for_filtering_with_channels,
    category,
    collection,
    channel_USD,
):
    # given
    if "Collection" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Collection", collection.pk)
    elif "Category" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Category", category.pk)
    else:
        raise AssertionError(tested_field)
    filter_by = {tested_field: filtered_by_node_id, "channel": channel_USD.slug}

    variables = {"filter": filter_by}

    # when
    response = api_client.post_graphql(QUERY_ATTRIBUTES_FILTERING, variables)

    # then
    content = get_graphql_content(response)
    attribute_nodes = content["data"]["attributes"]["edges"]
    assert len(attribute_nodes) == attribute_count


@pytest.mark.parametrize(
    "tested_field, attribute_count",
    [("inCategory", 5), ("inCollection", 5)],
)
def test_products_with_filtering_with_not_visible_in_listings_as_staff_user(
    tested_field,
    attribute_count,
    staff_api_client,
    permission_manage_products,
    attributes_for_filtering_with_channels,
    category,
    collection,
    channel_PLN,
):
    # given
    if "Collection" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Collection", collection.pk)
    elif "Category" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Category", category.pk)
    else:
        raise AssertionError(tested_field)
    filter_by = {tested_field: filtered_by_node_id, "channel": channel_PLN.slug}

    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ATTRIBUTES_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    attribute_nodes = content["data"]["attributes"]["edges"]
    assert len(attribute_nodes) == attribute_count


@pytest.mark.parametrize(
    "tested_field, attribute_count",
    [
        ("inCategory", 0),
        # Products not visible in listings should be visible in collections
        ("inCollection", 5),
    ],
)
def test_products_with_filtering_with_not_visible_in_listings_as_anonymous_client(
    tested_field,
    attribute_count,
    api_client,
    attributes_for_filtering_with_channels,
    category,
    collection,
    channel_PLN,
):
    # given
    if "Collection" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Collection", collection.pk)
    elif "Category" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Category", category.pk)
    else:
        raise AssertionError(tested_field)
    filter_by = {tested_field: filtered_by_node_id, "channel": channel_PLN.slug}

    variables = {"filter": filter_by}

    # when
    response = api_client.post_graphql(QUERY_ATTRIBUTES_FILTERING, variables)

    # then
    content = get_graphql_content(response)
    attribute_nodes = content["data"]["attributes"]["edges"]
    assert len(attribute_nodes) == attribute_count


@pytest.mark.parametrize(
    "tested_field, attribute_count",
    [("inCategory", 5), ("inCollection", 5)],
)
def test_products_with_filtering_with_not_published_as_staff_user(
    tested_field,
    attribute_count,
    staff_api_client,
    permission_manage_products,
    attributes_for_filtering_with_channels,
    category,
    collection,
    other_channel_USD,
):
    # given
    if "Collection" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Collection", collection.pk)
    elif "Category" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Category", category.pk)
    else:
        raise AssertionError(tested_field)
    filter_by = {tested_field: filtered_by_node_id, "channel": other_channel_USD.slug}

    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ATTRIBUTES_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    attribute_nodes = content["data"]["attributes"]["edges"]
    assert len(attribute_nodes) == attribute_count


@pytest.mark.parametrize(
    "tested_field, attribute_count",
    [("inCategory", 0), ("inCollection", 0)],
)
def test_products_with_filtering_with_not_published_as_anonymous_client(
    tested_field,
    attribute_count,
    api_client,
    attributes_for_filtering_with_channels,
    category,
    collection,
    other_channel_USD,
):
    # given
    if "Collection" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Collection", collection.pk)
    elif "Category" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Category", category.pk)
    else:
        raise AssertionError(tested_field)
    filter_by = {tested_field: filtered_by_node_id, "channel": other_channel_USD.slug}

    variables = {"filter": filter_by}

    # when
    response = api_client.post_graphql(QUERY_ATTRIBUTES_FILTERING, variables)

    # then
    content = get_graphql_content(response)
    attribute_nodes = content["data"]["attributes"]["edges"]
    assert len(attribute_nodes) == attribute_count


@pytest.mark.parametrize(
    "tested_field",
    ["inCategory", "inCollection"],
)
def test_products_with_filtering_not_existing_channel(
    tested_field,
    api_client,
    attributes_for_filtering_with_channels,
    category,
    collection,
):
    # given
    if "Collection" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Collection", collection.pk)
    elif "Category" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Category", category.pk)
    else:
        raise AssertionError(tested_field)
    filter_by = {tested_field: filtered_by_node_id, "channel": "Not-existing"}

    variables = {"filter": filter_by}

    # when
    response = api_client.post_graphql(QUERY_ATTRIBUTES_FILTERING, variables)

    # then
    content = get_graphql_content(response)
    attribute_nodes = content["data"]["attributes"]["edges"]
    assert len(attribute_nodes) == 0
