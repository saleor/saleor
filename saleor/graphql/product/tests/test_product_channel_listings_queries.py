from unittest import mock

import graphene

from ....warehouse.models import Warehouse
from ...tests.utils import get_graphql_content

QUERY_PRICING_ON_PRODUCT_CHANNEL_LISTING = """
fragment Pricing on ProductPricingInfo {
  priceRangeUndiscounted {
    start {
      net {
        amount
        currency
      }
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
query FetchProduct($id: ID, $channel: String, $address: AddressInput) {
  product(id: $id, channel: $channel) {
    id
    pricing(address: $address) {
      ...Pricing
    }
    pricingNoAddress: pricing {
      ...Pricing
    }
    channelListings {
      channel {
        slug
      }
      pricing(address: $address) {
        ...Pricing
      }
      pricingNoAddress: pricing {
        ...Pricing
      }
    }
  }
}
"""


@mock.patch("saleor.graphql.product.types.channels.WarehouseCountryCodeByChannelLoader")
def test_product_channel_listing_pricing_field(
    warehouse_country_code_loader,
    address_usa,
    staff_api_client,
    permission_manage_products,
    channel_USD,
    product,
):
    # given

    # Changing the address of a warehouse used by the product to address_usa, so that
    # we can query pricing in two countries: US and PL.
    warehouse = Warehouse.objects.first()
    warehouse.address = address_usa
    warehouse.save()

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
        "address": {"country": "PL"},
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
    assert warehouse_country_code_loader.called
