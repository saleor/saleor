from unittest.mock import patch

import pytest

from .....checkout.utils import set_external_shipping_id
from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_user_checkout_details(user_api_client, customer_checkout, count_queries):
    query = """
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

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
          }
          variant {
            ...ProductVariant
          }
          quantity
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

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
          }
        }

        fragment Checkout on Checkout {
          availablePaymentGateways {
            id
            name
            config {
              field
              value
            }
          }
          token
          id
          totalPrice {
            ...Price
          }
          subtotalPrice {
            ...Price
          }
          billingAddress {
            ...Address
          }
          shippingAddress {
            ...Address
          }
          email
          availableShippingMethods {
            ...ShippingMethod
          }
          shippingMethod {
            ...ShippingMethod
          }
          shippingPrice {
            ...Price
          }
          lines {
            ...CheckoutLine
          }
          isShippingRequired
          discount {
            currency
            amount
          }
          discountName
          translatedDiscountName
          voucherCode
        }

        query UserCheckoutDetails {
          me {
            id
            checkout {
              ...Checkout
            }
          }
        }
    """
    get_graphql_content(user_api_client.post_graphql(query))


@patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_user_checkout_details_with_external_shipping_method(
    mock_send_request,
    user_api_client,
    customer_checkout,
    shipping_app,
    settings,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    external_id = "abcd"
    mock_json_response = [
        {
            "id": external_id,
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    checkout = customer_checkout
    checkout.shipping_method = None
    set_external_shipping_id(checkout, external_id)
    checkout.save()
    mock_send_request.return_value = mock_json_response
    query = """
        query {
          me {
            checkout {
              id
              deliveryMethod {
                  __typename
              }
              shippingMethod {
                  __typename
              }
              shippingMethods {
                id
              }
            }
          }
        }
    """

    # when
    get_graphql_content(user_api_client.post_graphql(query))

    # then
    assert mock_send_request.call_count == 1
