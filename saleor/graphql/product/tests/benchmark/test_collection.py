import graphene
import pytest

from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_collection_view(api_client, published_collection, count_queries, channel_USD):
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

        fragment Price on TaxedMoney {
          gross {
            amount
            currency
          }
          net {
            amount
            currency
          }
        }

        fragment ProductPricingField on Product {
          pricing {
            onSale
            priceRangeUndiscounted {
              start {
                ...Price
              }
              stop {
                ...Price
              }
            }
            priceRange {
              start {
                ...Price
              }
              stop {
                ...Price
              }
            }
          }
        }

        query Collection($id: ID!, $pageSize: Int, $channel: String) {
          collection(id: $id, channel: $channel) {
            id
            slug
            name
            seoDescription
            seoTitle
            backgroundImage {
              url
            }
          }
          products (
            first: $pageSize,
            filter: {collections: [$id]},
            channel: $channel
          ) {
            totalCount
            edges {
              node {
                ...BasicProductFields
                ...ProductPricingField
                category {
                  id
                  name
                }
              }
            }
            pageInfo {
              endCursor
              hasNextPage
              hasPreviousPage
              startCursor
            }
          }
          attributes(filter: {inCollection: $id, channel: $channel}, first: 100) {
            edges {
              node {
                id
                name
                slug
                values {
                  id
                  name
                  slug
                }
              }
            }
          }
        }
    """
    variables = {
        "pageSize": 100,
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "channel": channel_USD.slug,
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_collection_channel_listings(
    product_list_with_many_channels,
    staff_api_client,
    count_queries,
    permission_manage_products,
    channel_USD,
):
    query = """
        query($channel: String) {
          collections(first: 10, channel: $channel) {
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
