import datetime
import uuid
from decimal import Decimal

import pytest
import pytz
from freezegun import freeze_time

from ....product import ProductTypeKind
from ....product.models import (
    Product,
    ProductChannelListing,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ....tests.utils import dummy_editorjs
from ...tests.utils import assert_graphql_error_with_message, get_graphql_content


@pytest.fixture
def products_for_sorting_with_channels(category, channel_USD, channel_PLN):
    product_type = ProductType.objects.create(name="Apple", kind=ProductTypeKind.NORMAL)
    products = Product.objects.bulk_create(
        [
            Product(
                name="Product1",
                slug="prod1",
                category=category,
                product_type=product_type,
                description=dummy_editorjs("Test description 1."),
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
                description=dummy_editorjs("Test description 2."),
            ),
            Product(
                name="Product3",
                slug="prod3",
                category=category,
                product_type=product_type,
                description=dummy_editorjs("Test description 3."),
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
                published_at=datetime.datetime(2002, 1, 1, tzinfo=pytz.UTC),
                available_for_purchase_at=None,
            ),
            ProductChannelListing(
                product=products[1],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=Decimal(15),
                published_at=datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC),
                available_for_purchase_at=datetime.datetime(
                    2003, 1, 1, tzinfo=pytz.UTC
                ),
            ),
            ProductChannelListing(
                product=products[2],
                channel=channel_USD,
                is_published=False,
                discounted_price_amount=Decimal(4),
                published_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
                available_for_purchase_at=datetime.datetime(
                    2000, 1, 1, tzinfo=pytz.UTC
                ),
            ),
            ProductChannelListing(
                product=products[3],
                channel=channel_USD,
                is_published=True,
                visible_in_listings=True,
                discounted_price_amount=Decimal(7),
                published_at=datetime.datetime(2001, 1, 1, tzinfo=pytz.UTC),
                available_for_purchase_at=datetime.datetime(
                    2001, 1, 1, tzinfo=pytz.UTC
                ),
            ),
            # Second channel
            ProductChannelListing(
                product=products[0],
                channel=channel_PLN,
                is_published=False,
                discounted_price_amount=Decimal(15),
                published_at=datetime.datetime(2003, 1, 1, tzinfo=pytz.UTC),
                available_for_purchase_at=datetime.datetime(
                    2003, 1, 1, tzinfo=pytz.UTC
                ),
            ),
            ProductChannelListing(
                product=products[1],
                channel=channel_PLN,
                is_published=True,
                discounted_price_amount=Decimal(4),
                published_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
                available_for_purchase_at=datetime.datetime(
                    2002, 1, 1, tzinfo=pytz.UTC
                ),
            ),
            ProductChannelListing(
                product=products[2],
                channel=channel_PLN,
                is_published=True,
                discounted_price_amount=Decimal(5),
                published_at=datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC),
                available_for_purchase_at=None,
            ),
            ProductChannelListing(
                product=products[4],
                channel=channel_PLN,
                is_published=True,
                visible_in_listings=True,
                discounted_price_amount=Decimal(7),
                published_at=datetime.datetime(1998, 1, 1, tzinfo=pytz.UTC),
                available_for_purchase_at=datetime.datetime(
                    2000, 1, 1, tzinfo=pytz.UTC
                ),
            ),
        ]
    )
    variants = ProductVariant.objects.bulk_create(
        [
            ProductVariant(
                product=products[0],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
                name="XS",
            ),
            ProductVariant(
                product=products[1],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
                name="S",
            ),
            ProductVariant(
                product=products[2],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
                name="M",
            ),
            ProductVariant(
                product=products[3],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
                name="L",
            ),
            ProductVariant(
                product=products[4],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
                name="XL",
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
            # Second channel
            ProductVariantChannelListing(
                variant=variants[0],
                channel=channel_PLN,
                price_amount=Decimal(15),
                currency=channel_PLN.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[1],
                channel=channel_PLN,
                price_amount=Decimal(8),
                currency=channel_PLN.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[2],
                channel=channel_PLN,
                price_amount=Decimal(10),
                currency=channel_PLN.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[4],
                channel=channel_PLN,
                price_amount=Decimal(7),
                currency=channel_PLN.currency_code,
            ),
        ]
    )

    products[3].save()
    products[4].save()
    products[0].save()
    products[2].save()
    products[1].save()

    variants[2].save()
    variants[0].save()
    variants[4].save()
    variants[1].save()
    variants[3].save()

    return products


QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING = """
    query ($sortBy: ProductOrder, $filter: ProductFilterInput, $channel: String){
        products (
            first: 10, sortBy: $sortBy, filter: $filter, channel: $channel
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
    "sort_by",
    [
        {"field": "PUBLISHED", "direction": "ASC"},
        {"field": "PRICE", "direction": "DESC"},
        {"field": "MINIMAL_PRICE", "direction": "DESC"},
        {"field": "PUBLISHED_AT", "direction": "DESC"},
    ],
)
def test_products_with_sorting_and_without_channel(
    sort_by,
    staff_api_client,
    permission_manage_products,
):
    # given
    variables = {"sortBy": sort_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(response, "A default channel does not exist.")


@pytest.mark.parametrize(
    ("sort_by", "products_order"),
    [
        (
            {"field": "PUBLISHED", "direction": "ASC"},
            ["ProductProduct2", "Product1", "Product2", "ProductProduct1"],
        ),
        (
            {"field": "PUBLISHED", "direction": "DESC"},
            ["ProductProduct1", "Product2", "Product1", "ProductProduct2"],
        ),
        (
            {"field": "PRICE", "direction": "ASC"},
            ["Product2", "ProductProduct2", "Product1", "ProductProduct1"],
        ),
        (
            {"field": "PRICE", "direction": "DESC"},
            ["ProductProduct1", "Product1", "ProductProduct2", "Product2"],
        ),
        (
            {"field": "MINIMAL_PRICE", "direction": "ASC"},
            ["ProductProduct2", "Product1", "Product2", "ProductProduct1"],
        ),
        (
            {"field": "MINIMAL_PRICE", "direction": "DESC"},
            ["ProductProduct1", "Product2", "Product1", "ProductProduct2"],
        ),
        (
            {"field": "PUBLICATION_DATE", "direction": "ASC"},
            ["ProductProduct2", "ProductProduct1", "Product2", "Product1"],
        ),
        (
            {"field": "PUBLICATION_DATE", "direction": "DESC"},
            ["Product1", "Product2", "ProductProduct1", "ProductProduct2"],
        ),
        (
            {"field": "PUBLISHED_AT", "direction": "ASC"},
            ["ProductProduct2", "ProductProduct1", "Product2", "Product1"],
        ),
        (
            {"field": "PUBLISHED_AT", "direction": "DESC"},
            ["Product1", "Product2", "ProductProduct1", "ProductProduct2"],
        ),
        (
            {"field": "LAST_MODIFIED_AT", "direction": "ASC"},
            ["Product2", "Product1", "ProductProduct2", "ProductProduct1"],
        ),
        (
            {"field": "LAST_MODIFIED_AT", "direction": "DESC"},
            ["ProductProduct1", "ProductProduct2", "Product1", "Product2"],
        ),
    ],
)
def test_products_with_sorting_and_channel_USD(
    sort_by,
    products_order,
    staff_api_client,
    permission_manage_products,
    products_for_sorting_with_channels,
    channel_USD,
):
    # given
    variables = {"sortBy": sort_by, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    for index, product_name in enumerate(products_order):
        assert product_name == products_nodes[index]["node"]["name"]


@pytest.mark.parametrize(
    ("sort_by", "products_order"),
    [
        (
            {"field": "PUBLISHED", "direction": "ASC"},
            ["Product1", "Product3", "ProductProduct1", "ProductProduct2"],
        ),
        (
            {"field": "PUBLISHED", "direction": "DESC"},
            ["ProductProduct2", "ProductProduct1", "Product3", "Product1"],
        ),
        (
            {"field": "PRICE", "direction": "ASC"},
            ["Product3", "ProductProduct1", "ProductProduct2", "Product1"],
        ),
        (
            {"field": "PRICE", "direction": "DESC"},
            ["Product1", "ProductProduct2", "ProductProduct1", "Product3"],
        ),
        (
            {"field": "MINIMAL_PRICE", "direction": "ASC"},
            ["ProductProduct1", "ProductProduct2", "Product3", "Product1"],
        ),
        (
            {"field": "MINIMAL_PRICE", "direction": "DESC"},
            ["Product1", "Product3", "ProductProduct2", "ProductProduct1"],
        ),
        (
            {"field": "PUBLICATION_DATE", "direction": "ASC"},
            ["Product3", "ProductProduct1", "ProductProduct2", "Product1"],
        ),
        (
            {"field": "PUBLICATION_DATE", "direction": "DESC"},
            ["Product1", "ProductProduct2", "ProductProduct1", "Product3"],
        ),
        (
            {"field": "PUBLISHED_AT", "direction": "ASC"},
            ["Product3", "ProductProduct1", "ProductProduct2", "Product1"],
        ),
        (
            {"field": "PUBLISHED_AT", "direction": "DESC"},
            ["Product1", "ProductProduct2", "ProductProduct1", "Product3"],
        ),
        (
            {"field": "LAST_MODIFIED_AT", "direction": "ASC"},
            ["Product3", "Product1", "ProductProduct2", "ProductProduct1"],
        ),
        (
            {"field": "LAST_MODIFIED_AT", "direction": "DESC"},
            ["ProductProduct1", "ProductProduct2", "Product1", "Product3"],
        ),
    ],
)
def test_products_with_sorting_and_channel_PLN(
    sort_by,
    products_order,
    staff_api_client,
    permission_manage_products,
    products_for_sorting_with_channels,
    channel_PLN,
):
    # given
    variables = {"sortBy": sort_by, "channel": channel_PLN.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    for index, product_name in enumerate(products_order):
        assert product_name == products_nodes[index]["node"]["name"]


@pytest.mark.parametrize(
    "sort_by",
    [
        {"field": "PUBLISHED", "direction": "ASC"},
        {"field": "PRICE", "direction": "ASC"},
        {"field": "MINIMAL_PRICE", "direction": "ASC"},
    ],
)
def test_products_with_sorting_and_not_existing_channel_asc(
    sort_by,
    staff_api_client,
    permission_manage_products,
    products_for_sorting_with_channels,
    channel_USD,
):
    # given
    variables = {"sortBy": sort_by, "channel": "Not-existing"}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["products"]["edges"]


@pytest.mark.parametrize(
    "sort_by",
    [
        {"field": "PUBLISHED", "direction": "DESC"},
        {"field": "PRICE", "direction": "DESC"},
        {"field": "MINIMAL_PRICE", "direction": "DESC"},
    ],
)
def test_products_with_sorting_and_not_existing_channel_desc(
    sort_by,
    staff_api_client,
    permission_manage_products,
    products_for_sorting_with_channels,
    channel_USD,
):
    # given
    variables = {"sortBy": sort_by, "channel": "Not-existing"}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["products"]["edges"]


@pytest.mark.parametrize(
    "filter_by",
    [{"isPublished": True}, {"price": {"lte": 5}}, {"minimalPrice": {"lte": 5}}],
)
def test_products_with_filtering_without_channel(
    filter_by, staff_api_client, permission_manage_products
):
    # given
    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(response, "A default channel does not exist.")


@pytest.mark.parametrize(
    ("filter_by", "products_count"),
    [
        ({"isPublished": True}, 3),
        ({"isPublished": False}, 1),
        ({"isAvailable": True}, 3),
        ({"isAvailable": False}, 1),
        ({"publishedFrom": "2001-01-01T00:00:00+00:00"}, 3),
        ({"availableFrom": "2001-01-01T00:00:00+00:00"}, 2),
        ({"isVisibleInListing": True}, 1),
        ({"isVisibleInListing": False}, 3),
        ({"price": {"lte": 8}}, 2),
        ({"price": {"gte": 11}}, 1),
        ({"minimalPrice": {"lte": 4}}, 1),
        ({"minimalPrice": {"gte": 5}}, 3),
        ({"slugs": ["prod1"]}, 1),
        ({"slugs": ["prod_prod1", "prod_prod2"]}, 2),
        ({"slugs": []}, 4),
    ],
)
def test_products_with_filtering_with_channel_USD(
    filter_by,
    products_count,
    staff_api_client,
    permission_manage_products,
    products_for_sorting_with_channels,
    channel_USD,
):
    # given
    variables = {"filter": filter_by, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    assert len(products_nodes) == products_count


@pytest.mark.parametrize(
    ("filter_by", "products_count"),
    [
        ({"isPublished": True}, 3),
        ({"isPublished": False}, 1),
        ({"isAvailable": True}, 3),
        ({"isAvailable": False}, 1),
        ({"publishedFrom": "2001-01-01T00:00:00+00:00"}, 3),
        ({"availableFrom": "2001-01-01T00:00:00+00:00"}, 1),
        ({"isVisibleInListing": True}, 1),
        ({"isVisibleInListing": False}, 3),
        ({"price": {"lte": 8}}, 2),
        ({"price": {"gte": 11}}, 1),
        ({"minimalPrice": {"lte": 4}}, 1),
        ({"minimalPrice": {"gte": 5}}, 3),
    ],
)
def test_products_with_filtering_with_channel_PLN(
    filter_by,
    products_count,
    staff_api_client,
    permission_manage_products,
    products_for_sorting_with_channels,
    channel_PLN,
):
    # given
    variables = {"filter": filter_by, "channel": channel_PLN.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    assert len(products_nodes) == products_count


@pytest.mark.parametrize(
    "filter_by",
    [
        {"isPublished": True},
        {"isPublished": False},
        {"isAvailable": True},
        {"isAvailable": False},
        {"publishedFrom": "2001-01-01T00:00:00+00:00"},
        {"availableFrom": "2001-01-01T00:00:00+00:00"},
        {"isVisibleInListing": True},
        {"isVisibleInListing": False},
        {"price": {"lte": 8}},
        {"price": {"gte": 11}},
        {"minimalPrice": {"lte": 4}},
        {"minimalPrice": {"gte": 5}},
        {"slugs": ["prod1"]},
    ],
)
def test_products_with_filtering_and_not_existing_channel(
    filter_by,
    staff_api_client,
    permission_manage_products,
    products_for_sorting_with_channels,
    channel_USD,
):
    # given
    variables = {"filter": filter_by, "channel": "Not-existing"}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    assert len(products_nodes) == 0


def test_published_products_without_sku_as_staff(
    staff_api_client,
    permission_manage_products,
    products_for_sorting_with_channels,
    channel_USD,
):
    # given
    ProductVariant.objects.update(sku=None)
    variables = {"filter": {"isPublished": True}, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    assert len(products_nodes) == 3


@pytest.mark.parametrize(
    ("products_filter", "count"),
    [
        ({"updatedAt": {"gte": "2012-01-14T10:59:00+00:00"}}, 2),
        ({"updatedAt": {"lte": "2012-01-14T12:00:05+00:00"}}, 2),
        ({"updatedAt": {"gte": "2012-01-14T11:59:00+00:00"}}, 1),
        ({"updatedAt": {"lte": "2012-01-14T11:05:00+00:00"}}, 1),
        ({"updatedAt": {"gte": "2012-01-14T12:01:00+00:00"}}, 0),
        ({"updatedAt": {"lte": "2012-01-14T10:59:00+00:00"}}, 0),
        (
            {
                "updatedAt": {
                    "lte": "2012-01-14T12:01:00+00:00",
                    "gte": "2012-01-14T11:59:00+00:00",
                },
            },
            1,
        ),
    ],
)
def test_product_query_with_filter_updated_at(
    products_filter,
    count,
    product_type,
    category,
    staff_api_client,
    permission_manage_products,
):
    with freeze_time("2012-01-14 11:00:00"):
        Product.objects.create(
            name="Product1",
            slug="prod1",
            category=category,
            product_type=product_type,
        )

    with freeze_time("2012-01-14 12:00:00"):
        Product.objects.create(
            name="Product2",
            slug="prod2",
            category=category,
            product_type=product_type,
        )

    variables = {"filter": products_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING, variables
    )
    content = get_graphql_content(response)
    variants = content["data"]["products"]["edges"]

    assert len(variants) == count


GET_SORTED_VARIANTS_QUERY = """
query Variants($sortBy: ProductVariantSortingInput, $channel: String) {
    productVariants(first: 10, sortBy: $sortBy, channel: $channel) {
      edges {
        node {
          name
        }
      }
    }
}
"""


@pytest.mark.parametrize(
    ("sort_by", "variants_order"),
    [
        (
            {"field": "LAST_MODIFIED_AT", "direction": "ASC"},
            ["M", "XS", "S", "L"],
        ),
        (
            {"field": "LAST_MODIFIED_AT", "direction": "DESC"},
            ["L", "S", "XS", "M"],
        ),
    ],
)
def test_products_variants_with_sorting_and_channel_USD(
    sort_by,
    variants_order,
    staff_api_client,
    permission_manage_products,
    products_for_sorting_with_channels,
    channel_USD,
):
    # given
    variables = {"sortBy": sort_by, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        GET_SORTED_VARIANTS_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["productVariants"]["edges"]
    for index, product_name in enumerate(variants_order):
        assert product_name == products_nodes[index]["node"]["name"]


@pytest.mark.parametrize(
    ("sort_by", "variants_order"),
    [
        (
            {"field": "LAST_MODIFIED_AT", "direction": "ASC"},
            ["M", "XS", "XL", "S"],
        ),
        (
            {"field": "LAST_MODIFIED_AT", "direction": "DESC"},
            ["S", "XL", "XS", "M"],
        ),
    ],
)
def test_products_variants_with_sorting_and_channel_PLN(
    sort_by,
    variants_order,
    staff_api_client,
    permission_manage_products,
    products_for_sorting_with_channels,
    channel_PLN,
):
    # given
    variables = {"sortBy": sort_by, "channel": channel_PLN.slug}

    # when
    response = staff_api_client.post_graphql(
        GET_SORTED_VARIANTS_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["productVariants"]["edges"]
    for index, product_name in enumerate(variants_order):
        assert product_name == products_nodes[index]["node"]["name"]
