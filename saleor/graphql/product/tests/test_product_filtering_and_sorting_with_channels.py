import uuid
from decimal import Decimal

import pytest

from ....product.models import (
    Product,
    ProductChannelListing,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ...tests.utils import assert_filter_without_channel, get_graphql_content


@pytest.fixture
def products_for_pagination(category, channel_USD):
    product_type = ProductType.objects.create(name="Apple")
    products = Product.objects.bulk_create(
        [
            Product(
                name="Product1",
                slug="prod1",
                category=category,
                product_type=product_type,
                description="desc1",
            ),
            Product(
                name="ProductProduct1",
                slug="prod_prod1",
                category=category,
                product_type=product_type,
            ),
            Product(
                name="ProductProduct2",
                slug="prod_prod2",
                category=category,
                product_type=product_type,
            ),
            Product(
                name="Product2",
                slug="prod2",
                category=category,
                product_type=product_type,
                description="desc2",
            ),
            Product(
                name="Product3",
                slug="prod3",
                category=category,
                product_type=product_type,
                description="desc3",
            ),
        ]
    )
    ProductChannelListing.objects.bulk_create(
        [
            ProductChannelListing(
                product=products[0],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=Decimal(5),
            ),
            ProductChannelListing(
                product=products[1],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=Decimal(15),
            ),
            ProductChannelListing(
                product=products[2],
                channel=channel_USD,
                is_published=False,
                discounted_price_amount=Decimal(4),
            ),
            ProductChannelListing(
                product=products[3],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=Decimal(7),
            ),
        ]
    )
    variants = ProductVariant.objects.bulk_create(
        [
            ProductVariant(
                product=products[0],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
            ),
            ProductVariant(
                product=products[1],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
            ),
            ProductVariant(
                product=products[2],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
            ),
            ProductVariant(
                product=products[3],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
            ),
            ProductVariant(
                product=products[4],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
            ),
        ]
    )
    ProductVariantChannelListing.objects.bulk_create(
        [
            ProductVariantChannelListing(
                variant=variants[0],
                channel=channel_USD,
                price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[1],
                channel=channel_USD,
                price_amount=Decimal(15),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[2],
                channel=channel_USD,
                price_amount=Decimal(8),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[3],
                channel=channel_USD,
                price_amount=Decimal(7),
                currency=channel_USD.currency_code,
            ),
        ]
    )
    return products


QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING = """
    query ($sortBy: ProductOrder, $filter: ProductFilterInput){
        products (
            first: 10, sortBy: $sortBy, filter: $filter
        ) {
            edges {
                node {
                    name
                    slug
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "sort_by, products_order",
    [
        (
            {"field": "PUBLISHED", "direction": "ASC"},
            ["ProductProduct2", "Product1", "Product2", "ProductProduct1", "Product3"],
        ),
        (
            {"field": "PUBLISHED", "direction": "DESC"},
            ["Product3", "ProductProduct1", "Product2", "Product1", "ProductProduct2"],
        ),
        (
            {"field": "PRICE", "direction": "ASC"},
            ["Product2", "ProductProduct2", "Product1", "ProductProduct1", "Product3"],
        ),
        (
            {"field": "PRICE", "direction": "DESC"},
            ["Product3", "ProductProduct1", "Product1", "ProductProduct2", "Product2"],
        ),
        (
            {"field": "MINIMAL_PRICE", "direction": "ASC"},
            ["ProductProduct2", "Product1", "Product2", "ProductProduct1", "Product3"],
        ),
        (
            {"field": "MINIMAL_PRICE", "direction": "DESC"},
            ["Product3", "ProductProduct1", "Product2", "Product1", "ProductProduct2"],
        ),
    ],
)
def test_products_with_sorting_and_channel(
    sort_by,
    products_order,
    staff_api_client,
    permission_manage_products,
    products_for_pagination,
    channel_USD,
):

    sort_by["channel"] = channel_USD.slug
    variables = {"sortBy": sort_by}
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    for index, product_name in enumerate(products_order):
        assert product_name == products_nodes[index]["node"]["name"]


@pytest.mark.parametrize(
    "filter_by",
    [{"isPublished": True}, {"price": {"lte": 5}}, {"minimalPrice": {"lte": 5}}],
)
def test_products_with_filtering_without_channel(
    filter_by, staff_api_client, permission_manage_products
):
    variables = {"filter": filter_by}
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    assert_filter_without_channel(response)


@pytest.mark.parametrize(
    "filter_by, products_count",
    [
        ({"isPublished": True}, 3),
        ({"isPublished": False}, 1),
        ({"price": {"lte": 8}}, 2),
        ({"price": {"gte": 11}}, 1),
        ({"minimalPrice": {"lte": 4}}, 1),
        ({"minimalPrice": {"gte": 5}}, 3),
    ],
)
def test_products_with_filtering_with_channel(
    filter_by,
    products_count,
    staff_api_client,
    permission_manage_products,
    products_for_pagination,
    channel_USD,
):
    filter_by["channel"] = channel_USD.slug
    variables = {"filter": filter_by}
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    assert len(products_nodes) == products_count
