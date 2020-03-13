import pytest

from tests.api.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_user_order_details(user_api_client, order_with_lines, count_queries):
    query = """
        fragment OrderPrice on TaxedMoney {
          gross {
            amount
            currency
          }
          net {
            amount
            currency
          }
        }

        fragment Address on Address {
          id
          firstName
          lastName
          companyName
          streetAddress1
          streetAddress2
          city
          postalCode
          country {
            code
            country
          }
          countryArea
          phone
          isDefaultBillingAddress
          isDefaultShippingAddress
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

        fragment ProductVariant on ProductVariant {
          id
          name
          pricing {
            onSale
            priceUndiscounted {
              ...Price
            }
            price {
              ...Price
            }
          }
          product {
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
        }

        fragment OrderDetail on Order {
          userEmail
          paymentStatus
          paymentStatusDisplay
          status
          statusDisplay
          id
          number
          shippingAddress {
            ...Address
          }
          lines {
            productName
            quantity
            variant {
              ...ProductVariant
            }
            unitPrice {
              currency
              ...OrderPrice
            }
          }
          subtotal {
            ...OrderPrice
          }
          total {
            ...OrderPrice
          }
          shippingPrice {
            ...OrderPrice
          }
        }

        query OrderByToken($token: UUID!) {
          orderByToken(token: $token) {
            ...OrderDetail
          }
        }
    """
    variables = {
        "token": order_with_lines.token,
    }
    get_graphql_content(user_api_client.post_graphql(query, variables))
