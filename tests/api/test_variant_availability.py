from unittest.mock import Mock

from saleor.product.models import ProductVariant
from saleor.product.utils.availability import get_variant_availability
from tests.api.utils import get_graphql_content

QUERY_GET_VARIANT_AVAILABILITY = """
query {
  products(first: 1) {
    edges {
      node {
        variants {
          availability {
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


def test_get_variant_availability_on_sale(api_client, sale, product):
    response = api_client.post_graphql(QUERY_GET_VARIANT_AVAILABILITY, {})
    content = get_graphql_content(response)

    availability = (
        content['data']['products']['edges'][0]['node']
        ['variants'][0]['availability'])

    # ensure the availability was correctly retrieved and sent
    assert availability

    # check availability
    assert availability['available'] is True
    assert availability['onSale'] is True

    # check the discount
    assert availability['discount']['currency'] == 'USD'
    assert availability['discount']['net']['amount'] == 5.0

    # check the undiscounted price
    assert availability['priceUndiscounted']['currency'] == 'USD'
    assert availability['priceUndiscounted']['net']['amount'] == 10.0

    # check the discounted price
    assert availability['price']['currency'] == 'USD'
    assert availability['price']['net']['amount'] == 5.0


def test_get_variant_availability_not_on_sale(api_client, product):
    response = api_client.post_graphql(QUERY_GET_VARIANT_AVAILABILITY, {})
    content = get_graphql_content(response)

    availability = (
        content['data']['products']['edges'][0]['node']
        ['variants'][0]['availability'])

    # ensure the availability was correctly retrieved and sent
    assert availability

    # check availability
    assert availability['available'] is True
    assert availability['onSale'] is False

    # check the discount
    assert availability['discount'] is None

    # check the undiscounted price
    assert availability['priceUndiscounted']['currency'] == 'USD'
    assert availability['priceUndiscounted']['net']['amount'] == 10.0

    # check the discounted price
    assert availability['price']['currency'] == 'USD'
    assert availability['price']['net']['amount'] == 10.0


def test_variant_availability(
        variant: ProductVariant, monkeypatch, settings, taxes):
    availability = get_variant_availability(variant)
    assert availability.price == variant.get_price()
    assert availability.price_local_currency is None

    monkeypatch.setattr(
        'django_prices_openexchangerates.models.get_rates',
        lambda c: {'PLN': Mock(rate=2)})

    settings.DEFAULT_COUNTRY = 'PL'
    settings.OPENEXCHANGERATES_API_KEY = 'fake-key'

    availability = get_variant_availability(variant, local_currency='PLN')
    assert availability.price_local_currency.currency == 'PLN'
    assert availability.available

    availability = get_variant_availability(variant, taxes=taxes)
    assert availability.price.tax.amount
    assert availability.price_undiscounted.tax.amount
    assert availability.price_undiscounted.tax.amount
    assert availability.available
