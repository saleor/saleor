import pytest

from .....app.models import App
from .....app.types import AppType
from .....graphql.core.utils import to_global_id_or_none
from .....webhook.event_types import WebhookEventSyncType
from .....webhook.models import Webhook, WebhookEvent

CALCULATE_TAXES_SUBSCRIPTION_QUERY = """
subscription CalculateTaxes {
  event {
    ...CalculateTaxesEvent
  }
}

fragment CalculateTaxesEvent on Event {
  __typename
  ... on CalculateTaxes {
    taxBase {
      ...TaxBase
    }
    recipient {
      privateMetadata {
        key
        value
      }
    }
  }
}

fragment TaxBase on TaxableObject {
  pricesEnteredWithTax
  currency
  channel {
    slug
  }
  discounts {
    ...TaxDiscount
  }
  address {
    ...Address
  }
  shippingPrice {
    amount
  }
  lines {
    ...TaxBaseLine
  }
  sourceObject {
    __typename
    ... on Checkout {
      avataxEntityCode: metafield(key: "avataxEntityCode")
      user {
        ...User
      }
    }
    ... on Order {
      avataxEntityCode: metafield(key: "avataxEntityCode")
      user {
        ...User
      }
    }
  }
}

fragment TaxDiscount on TaxableObjectDiscount {
  name
  amount {
    amount
  }
}

fragment Address on Address {
  streetAddress1
  streetAddress2
  city
  countryArea
  postalCode
  country {
    code
  }
}

fragment TaxBaseLine on TaxableObjectLine {
  sourceLine {
    __typename
    ... on CheckoutLine {
      id
      checkoutProductVariant: variant {
        id
        product {
          taxClass {
            id
            name
          }
        }
      }
    }
    ... on OrderLine {
      id
      orderProductVariant: variant {
        id
        product {
          taxClass {
            id
            name
          }
        }
      }
    }
  }
  quantity
  unitPrice {
    amount
  }
  totalPrice {
    amount
  }
}

fragment User on User {
  id
  email
  avataxCustomerCode: metafield(key: "avataxCustomerCode")
}
"""


@pytest.fixture
def tax_app(db, permission_handle_taxes, permission_manage_users):
    app = App.objects.create(name="Tax App", is_active=True)
    app.identifier = to_global_id_or_none(app)
    app.save()
    app.permissions.add(permission_handle_taxes)
    app.permissions.add(permission_manage_users)

    webhook = Webhook.objects.create(
        name="tax-webhook-1",
        app=app,
        target_url="https://tax-app.com/api/",
        subscription_query=CALCULATE_TAXES_SUBSCRIPTION_QUERY,
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in [
                WebhookEventSyncType.ORDER_CALCULATE_TAXES,
                WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
            ]
        ]
    )
    return app


@pytest.fixture
def external_tax_app(db, permission_handle_taxes):
    app = App.objects.create(
        name="External App",
        is_active=True,
        type=AppType.THIRDPARTY,
        identifier="mirumee.app.simple.tax",
        about_app="About app text.",
        data_privacy="Data privacy text.",
        data_privacy_url="http://www.example.com/privacy/",
        homepage_url="http://www.example.com/homepage/",
        support_url="http://www.example.com/support/contact/",
        configuration_url="http://www.example.com/app-configuration/",
        app_url="http://www.example.com/app/",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_handle_taxes)

    webhook = Webhook.objects.create(
        name="external-tax-webhook-1",
        app=app,
        target_url="https://tax-app.example.com/api/",
        subscription_query=CALCULATE_TAXES_SUBSCRIPTION_QUERY,
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in [
                WebhookEventSyncType.ORDER_CALCULATE_TAXES,
                WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
            ]
        ]
    )
    return app
