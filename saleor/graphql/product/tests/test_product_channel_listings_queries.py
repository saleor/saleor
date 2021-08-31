from unittest import mock

import graphene

from ....product.utils.availability import get_product_availability
from ....warehouse.models import Warehouse
from ...tests.utils import get_graphql_content

QUERY_PRICING_ON_PRODUCT_CHANNEL_LISTING = """
fragment Pricing on ProductPricingInfo {
  priceRangeUndiscounted {
    start {
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
    channelListings {
      channel {
        slug
      }
      pricing(address: $address) {
        ...Pricing
      }
    }
  }
}
"""


def test_product_channel_listing_pricing_field(
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


QUERY_PRICING_ON_PRODUCT_CHANNEL_LISTING_NO_ADDRESS = """
fragment Pricing on ProductPricingInfo {
  priceRangeUndiscounted {
    start {
      gross {
        amount
        currency
      }
    }
  }
}
query FetchProduct($id: ID, $channel: String) {
  product(id: $id, channel: $channel) {
    id
    pricing {
      ...Pricing
    }
    channelListings {
      pricing {
        ...Pricing
      }
    }
  }
}
"""


@mock.patch(
    "saleor.graphql.product.types.products.get_product_availability",
    wraps=get_product_availability,
)
def test_product_channel_listing_pricing_field_no_address(
    mock_get_product_availability,
    staff_api_client,
    permission_manage_products,
    channel_USD,
    product,
):
    # given
    channel_USD.default_country = "FR"
    channel_USD.save()
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    product.channel_listings.exclude(channel__slug=channel_USD.slug).delete()

    # when
    staff_api_client.post_graphql(
        QUERY_PRICING_ON_PRODUCT_CHANNEL_LISTING_NO_ADDRESS,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    assert (
        mock_get_product_availability.call_args[1]["country"]
        == channel_USD.default_country
    )
