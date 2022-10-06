from unittest.mock import patch

import pytest
from django.utils import timezone

from .....checkout.utils import set_external_shipping_id
from .....plugins.webhook.shipping import to_shipping_app_id
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
    app,
    user_api_client,
    customer_checkout,
    shipping_app,
    settings,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    external_id = to_shipping_app_id(app, "abcd")
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


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
@patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_user_checkout_details_with_tax_app(
    mock_send_request,
    user_api_client,
    customer_checkout,
    tax_app,
    settings,
    count_queries,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mock_json_response = {
        "currency": "PLN",
        "total_net_amount": 1080,
        "total_gross_amount": 1200,
        "subtotal_net_amount": 1000,
        "subtotal_gross_amount": 1100,
        "shipping_price_gross_amount": 100.0,
        "shipping_price_net_amount": 80.00,
        "shipping_tax_rate": 0.25,
        "lines": [
            {
                "id": line.pk,
                "currency": "PLN",
                "unit_net_amount": 12.34,
                "unit_gross_amount": 12.34,
                "total_gross_amount": 12.34,
                "total_net_amount": 12.34,
                "tax_rate": 0.23,
            }
            for line in customer_checkout.lines.all()
        ],
    }
    mock_send_request.return_value = mock_json_response
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
        query {
          me {
            checkout {
              totalPrice {
                ...Price
              }
              subtotalPrice {
                ...Price
              }
              shippingPrice {
                ...Price
              }
            }
          }
        }
    """
    customer_checkout.price_expiration = timezone.now()
    customer_checkout.save()

    # when
    get_graphql_content(user_api_client.post_graphql(query))

    # then
    customer_checkout.refresh_from_db()
    assert mock_send_request.call_count == 1
