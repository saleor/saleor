from unittest.mock import MagicMock

import pytest

from saleor.app.models import App
from saleor.webhook.event_types import WebhookEventType
from saleor.webhook.models import Webhook

from ....tests.utils import get_graphql_content


@pytest.fixture
def mock_webhook_plugin_with_shipping_app(
    settings,
    permission_manage_checkouts,
    monkeypatch,
):
    # Mock http requests as we are focusing on testing database access
    response = MagicMock()
    response.json.return_value = {"excluded_methods": []}
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: response)

    # Enable webhook plugin
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    # Create multiple apps with a shipping webhook
    for i in range(3):
        app = App.objects.create(name=f"Benchmark App {i}", is_active=True)
        app.tokens.create(name="Default")
        app.permissions.add(permission_manage_checkouts)
        webhook = Webhook.objects.create(
            name="shipping-webhook-1",
            app=app,
            target_url="https://shipping-gateway.com/api/",
        )
        webhook.events.create(
            event_type=WebhookEventType.CHECKOUT_FILTER_SHIPPING_METHODS,
            webhook=webhook,
        )


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_user_checkout_details(
    mock_webhook_plugin_with_shipping_app,
    user_api_client,
    customer_checkout,
    count_queries,
):
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
