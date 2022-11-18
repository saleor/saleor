import graphene

from .....product.models import ProductVariant
from ....tests.utils import assert_no_permission, get_graphql_content


def test_product_variants_by_ids(staff_api_client, variant, channel_USD):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert data["edges"][0]["node"]["id"] == variant_id
    assert len(data["edges"]) == 1


def test_product_variants_without_price_by_ids_as_staff_without_permission(
    staff_api_client, variant, channel_USD
):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert len(data["edges"]) == 0


def test_product_variants_without_price_by_ids_as_staff_with_permission(
    staff_api_client, variant, channel_USD, permission_manage_products
):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert data["edges"][0]["node"]["id"] == variant_id
    assert len(data["edges"]) == 1


def test_product_variants_without_price_by_ids_as_user(
    user_api_client, variant, channel_USD
):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                    }
                }
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert len(data["edges"]) == 0


def test_product_variants_without_price_by_ids_as_app_without_permission(
    app_api_client, variant, channel_USD
):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = app_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert len(content["data"]["productVariants"]["edges"]) == 0


def test_product_variants_without_price_by_ids_as_app_with_permission(
    app_api_client, variant, channel_USD, permission_manage_products
):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert data["edges"][0]["node"]["id"] == variant_id
    assert len(data["edges"]) == 1


def test_product_variants_by_customer(user_api_client, variant, channel_USD):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_product_variants_no_ids_list(user_api_client, variant, channel_USD):
    query = """
        query getProductVariants($channel: String) {
            productVariants(first: 10, channel: $channel) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    variables = {"channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert len(data["edges"]) == ProductVariant.objects.count()
