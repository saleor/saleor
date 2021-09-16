from unittest.mock import Mock

from django_countries.fields import Country
from prices import Money, TaxedMoney

from ....plugins.manager import PluginsManager, get_plugins_manager
from ....product.models import ProductVariant
from ....product.utils.availability import get_variant_availability
from ...tests.utils import get_graphql_content

QUERY_GET_VARIANT_PRICING = """
fragment VariantPricingInfo on VariantPricingInfo {
  onSale
  discount {
    currency
    net {
      amount
    }
  }
  priceUndiscounted {
    currency
    net {
      amount
    }
  }
  price {
    currency
    net {
      amount
    }
  }
}
query ($channel: String, $address: AddressInput) {
  products(first: 1, channel: $channel) {
    edges {
      node {
        variants {
          pricing(address: $address) {
            ...VariantPricingInfo
          }
          pricingNoAddress: pricing {
            ...VariantPricingInfo
          }
        }
      }
    }
  }
}
"""


def test_get_variant_pricing_on_sale(api_client, sale, product, channel_USD):
    price = product.variants.first().channel_listings.get().price
    sale_discounted_value = sale.channel_listings.get().discount_value
    discounted_price = price.amount - sale_discounted_value

    variables = {"channel": channel_USD.slug, "address": {"country": "US"}}
    response = api_client.post_graphql(QUERY_GET_VARIANT_PRICING, variables)
    content = get_graphql_content(response)

    pricing = content["data"]["products"]["edges"][0]["node"]["variants"][0]["pricing"]

    # ensure the availability was correctly retrieved and sent
    assert pricing

    # check availability
    assert pricing["onSale"] is True

    # check the discount
    assert pricing["discount"]["currency"] == price.currency
    assert pricing["discount"]["net"]["amount"] == discounted_price

    # check the undiscounted price
    assert pricing["priceUndiscounted"]["currency"] == price.currency
    assert pricing["priceUndiscounted"]["net"]["amount"] == price.amount

    # check the discounted price
    assert pricing["price"]["currency"] == price.currency
    assert pricing["price"]["net"]["amount"] == discounted_price


def test_get_variant_pricing_not_on_sale(api_client, product, channel_USD):
    price = product.variants.first().channel_listings.get().price

    variables = {"channel": channel_USD.slug, "address": {"country": "US"}}
    response = api_client.post_graphql(QUERY_GET_VARIANT_PRICING, variables)
    content = get_graphql_content(response)

    pricing = content["data"]["products"]["edges"][0]["node"]["variants"][0]["pricing"]

    # ensure the availability was correctly retrieved and sent
    assert pricing

    # check availability
    assert pricing["onSale"] is False

    # check the discount
    assert pricing["discount"] is None

    # check the undiscounted price
    assert pricing["priceUndiscounted"]["currency"] == price.currency
    assert pricing["priceUndiscounted"]["net"]["amount"] == price.amount

    # check the discounted price
    assert pricing["price"]["currency"] == price.currency
    assert pricing["price"]["net"]["amount"] == price.amount


def test_variant_pricing(
    variant: ProductVariant, monkeypatch, settings, stock, channel_USD
):
    taxed_price = TaxedMoney(Money("10.0", "USD"), Money("12.30", "USD"))
    monkeypatch.setattr(
        PluginsManager, "apply_taxes_to_product", Mock(return_value=taxed_price)
    )

    product = variant.product
    product_channel_listing = product.channel_listings.get()
    variant_channel_listing = variant.channel_listings.get()

    manager = get_plugins_manager()
    pricing = get_variant_availability(
        variant=variant,
        variant_channel_listing=variant_channel_listing,
        product=product,
        product_channel_listing=product_channel_listing,
        collections=[],
        discounts=[],
        channel=channel_USD,
        plugins=manager,
        country=Country("US"),
    )
    assert pricing.price == taxed_price
    assert pricing.price_local_currency is None

    monkeypatch.setattr(
        "django_prices_openexchangerates.models.get_rates",
        lambda c: {"PLN": Mock(rate=2)},
    )

    settings.OPENEXCHANGERATES_API_KEY = "fake-key"

    pricing = get_variant_availability(
        variant=variant,
        variant_channel_listing=variant_channel_listing,
        product=product,
        product_channel_listing=product_channel_listing,
        collections=[],
        discounts=[],
        channel=channel_USD,
        plugins=manager,
        local_currency="PLN",
        country=Country("US"),
    )
    assert pricing.price_local_currency.currency == "PLN"  # type: ignore

    pricing = get_variant_availability(
        variant=variant,
        variant_channel_listing=variant_channel_listing,
        product=product,
        product_channel_listing=product_channel_listing,
        collections=[],
        discounts=[],
        channel=channel_USD,
        plugins=manager,
        country=Country("PL"),
    )
    assert pricing.price.tax.amount
    assert pricing.price_undiscounted.tax.amount
    assert pricing.price_undiscounted.tax.amount
