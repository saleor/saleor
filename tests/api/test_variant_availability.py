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
