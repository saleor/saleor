from unittest.mock import Mock

from saleor.product.models import ProductVariant
from saleor.product.utils.availability import get_variant_availability
from tests.api.utils import get_graphql_content

QUERY_GET_VARIANT_PRICING = """
query {
  products(first: 1) {
    edges {
      node {
        variants {
          pricing {
            available
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
        }
      }
    }
  }
}
"""


def test_get_variant_pricing_on_sale(api_client, sale, product):
    price = product.price
    discounted_price = price.amount - sale.value

    response = api_client.post_graphql(QUERY_GET_VARIANT_PRICING, {})
    content = get_graphql_content(response)

    pricing = (
        content['data']['products']['edges'][0]['node']
        ['variants'][0]['pricing'])

    # ensure the availability was correctly retrieved and sent
    assert pricing

    # check availability
    assert pricing['available'] is True
    assert pricing['onSale'] is True

    # check the discount
    assert pricing['discount']['currency'] == price.currency
    assert pricing['discount']['net']['amount'] == discounted_price

    # check the undiscounted price
    assert (
        pricing['priceUndiscounted']['currency'] == price.currency)
    assert (
        pricing['priceUndiscounted']['net']['amount'] == price.amount)

    # check the discounted price
    assert pricing['price']['currency'] == price.currency
    assert pricing['price']['net']['amount'] == discounted_price


def test_get_variant_pricing_not_on_sale(api_client, product):
    response = api_client.post_graphql(QUERY_GET_VARIANT_PRICING, {})
    content = get_graphql_content(response)

    pricing = (
        content['data']['products']['edges'][0]['node']
        ['variants'][0]['pricing'])

    # ensure the availability was correctly retrieved and sent
    assert pricing

    # check availability
    assert pricing['available'] is True
    assert pricing['onSale'] is False

    # check the discount
    assert pricing['discount'] is None

    # check the undiscounted price
    assert (
        pricing['priceUndiscounted']['currency'] == product.price.currency)
    assert (
        pricing['priceUndiscounted']['net']['amount'] == product.price.amount)

    # check the discounted price
    assert pricing['price']['currency'] == product.price.currency
    assert pricing['price']['net']['amount'] == product.price.amount


def test_variant_pricing(
        variant: ProductVariant, monkeypatch, settings, taxes):
    pricing = get_variant_availability(variant)
    assert pricing.price == variant.get_price()
    assert pricing.price_local_currency is None

    monkeypatch.setattr(
        'django_prices_openexchangerates.models.get_rates',
        lambda c: {'PLN': Mock(rate=2)})

    settings.DEFAULT_COUNTRY = 'PL'
    settings.OPENEXCHANGERATES_API_KEY = 'fake-key'

    pricing = get_variant_availability(variant, local_currency='PLN')
    assert pricing.price_local_currency.currency == 'PLN'
    assert pricing.available

    pricing = get_variant_availability(variant, taxes=taxes)
    assert pricing.price.tax.amount
    assert pricing.price_undiscounted.tax.amount
    assert pricing.price_undiscounted.tax.amount
    assert pricing.available
