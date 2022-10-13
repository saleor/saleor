import graphene
import pytest

from ....tax import TaxCalculationStrategy
from ....tax.models import TaxClassCountryRate, TaxConfigurationPerCountry
from ...tests.utils import get_graphql_content

FRAGMENT_PRICE = """
  fragment Price on TaxedMoney {
    gross {
      amount
    }
    net {
      amount
    }
    tax {
      amount
    }
  }
"""


FRAGMENT_PRICING = (
    """
  fragment Pricing on ProductPricingInfo {
    priceRange {
      start {
        ...Price
      }
      stop {
        ...Price
      }
    }
    priceRangeUndiscounted {
      start {
        ...Price
      }
      stop {
        ...Price
      }
    }
  }
"""
    + FRAGMENT_PRICE
)


QUERY_PRODUCT_PRICING = (
    """
  query Product($id: ID!, $channel: String!) {
    product(id: $id, channel: $channel) {
      pricingPL: pricing(address: { country: PL }) {
        ...Pricing
      }
      pricingDE: pricing(address: { country: DE }) {
        ...Pricing
      }
      pricing: pricing {
        ...Pricing
      }
    }
  }
"""
    + FRAGMENT_PRICING
)


def _enable_flat_rates(channel, prices_entered_with_tax):
    tc = channel.tax_configuration
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.charge_taxes = True
    tc.country_exceptions.all().delete()
    tc.country_exceptions.create(
        country="PL",
        charge_taxes=True,
        tax_calculation_strategy=TaxCalculationStrategy.FLAT_RATES,
    )
    tc.country_exceptions.create(
        country="DE",
        charge_taxes=True,
        tax_calculation_strategy=TaxCalculationStrategy.FLAT_RATES,
    )
    tc.save()


def _configure_tax_rates(product):
    product.tax_class.country_rates.all().delete()
    product.tax_class.country_rates.create(country="PL", rate=23)
    product.tax_class.country_rates.create(country="DE", rate=19)


@pytest.mark.parametrize(
    "net_PL, gross_PL, net_DE, gross_DE, prices_entered_with_tax",
    [
        (40.65, 50.00, 42.02, 50.00, True),
        (50.00, 61.50, 50.00, 59.50, False),
    ],
)
def test_product_pricing(
    product_available_in_many_channels,
    channel_PLN,
    user_api_client,
    net_PL,
    gross_PL,
    net_DE,
    gross_DE,
    prices_entered_with_tax,
):
    # given
    product = product_available_in_many_channels
    _enable_flat_rates(channel_PLN, prices_entered_with_tax)
    _configure_tax_rates(product)

    # when
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_PLN.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_PRICING, variables)
    content = get_graphql_content(response)
    data = content["data"]["product"]

    # then
    price_range_PL = data["pricingPL"]["priceRange"]
    price_range_undiscounted_PL = data["pricingPL"]["priceRangeUndiscounted"]
    assert price_range_PL["start"]["net"]["amount"] == net_PL
    assert price_range_PL["start"]["gross"]["amount"] == gross_PL
    assert price_range_PL["stop"]["net"]["amount"] == net_PL
    assert price_range_PL["stop"]["gross"]["amount"] == gross_PL
    assert price_range_undiscounted_PL["start"]["net"]["amount"] == net_PL
    assert price_range_undiscounted_PL["start"]["gross"]["amount"] == gross_PL
    assert price_range_undiscounted_PL["stop"]["net"]["amount"] == net_PL
    assert price_range_undiscounted_PL["stop"]["gross"]["amount"] == gross_PL

    price_range_DE = data["pricingDE"]["priceRange"]
    price_range_undiscounted_DE = data["pricingDE"]["priceRangeUndiscounted"]
    assert price_range_DE["start"]["net"]["amount"] == net_DE
    assert price_range_DE["start"]["gross"]["amount"] == gross_DE
    assert price_range_DE["stop"]["net"]["amount"] == net_DE
    assert price_range_DE["stop"]["gross"]["amount"] == gross_DE
    assert price_range_undiscounted_DE["start"]["net"]["amount"] == net_DE
    assert price_range_undiscounted_DE["start"]["gross"]["amount"] == gross_DE
    assert price_range_undiscounted_DE["stop"]["net"]["amount"] == net_DE
    assert price_range_undiscounted_DE["stop"]["gross"]["amount"] == gross_DE


def test_product_pricing_default_country_default_rate(
    product_available_in_many_channels,
    channel_PLN,
    user_api_client,
):
    # given
    product = product_available_in_many_channels
    _enable_flat_rates(channel_PLN, True)
    TaxClassCountryRate.objects.all().delete()
    TaxClassCountryRate.objects.create(country=channel_PLN.default_country, rate=23)

    # when
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_PLN.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_PRICING, variables)
    content = get_graphql_content(response)
    data = content["data"]["product"]

    # then
    price_range = data["pricing"]["priceRange"]
    price_range_undiscounted = data["pricing"]["priceRangeUndiscounted"]
    assert price_range["start"]["net"]["amount"] == 40.65
    assert price_range["start"]["gross"]["amount"] == 50.00
    assert price_range["stop"]["net"]["amount"] == 40.65
    assert price_range["stop"]["gross"]["amount"] == 50.00
    assert price_range_undiscounted["start"]["net"]["amount"] == 40.65
    assert price_range_undiscounted["start"]["gross"]["amount"] == 50.00
    assert price_range_undiscounted["stop"]["net"]["amount"] == 40.65
    assert price_range_undiscounted["stop"]["gross"]["amount"] == 50.00


def test_product_pricing_use_tax_class_from_product_type(
    product_available_in_many_channels,
    channel_PLN,
    user_api_client,
):
    # given
    product = product_available_in_many_channels
    _enable_flat_rates(channel_PLN, True)
    TaxClassCountryRate.objects.all().delete()
    product.tax_class = None
    product.save(update_fields=["tax_class"])
    product.product_type.tax_class.country_rates.create(
        country=channel_PLN.default_country, rate=23
    )

    # when
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_PLN.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_PRICING, variables)
    content = get_graphql_content(response)
    data = content["data"]["product"]

    # then
    price_range_PL = data["pricingPL"]["priceRange"]
    price_range_undiscounted_PL = data["pricingPL"]["priceRangeUndiscounted"]
    assert price_range_PL["start"]["net"]["amount"] == 40.65
    assert price_range_PL["start"]["gross"]["amount"] == 50.00
    assert price_range_PL["stop"]["net"]["amount"] == 40.65
    assert price_range_PL["stop"]["gross"]["amount"] == 50.00
    assert price_range_undiscounted_PL["start"]["net"]["amount"] == 40.65
    assert price_range_undiscounted_PL["start"]["gross"]["amount"] == 50.00
    assert price_range_undiscounted_PL["stop"]["net"]["amount"] == 40.65
    assert price_range_undiscounted_PL["stop"]["gross"]["amount"] == 50.00


def test_product_pricing_no_flat_rates_in_one_country(
    product_available_in_many_channels,
    channel_PLN,
    user_api_client,
):
    # given
    product = product_available_in_many_channels
    _enable_flat_rates(channel_PLN, True)
    _configure_tax_rates(product)
    TaxConfigurationPerCountry.objects.filter(country="PL").update(
        tax_calculation_strategy=None
    )

    # when
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_PLN.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_PRICING, variables)
    content = get_graphql_content(response)
    data = content["data"]["product"]

    # then
    price_range_PL = data["pricingPL"]["priceRange"]
    price_range_undiscounted_PL = data["pricingPL"]["priceRangeUndiscounted"]
    assert price_range_PL["start"]["net"]["amount"] == 50.00
    assert price_range_PL["start"]["gross"]["amount"] == 50.00
    assert price_range_PL["stop"]["net"]["amount"] == 50.00
    assert price_range_PL["stop"]["gross"]["amount"] == 50.00
    assert price_range_undiscounted_PL["start"]["net"]["amount"] == 50.00
    assert price_range_undiscounted_PL["start"]["gross"]["amount"] == 50.00
    assert price_range_undiscounted_PL["stop"]["net"]["amount"] == 50.00
    assert price_range_undiscounted_PL["stop"]["gross"]["amount"] == 50.00

    price_range_DE = data["pricingDE"]["priceRange"]
    price_range_undiscounted_DE = data["pricingDE"]["priceRangeUndiscounted"]
    assert price_range_DE["start"]["net"]["amount"] == 42.02
    assert price_range_DE["start"]["gross"]["amount"] == 50.00
    assert price_range_DE["stop"]["net"]["amount"] == 42.02
    assert price_range_DE["stop"]["gross"]["amount"] == 50.00
    assert price_range_undiscounted_DE["start"]["net"]["amount"] == 42.02
    assert price_range_undiscounted_DE["start"]["gross"]["amount"] == 50.00
    assert price_range_undiscounted_DE["stop"]["net"]["amount"] == 42.02
    assert price_range_undiscounted_DE["stop"]["gross"]["amount"] == 50.00
