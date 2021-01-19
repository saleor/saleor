import pytest
from graphene import Node

from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_product_details(product_with_image, api_client, count_queries, channel_USD):
    query = """
        fragment BasicProductFields on Product {
          id
          name
          thumbnail {
            url
            alt
          }
          thumbnail2x: thumbnail(size: 510) {
            url
          }
        }

        fragment ProductVariantFields on ProductVariant {
          id
          sku
          name
          pricing {
            discountLocalCurrency {
              currency
              gross {
                amount
                localized
              }
            }
            price {
              currency
              gross {
                amount
                localized
              }
            }
            priceUndiscounted {
              currency
              gross {
                amount
                localized
              }
            }
            priceLocalCurrency {
              currency
              gross {
                amount
                localized
              }
            }
          }
          attributes {
            attribute {
              id
              name
            }
            values {
              id
              name
              value: name
            }
          }
          images {
            id
            url
          }
        }

        query ProductDetails($id: ID!, $channel: String) {
          product(id: $id, channel: $channel) {
            ...BasicProductFields
            description
            category {
              id
              name
              products(first: 4, channel: $channel) {
                edges {
                  node {
                    ...BasicProductFields
                    category {
                      id
                      name
                    }
                    pricing {
                      priceRange {
                        start{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                        stop{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                      }
                      priceRangeUndiscounted {
                        start{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                        stop{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                      }
                      priceRangeLocalCurrency {
                        start{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                        stop{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            images {
              id
              url
            }
            variants {
              ...ProductVariantFields
            }
            seoDescription
            seoTitle
            isAvailable
          }
        }
    """
    product = product_with_image
    variant = product_with_image.variants.first()
    image = product_with_image.get_first_image()
    image.variant_images.create(variant=variant)

    variables = {
        "id": Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_product_attributes(
    product_list, api_client, count_queries, channel_USD
):
    query = """
        query($sortBy: ProductOrder, $channel: String) {
          products(first: 10, sortBy: $sortBy, channel: $channel) {
            edges {
              node {
                id
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

    variables = {"channel": channel_USD.slug}
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_channel_listings(
    product_list_with_many_channels,
    staff_api_client,
    count_queries,
    permission_manage_products,
    channel_USD,
):
    query = """
        query($channel: String) {
          products(first: 10, channel: $channel) {
            edges {
              node {
                id
                channelListings {
                  publicationDate
                  isPublished
                  channel{
                    slug
                    currencyCode
                    name
                    isActive
                  }
                  visibleInListings
                  discountedPrice{
                    amount
                    currency
                  }
                  purchaseCost{
                    start{
                      amount
                    }
                    stop{
                      amount
                    }
                  }
                  margin{
                    start
                    stop
                  }
                  isAvailableForPurchase
                  availableForPurchase
                  pricing {
                    priceRangeUndiscounted {
                      start {
                        gross {
                          amount
                          currency
                        }
                      }
                      stop {
                        gross {
                          amount
                          currency
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
    """

    variables = {"channel": channel_USD.slug}
    get_graphql_content(
        staff_api_client.post_graphql(
            query,
            variables,
            permissions=(permission_manage_products,),
            check_no_permissions=False,
        )
    )


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrive_products_with_product_types_and_attributes(
    product_list,
    api_client,
    count_queries,
    channel_USD,
):
    query = """
        query($channel: String) {
          products(first: 10, channel: $channel) {
            edges {
              node {
                id
                  productType {
                    name
                  productAttributes {
                    name
                  }
                  variantAttributes {
                    name
                  }
                }
              }
            }
          }
        }
    """
    variables = {"channel": channel_USD.slug}
    get_graphql_content(api_client.post_graphql(query, variables))
