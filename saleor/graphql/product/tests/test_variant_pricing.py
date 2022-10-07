from decimal import Decimal
from unittest.mock import Mock

from prices import Money, TaxedMoney

from ....product.models import ProductVariant
from ....product.utils.availability import get_variant_availability
from ....tax import TaxCalculationStrategy
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
    product = variant.product
    tax_class = product.tax_class or product.product_type.tax_class

    tc = channel_USD.tax_configuration
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.charge_taxes = True
    tc.prices_entered_with_tax = False
    tc.save()

    tax_rate = Decimal(23)
    country = "PL"
    tax_class.country_rates.update_or_create(rate=tax_rate, country=country)

    taxed_price = TaxedMoney(Money("10.0", "USD"), Money("12.30", "USD"))
    product_channel_listing = product.channel_listings.get()
    variant_channel_listing = variant.channel_listings.get()

    pricing = get_variant_availability(
        variant=variant,
        variant_channel_listing=variant_channel_listing,
        product=product,
        product_channel_listing=product_channel_listing,
        collections=[],
        discounts=[],
        channel=channel_USD,
        tax_rate=tax_rate,
        tax_calculation_strategy=tc.tax_calculation_strategy,
        prices_entered_with_tax=tc.prices_entered_with_tax,
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
        local_currency="PLN",
        tax_rate=tax_rate,
        tax_calculation_strategy=tc.tax_calculation_strategy,
        prices_entered_with_tax=tc.prices_entered_with_tax,
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
        tax_rate=tax_rate,
        tax_calculation_strategy=tc.tax_calculation_strategy,
        prices_entered_with_tax=tc.prices_entered_with_tax,
    )
    assert pricing.price.tax.amount
    assert pricing.price_undiscounted.tax.amount
    assert pricing.price_undiscounted.tax.amount
