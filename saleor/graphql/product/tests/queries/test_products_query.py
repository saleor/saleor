from datetime import datetime
from decimal import Decimal

import graphene
from django.utils.dateparse import parse_datetime

from .....core.postgres import FlatConcatSearchVector
from .....product.models import (
    Product,
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
)
from .....product.search import prepare_product_search_vector_value
from ....tests.utils import get_graphql_content

QUERY_FETCH_ALL_PRODUCTS = """
    query ($channel:String){
        products(first: 10, channel: $channel) {
            totalCount
            edges {
                node {
                    id
                    name
                    variants {
                        id
                    }
                }
            }
        }
    }
"""


def test_fetch_all_products_available_as_staff_user(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_product_variants_available_as_staff_user_with_channel(
    staff_api_client, permission_manage_products, product_variant_list, channel_USD
):
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    num_products = Product.objects.count()
    num_variants = ProductVariant.objects.count()
    assert num_variants > 1

    content = get_graphql_content(response)
    products = content["data"]["products"]
    variants = products["edges"][0]["node"]["variants"]

    assert products["totalCount"] == num_products
    assert len(products["edges"]) == num_products
    assert len(variants) == num_variants - 1


def test_fetch_all_product_variants_available_as_staff_user_without_channel(
    staff_api_client, permission_manage_products, product_variant_list, channel_USD
):
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    num_products = Product.objects.count()
    num_variants = ProductVariant.objects.count()
    assert num_variants > 1

    content = get_graphql_content(response)
    products = content["data"]["products"]
    variants = products["edges"][0]["node"]["variants"]

    assert products["totalCount"] == num_products
    assert len(products["edges"]) == num_products
    assert len(variants) == num_variants


def test_fetch_all_products_not_available_as_staff_user(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_not_existing_in_channel_as_staff_user(
    staff_api_client, permission_manage_products, channel_USD, product_list
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(
        product=product_list[0], channel=channel_USD
    ).delete()

    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # if channel slug is provided we return all products related to this channel
    num_products = Product.objects.count() - 1

    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_as_staff_user_without_channel_slug(
    staff_api_client, permission_manage_products, product_list, channel_USD
):
    ProductChannelListing.objects.filter(
        product=product_list[0], channel=channel_USD
    ).delete()

    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_available_as_app(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    response = app_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_not_available_as_app(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = app_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_not_existing_in_channel_as_app(
    app_api_client, permission_manage_products, product_list, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(
        product=product_list[0], channel=channel_USD
    ).delete()

    response = app_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    # if channel slug is provided we return all products related to this channel

    num_products = Product.objects.count() - 1
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_as_app_without_channel_slug(
    app_api_client, permission_manage_products, product_list, channel_USD
):
    ProductChannelListing.objects.filter(
        product=product_list[0], channel=channel_USD
    ).delete()

    response = app_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_available_as_customer(
    user_api_client, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    response = user_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_not_available_as_customer(
    user_api_client, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = user_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
    )
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == 0
    assert not content["data"]["products"]["edges"]


def test_fetch_all_products_not_existing_in_channel_as_customer(
    user_api_client, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = user_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == 0
    assert not content["data"]["products"]["edges"]


def test_fetch_all_products_available_as_anonymous(api_client, product, channel_USD):
    variables = {"channel": channel_USD.slug}
    response = api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_not_available_as_anonymous(
    api_client, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
    )
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == 0
    assert not content["data"]["products"]["edges"]


def test_fetch_all_products_not_existing_in_channel_as_anonymous(
    api_client, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == 0
    assert not content["data"]["products"]["edges"]


def test_fetch_all_products_visible_in_listings(
    user_api_client, product_list, permission_manage_products, channel_USD
):
    # given
    product_list[0].channel_listings.update(visible_in_listings=False)

    product_count = Product.objects.count()
    variables = {"channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["products"]["edges"]
    assert len(product_data) == product_count - 1
    products_ids = [product["node"]["id"] for product in product_data]
    assert graphene.Node.to_global_id("Product", product_list[0].pk) not in products_ids


def test_fetch_all_products_visible_in_listings_by_staff_with_perm(
    staff_api_client, product_list, permission_manage_products, channel_USD
):
    # given
    product_list[0].channel_listings.update(visible_in_listings=False)

    product_count = Product.objects.count()
    variables = {"channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["products"]["edges"]
    assert len(product_data) == product_count


def test_fetch_all_products_visible_in_listings_by_staff_without_manage_products(
    staff_api_client, product_list, channel_USD
):
    # given
    product_list[0].channel_listings.update(visible_in_listings=False)

    product_count = Product.objects.count()
    variables = {"channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["products"]["edges"]
    assert len(product_data) == product_count - 1  # invisible doesn't count


def test_fetch_all_products_visible_in_listings_by_app_with_perm(
    app_api_client, product_list, permission_manage_products, channel_USD
):
    # given
    product_list[0].channel_listings.update(visible_in_listings=False)

    product_count = Product.objects.count()
    variables = {"channel": channel_USD.slug}

    # when
    response = app_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["products"]["edges"]
    assert len(product_data) == product_count


def test_fetch_all_products_visible_in_listings_by_app_without_manage_products(
    app_api_client, product_list, channel_USD
):
    # given
    product_list[0].channel_listings.update(visible_in_listings=False)

    product_count = Product.objects.count()
    variables = {"channel": channel_USD.slug}

    # when
    response = app_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["products"]["edges"]
    assert len(product_data) == product_count - 1  # invisible doesn't count


def test_filter_products_by_wrong_attributes(user_api_client, product, channel_USD):
    product_attr = product.product_type.product_attributes.get(slug="color")
    attr_value = product.product_type.variant_attributes.get(slug="size").values.first()
    query = """
    query ($channel: String, $filter: ProductFilterInput){
        products(
            filter: $filter,
            first: 1,
            channel: $channel
        ) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """

    variables = {
        "channel": channel_USD.slug,
        "filter": {
            "attributes": [{"slug": product_attr.slug, "values": [attr_value.slug]}]
        },
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert products == []


def test_filter_products_with_unavailable_variants_attributes_as_user(
    user_api_client, product_list, channel_USD
):
    product_attr = product_list[0].product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    query = """
    query Products($attributesFilter: [AttributeInput!], $channel: String) {
        products(
            first: 5,
            filter: {attributes: $attributesFilter},
            channel: $channel
        ) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    second_product_id = graphene.Node.to_global_id("Product", product_list[1].id)
    third_product_id = graphene.Node.to_global_id("Product", product_list[2].id)
    variables = {
        "channel": channel_USD.slug,
        "attributesFilter": [
            {"slug": f"{product_attr.slug}", "values": [f"{attr_value.slug}"]}
        ],
    }
    product_list[0].variants.first().channel_listings.filter(
        channel=channel_USD
    ).update(price_amount=None)

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 2
    assert products[0]["node"]["id"] == second_product_id
    assert products[1]["node"]["id"] == third_product_id


def test_filter_products_with_unavailable_variants_attributes_as_staff(
    staff_api_client, product_list, channel_USD, permission_manage_products
):
    product_attr = product_list[0].product_type.product_attributes.first()
    attr_value = product_attr.values.first()
    staff_api_client.user.user_permissions.add(permission_manage_products)

    query = """
    query Products($attributesFilter: [AttributeInput!], $channel: String) {
        products(
            first: 5,
            filter: {attributes: $attributesFilter},
            channel: $channel
        ) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """

    variables = {
        "channel": channel_USD.slug,
        "attributesFilter": [
            {"slug": f"{product_attr.slug}", "values": [f"{attr_value.slug}"]}
        ],
    }
    product_list[0].variants.first().channel_listings.filter(
        channel=channel_USD
    ).update(price_amount=None)

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 3


SORT_PRODUCTS_QUERY = """
    query ($channel:String) {
        products (
            sortBy: %(sort_by_product_order)s, first: 3, channel: $channel
        ) {
            edges {
                node {
                    name
                    productType{
                        name
                    }
                    pricing {
                        priceRangeUndiscounted {
                            start {
                                gross {
                                    amount
                                }
                            }
                        }
                        priceRange {
                            start {
                                gross {
                                    amount
                                }
                            }
                        }
                    }
                    updatedAt
                }
            }
        }
    }
"""


def test_sort_products(user_api_client, product, channel_USD):
    product.updated_at = datetime.utcnow()
    product.save()

    product.pk = None
    product.slug = "second-product"
    product.updated_at = datetime.utcnow()
    product.save()
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    variant = ProductVariant.objects.create(product=product, sku="1234")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(20),
        cost_price_amount=Decimal(2),
        currency=channel_USD.currency_code,
    )
    product.pk = None
    product.slug = "third-product"
    product.updated_at = datetime.utcnow()
    product.save()
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    variant_second = ProductVariant.objects.create(product=product, sku="12345")
    ProductVariantChannelListing.objects.create(
        variant=variant_second,
        channel=channel_USD,
        currency=channel_USD.currency_code,
    )
    variables = {"channel": channel_USD.slug}
    query = SORT_PRODUCTS_QUERY

    # Test sorting by PRICE, ascending
    sort_by = "{field: PRICE, direction: ASC}"
    asc_price_query = query % {"sort_by_product_order": sort_by}
    response = user_api_client.post_graphql(asc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    assert len(edges) == 2
    price1 = edges[0]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    price2 = edges[1]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    assert price1 < price2

    # Test sorting by PRICE, descending
    sort_by = "{field: PRICE, direction:DESC}"
    desc_price_query = query % {"sort_by_product_order": sort_by}
    response = user_api_client.post_graphql(desc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    price2 = edges[1]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    assert price1 > price2

    # Test sorting by MINIMAL_PRICE, ascending
    sort_by = "{field: MINIMAL_PRICE, direction:ASC}"
    asc_price_query = query % {"sort_by_product_order": sort_by}
    response = user_api_client.post_graphql(asc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    price2 = edges[1]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    assert price1 < price2

    # Test sorting by MINIMAL_PRICE, descending
    sort_by = "{field: MINIMAL_PRICE, direction:DESC}"
    desc_price_query = query % {"sort_by_product_order": sort_by}
    response = user_api_client.post_graphql(desc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    price2 = edges[1]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    assert price1 > price2

    # Test sorting by DATE, ascending
    asc_date_query = query % {"sort_by_product_order": "{field: DATE, direction:ASC}"}
    response = user_api_client.post_graphql(asc_date_query, variables)
    content = get_graphql_content(response)
    date_0 = content["data"]["products"]["edges"][0]["node"]["updatedAt"]
    date_1 = content["data"]["products"]["edges"][1]["node"]["updatedAt"]
    assert parse_datetime(date_0) < parse_datetime(date_1)

    # Test sorting by DATE, descending
    desc_date_query = query % {"sort_by_product_order": "{field: DATE, direction:DESC}"}
    response = user_api_client.post_graphql(desc_date_query, variables)
    content = get_graphql_content(response)
    date_0 = content["data"]["products"]["edges"][0]["node"]["updatedAt"]
    date_1 = content["data"]["products"]["edges"][1]["node"]["updatedAt"]
    assert parse_datetime(date_0) > parse_datetime(date_1)


def test_sort_products_by_price_as_staff(
    staff_api_client, product, channel_USD, permission_manage_products
):
    product.updated_at = datetime.utcnow()
    product.save()
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product.pk = None
    product.slug = "second-product"
    product.updated_at = datetime.utcnow()
    product.save()
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    variant = ProductVariant.objects.create(product=product, sku="1234")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(20),
        cost_price_amount=Decimal(2),
        currency=channel_USD.currency_code,
    )
    product.pk = None
    product.slug = "third-product"
    product.updated_at = datetime.utcnow()
    product.save()
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    variant_second = ProductVariant.objects.create(product=product, sku="12345")
    ProductVariantChannelListing.objects.create(
        variant=variant_second,
        channel=channel_USD,
        currency=channel_USD.currency_code,
    )
    variables = {"channel": channel_USD.slug}
    query = SORT_PRODUCTS_QUERY

    # Test sorting by PRICE, ascending
    sort_by = "{field: PRICE, direction: ASC}"
    asc_price_query = query % {"sort_by_product_order": sort_by}
    response = staff_api_client.post_graphql(asc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    assert len(edges) == 3
    price1 = edges[0]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    price2 = edges[1]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    assert edges[2]["node"]["pricing"] is None
    assert price1 < price2

    # Test sorting by PRICE, descending
    sort_by = "{field: PRICE, direction:DESC}"
    desc_price_query = query % {"sort_by_product_order": sort_by}
    response = staff_api_client.post_graphql(desc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[1]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    price2 = edges[2]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    assert edges[0]["node"]["pricing"] is None
    assert price1 > price2


def test_sort_products_product_type_name(
    user_api_client, product, product_with_default_variant, channel_USD
):
    variables = {"channel": channel_USD.slug}

    # Test sorting by TYPE, ascending
    asc_published_query = SORT_PRODUCTS_QUERY % {
        "sort_by_product_order": "{field: TYPE, direction:ASC}"
    }
    response = user_api_client.post_graphql(asc_published_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    product_type_name_0 = edges[0]["node"]["productType"]["name"]
    product_type_name_1 = edges[1]["node"]["productType"]["name"]
    assert product_type_name_0 < product_type_name_1

    # Test sorting by PUBLISHED, descending
    desc_published_query = SORT_PRODUCTS_QUERY % {
        "sort_by_product_order": "{field: TYPE, direction:DESC}"
    }
    response = user_api_client.post_graphql(desc_published_query, variables)
    content = get_graphql_content(response)
    product_type_name_0 = edges[0]["node"]["productType"]["name"]
    product_type_name_1 = edges[1]["node"]["productType"]["name"]
    assert product_type_name_0 < product_type_name_1


SEARCH_PRODUCTS_QUERY = """
    query Products(
        $filters: ProductFilterInput,
        $sortBy: ProductOrder,
        $channel: String,
        $after: String,
    ) {
        products(
            first: 5,
            filter: $filters,
            sortBy: $sortBy,
            channel: $channel,
            after: $after,
        ) {
            edges {
                node {
                    id
                    name
                }
                cursor
            }
        }
    }
"""


def test_search_product_by_description(user_api_client, product_list, channel_USD):

    variables = {"filters": {"search": "big"}, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)
    assert len(content["data"]["products"]["edges"]) == 2

    variables = {"filters": {"search": "small"}, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)

    assert len(content["data"]["products"]["edges"]) == 1


def test_search_product_by_description_and_name(
    user_api_client, product_list, product, channel_USD, category, product_type
):
    product.description_plaintext = "new big new product"

    product_2 = product_list[1]
    product_2.name = "new product"
    product_1 = product_list[0]
    product_1.description_plaintext = "some new product"
    product_3 = product_list[2]
    product_3.description_plaintext = "desc without searched word"

    product_list.append(product)
    for prod in product_list:
        prod.search_vector = FlatConcatSearchVector(
            *prepare_product_search_vector_value(prod)
        )

    Product.objects.bulk_update(
        product_list,
        ["search_document", "search_vector", "name", "description_plaintext"],
    )

    variables = {
        "filters": {
            "search": "new",
        },
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["products"]["edges"]

    assert len(data) == 3
    assert {node["node"]["name"] for node in data} == {
        product.name,
        product_1.name,
        product_2.name,
    }


def test_sort_product_by_rank_without_search(
    user_api_client, product_list, channel_USD
):
    variables = {
        "sortBy": {"field": "RANK", "direction": "DESC"},
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert (
        content["errors"][0]["message"]
        == "Sorting by RANK is available only when using a search filter."
    )


def test_search_product_by_description_and_name_without_sort_by(
    user_api_client, product_list, product, channel_USD
):
    product.description_plaintext = "new big new product"

    product_2 = product_list[1]
    product_2.name = "new product"
    product_1 = product_list[0]
    product_1.description_plaintext = "some new product"

    product_list.append(product)
    for prod in product_list:
        prod.search_vector = FlatConcatSearchVector(
            *prepare_product_search_vector_value(prod)
        )

    Product.objects.bulk_update(
        product_list,
        ["search_vector", "name", "description_plaintext"],
    )

    variables = {
        "filters": {
            "search": "new",
        },
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["products"]["edges"]

    assert len(data) == 3
    assert {node["node"]["name"] for node in data} == {
        product.name,
        product_1.name,
        product_2.name,
    }


def test_search_product_by_description_and_name_and_use_cursor(
    user_api_client, product_list, product, channel_USD, category, product_type
):
    product.description_plaintext = "new big new product"

    product_2 = product_list[1]
    product_2.name = "new product"
    product_1 = product_list[0]
    product_1.description_plaintext = "some new product"

    product_list.append(product)
    for prod in product_list:
        prod.search_vector = FlatConcatSearchVector(
            *prepare_product_search_vector_value(prod)
        )

    Product.objects.bulk_update(
        product_list,
        ["search_vector", "name", "description_plaintext"],
    )

    variables = {
        "filters": {
            "search": "new",
        },
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)
    cursor = content["data"]["products"]["edges"][0]["cursor"]

    variables = {
        "filters": {
            "search": "new",
        },
        "after": cursor,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["products"]["edges"]

    assert len(data) == 2


def test_hidden_product_access_with_proper_permissions(
    staff_api_client,
    product_list,
    channel_USD,
    permission_manage_products,
):
    hidden_product = product_list[0]
    hidden_product.channel_listings.all().update(is_published=False)

    variables = {
        "channel": channel_USD.slug,
    }

    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    total_count = content["data"]["products"]["totalCount"]
    assert total_count == 3


def test_hidden_product_access_with_permission_manage_orders(
    staff_api_client,
    product_list,
    channel_USD,
    permission_manage_orders,
):
    hidden_product = product_list[0]
    hidden_product.channel_listings.all().update(is_published=False)

    variables = {
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables=variables,
        permissions=(permission_manage_orders,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    total_count = content["data"]["products"]["totalCount"]
    assert total_count == 3


def test_hidden_product_access_with_permission_manage_discounts(
    staff_api_client,
    product_list,
    channel_USD,
    permission_manage_discounts,
):
    hidden_product = product_list[0]
    hidden_product.channel_listings.all().update(is_published=False)

    variables = {
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables=variables,
        permissions=(permission_manage_discounts,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    total_count = content["data"]["products"]["totalCount"]
    assert total_count == 3


def test_hidden_product_access_with_permission_manage_channels(
    staff_api_client,
    product_list,
    channel_USD,
    permission_manage_channels,
):
    hidden_product = product_list[0]
    hidden_product.channel_listings.all().update(is_published=False)

    variables = {
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables=variables,
        permissions=(permission_manage_channels,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    total_count = content["data"]["products"]["totalCount"]
    assert total_count == 2


def test_product_filter_by_attribute_values(
    user_api_client,
    permission_manage_products,
    color_attribute,
    pink_attribute_value,
    product_with_variant_with_two_attributes,
    channel_USD,
):
    query = """
    query Products($filters: ProductFilterInput, $channel: String) {
      products(first: 5, filter: $filters, channel: $channel) {
        edges {
        node {
          id
          name
          attributes {
            attribute {
              name
              slug
            }
            values {
              name
              slug
            }
          }
        }
        }
      }
    }
    """
    variables = {
        "attributes": [
            {"slug": color_attribute.slug, "values": [pink_attribute_value.slug]}
        ],
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["products"]["edges"] == [
        {
            "node": {
                "attributes": [],
                "name": product_with_variant_with_two_attributes.name,
            }
        }
    ]


def test_products_with_variants_query_as_app(
    app_api_client,
    product_with_multiple_values_attributes,
    permission_manage_products,
):
    query = """
        query {
          products(first:5) {
            edges{
              node{
                id
                name
                attributes {
                    attribute {
                        id
                    }
                }
              }
            }
          }
        }
    """
    product = product_with_multiple_values_attributes
    attribute = product.attributes.first().attribute
    attribute.visible_in_storefront = False
    attribute.save()
    second_product = product
    second_product.id = None
    second_product.slug = "second-product"
    second_product.save()
    product.save()

    app_api_client.app.permissions.add(permission_manage_products)
    response = app_api_client.post_graphql(query)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    for response_product in products:
        attrs = response_product["node"]["attributes"]
        assert len(attrs) == 1
        assert attrs[0]["attribute"]["id"] == attribute_id
