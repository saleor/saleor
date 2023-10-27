import graphene

from .....product.models import Product, ProductVariant
from ....tests.utils import get_graphql_content, get_graphql_content_from_response


def _fetch_all_variants(client, variables={}, permissions=None):
    query = """
        query fetchAllVariants($channel: String) {
            productVariants(first: 10, channel: $channel) {
                totalCount
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    response = client.post_graphql(
        query, variables, permissions=permissions, check_no_permissions=False
    )
    content = get_graphql_content(response)
    return content["data"]["productVariants"]


def test_fetch_all_variants_staff_user(
    staff_api_client, unavailable_product_with_variant, permission_manage_products
):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_all_variants(
        staff_api_client, permissions=[permission_manage_products]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["id"] == variant_id


def test_fetch_all_variants_staff_user_with_channel(
    staff_api_client,
    product_list_with_variants_many_channel,
    permission_manage_products,
    channel_PLN,
):
    variables = {"channel": channel_PLN.slug}
    data = _fetch_all_variants(
        staff_api_client, variables, permissions=[permission_manage_products]
    )
    assert data["totalCount"] == 2


def test_fetch_all_variants_staff_user_without_channel(
    staff_api_client,
    product_list_with_variants_many_channel,
    permission_manage_products,
):
    data = _fetch_all_variants(
        staff_api_client, permissions=[permission_manage_products]
    )
    assert data["totalCount"] == 3


def test_fetch_all_variants_customer(
    user_api_client, unavailable_product_with_variant, channel_USD
):
    data = _fetch_all_variants(user_api_client, variables={"channel": channel_USD.slug})
    assert data["totalCount"] == 0


def test_fetch_all_variants_anonymous_user(
    api_client, unavailable_product_with_variant, channel_USD
):
    data = _fetch_all_variants(api_client, variables={"channel": channel_USD.slug})
    assert data["totalCount"] == 0


def test_fetch_all_variants_without_sku_staff_user(
    staff_api_client, product, permission_manage_products
):
    variant = product.variants.first()
    variant.sku = None
    variant.save()

    data = _fetch_all_variants(
        staff_api_client, permissions=[permission_manage_products]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["id"] == variant_id


def test_fetch_all_variants_without_sku_staff_user_with_channel(
    staff_api_client,
    product,
    permission_manage_products,
    channel_USD,
):
    variant = product.variants.first()
    variant.sku = None
    variant.save()

    variables = {"channel": channel_USD.slug}
    data = _fetch_all_variants(
        staff_api_client, variables, permissions=[permission_manage_products]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["id"] == variant_id


def test_fetch_all_variants_without_sku_as_customer_with_channel(
    user_api_client, product, channel_USD
):
    variant = product.variants.first()
    variant.sku = None
    variant.save()

    ProductVariant.objects.update(sku=None)
    data = _fetch_all_variants(user_api_client, variables={"channel": channel_USD.slug})
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["id"] == variant_id


def test_fetch_all_variants_without_sku_as_anonymous_user_with_channel(
    api_client, product, channel_USD
):
    variant = product.variants.first()
    variant.sku = None
    variant.save()

    ProductVariant.objects.update(sku=None)
    data = _fetch_all_variants(api_client, variables={"channel": channel_USD.slug})
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["id"] == variant_id


QUERY_PRODUCT_VARIANTS_BY_IDS = """
    query getProductVariants($ids: [ID!], $channel: String) {
        productVariants(ids: $ids, first: 1, channel: $channel) {
            edges {
                node {
                    id
                }
            }
        }
    }
"""


def test_product_variants_by_ids(user_api_client, variant, channel_USD):
    query = QUERY_PRODUCT_VARIANTS_BY_IDS
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert data["edges"][0]["node"]["id"] == variant_id
    assert len(data["edges"]) == 1


def test_product_variants_by_invalid_ids(user_api_client, variant, channel_USD):
    query = QUERY_PRODUCT_VARIANTS_BY_IDS
    variant_id = "cbs"

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == f"Invalid ID: {variant_id}. Expected: ProductVariant."
    )
    assert content["data"]["productVariants"] is None


def test_product_variants_by_ids_that_do_not_exist(
    user_api_client, variant, channel_USD
):
    query = QUERY_PRODUCT_VARIANTS_BY_IDS
    variant_id = graphene.Node.to_global_id("Order", -1)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["productVariants"]["edges"] == []


def test_product_variants_visible_in_listings_by_customer(
    user_api_client, product_list, channel_USD
):
    # given
    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    # when
    data = _fetch_all_variants(user_api_client, variables={"channel": channel_USD.slug})

    assert data["totalCount"] == product_count - 1


def test_product_variants_visible_in_listings_by_staff_without_manage_products(
    staff_api_client, product_list, channel_USD
):
    # given
    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    # when
    data = _fetch_all_variants(
        staff_api_client, variables={"channel": channel_USD.slug}
    )

    assert data["totalCount"] == product_count - 1  # invisible doesn't count


def test_product_variants_visible_in_listings_by_staff_with_perm(
    staff_api_client, product_list, permission_manage_products, channel_USD
):
    # given
    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    # when
    data = _fetch_all_variants(
        staff_api_client,
        variables={"channel": channel_USD.slug},
        permissions=[permission_manage_products],
    )

    assert data["totalCount"] == product_count


def test_product_variants_visible_in_listings_by_app_without_manage_products(
    app_api_client, product_list, channel_USD
):
    # given
    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    # when
    data = _fetch_all_variants(app_api_client, variables={"channel": channel_USD.slug})

    assert data["totalCount"] == product_count - 1  # invisible doesn't count


def test_product_variants_visible_in_listings_by_app_with_perm(
    app_api_client, product_list, permission_manage_products, channel_USD
):
    # given
    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    # when
    data = _fetch_all_variants(
        app_api_client,
        variables={"channel": channel_USD.slug},
        permissions=[permission_manage_products],
    )

    assert data["totalCount"] == product_count
