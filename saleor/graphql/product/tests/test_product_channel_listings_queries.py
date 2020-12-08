import graphene

from ...tests.utils import get_graphql_content

QUERY_PRICING_ON_PRODUCT_CHANNEL_LISTING = """
query FetchProduct($id: ID, $channel: String) {
  product(id: $id, channel: $channel) {
    id
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
    channelListings {
      channel {
        slug
      }
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
"""


def test_product_channel_listing_pricing_field(
    staff_api_client, permission_manage_products, channel_USD, product
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    product.channel_listings.exclude(channel__slug=channel_USD.slug).delete()

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRICING_ON_PRODUCT_CHANNEL_LISTING,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    product_channel_listing_data = product_data["channelListings"][0]
    assert product_data["pricing"] == product_channel_listing_data["pricing"]
