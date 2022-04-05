import pytest

from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.models import Webhook


@pytest.fixture
def subscription_webhook(app):
    def fun(query, event_type, name="Subscription"):
        webhook = Webhook.objects.create(
            name=name,
            app=app,
            target_url="http://www.example.com/any",
            subscription_query=query,
        )
        webhook.events.create(event_type=event_type)
        return webhook

    return fun


PRODUCT_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ProductUpdated{
          product{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_product_updated_webhook(subscription_webhook):
    return subscription_webhook(
        PRODUCT_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.PRODUCT_UPDATED
    )


PRODUCT_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ProductCreated{
          product{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_product_created_webhook(subscription_webhook):
    return subscription_webhook(
        PRODUCT_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.PRODUCT_CREATED
    )


PRODUCT_DELETED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ProductDeleted{
          product{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_product_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        PRODUCT_DELETED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.PRODUCT_DELETED
    )


PRODUCT_VARIANT_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ProductVariantCreated{
          productVariant{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_product_variant_created_webhook(subscription_webhook):
    return subscription_webhook(
        PRODUCT_VARIANT_CREATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.PRODUCT_VARIANT_CREATED,
    )


PRODUCT_VARIANT_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ProductVariantUpdated{
          productVariant{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_product_variant_updated_webhook(subscription_webhook):
    return subscription_webhook(
        PRODUCT_VARIANT_UPDATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
    )


PRODUCT_VARIANT_DELETED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ProductVariantDeleted{
          productVariant{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_product_variant_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        PRODUCT_VARIANT_DELETED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.PRODUCT_VARIANT_DELETED,
    )


PRODUCT_VARIANT_OUT_OF_STOCK_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ProductVariantOutOfStock{
          productVariant{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_product_variant_out_of_stock_webhook(subscription_webhook):
    return subscription_webhook(
        PRODUCT_VARIANT_OUT_OF_STOCK_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK,
    )


PRODUCT_VARIANT_BACK_IN_STOCK_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ProductVariantBackInStock{
          productVariant{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_product_variant_back_in_stock_webhook(subscription_webhook):
    return subscription_webhook(
        PRODUCT_VARIANT_BACK_IN_STOCK_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK,
    )


ORDER_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on OrderCreated{
          order{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_order_created_webhook(subscription_webhook):
    return subscription_webhook(
        ORDER_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.ORDER_CREATED
    )


ORDER_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on OrderUpdated{
          order{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_order_updated_webhook(subscription_webhook):
    return subscription_webhook(
        ORDER_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.ORDER_UPDATED
    )


ORDER_CONFIRMED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on OrderConfirmed{
          order{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_order_confirmed_webhook(subscription_webhook):
    return subscription_webhook(
        ORDER_CONFIRMED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.ORDER_CONFIRMED
    )


ORDER_FULLY_PAID_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on OrderFullyPaid{
          order{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_order_fully_paid_webhook(subscription_webhook):
    return subscription_webhook(
        ORDER_FULLY_PAID_SUBSCRIPTION_QUERY, WebhookEventAsyncType.ORDER_FULLY_PAID
    )


ORDER_CANCELLED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on OrderCancelled{
          order{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_order_cancelled_webhook(subscription_webhook):
    return subscription_webhook(
        ORDER_CANCELLED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.ORDER_CANCELLED
    )


ORDER_FULFILLED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on OrderFulfilled{
          order{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_order_fulfilled_webhook(subscription_webhook):
    return subscription_webhook(
        ORDER_FULFILLED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.ORDER_FULFILLED
    )


DRAFT_ORDER_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on DraftOrderCreated{
          order{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_draft_order_created_webhook(subscription_webhook):
    return subscription_webhook(
        DRAFT_ORDER_CREATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.DRAFT_ORDER_CREATED,
    )


DRAFT_ORDER_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on DraftOrderUpdated{
          order{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_draft_order_updated_webhook(subscription_webhook):
    return subscription_webhook(
        DRAFT_ORDER_UPDATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.DRAFT_ORDER_UPDATED,
    )


DRAFT_ORDER_DELETED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on DraftOrderDeleted{
          order{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_draft_order_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        DRAFT_ORDER_DELETED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.DRAFT_ORDER_DELETED,
    )


SALE_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on SaleCreated{
          sale{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_sale_created_webhook(subscription_webhook):
    return subscription_webhook(
        SALE_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.SALE_CREATED
    )


SALE_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on SaleUpdated{
          sale{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_sale_updated_webhook(subscription_webhook):
    return subscription_webhook(
        SALE_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.SALE_UPDATED
    )


SALE_DELETED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on SaleDeleted{
          sale{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_sale_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        SALE_DELETED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.SALE_DELETED
    )


INVOICE_REQUESTED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on InvoiceRequested{
          invoice{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_invoice_requested_webhook(subscription_webhook):
    return subscription_webhook(
        INVOICE_REQUESTED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.INVOICE_REQUESTED
    )


INVOICE_DELETED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on InvoiceDeleted{
          invoice{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_invoice_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        INVOICE_DELETED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.INVOICE_DELETED
    )


INVOICE_SENT_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on InvoiceSent{
          invoice{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_invoice_sent_webhook(subscription_webhook):
    return subscription_webhook(
        INVOICE_SENT_SUBSCRIPTION_QUERY, WebhookEventAsyncType.INVOICE_SENT
    )


FULFILLMENT_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on FulfillmentCreated{
          fulfillment{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_fulfillment_created_webhook(subscription_webhook):
    return subscription_webhook(
        FULFILLMENT_CREATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.FULFILLMENT_CREATED,
    )


FULFILLMENT_CANCELED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on FulfillmentCanceled{
          fulfillment{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_fulfillment_canceled_webhook(subscription_webhook):
    return subscription_webhook(
        FULFILLMENT_CANCELED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.FULFILLMENT_CANCELED,
    )


CUSTOMER_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on CustomerCreated{
          user{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_customer_created_webhook(subscription_webhook):
    return subscription_webhook(
        CUSTOMER_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.CUSTOMER_CREATED
    )


CUSTOMER_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on CustomerUpdated{
          user{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_customer_updated_webhook(subscription_webhook):
    return subscription_webhook(
        CUSTOMER_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.CUSTOMER_UPDATED
    )


COLLECTION_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on CollectionCreated{
          collection{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_collection_created_webhook(subscription_webhook):
    return subscription_webhook(
        COLLECTION_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.COLLECTION_CREATED
    )


COLLECTION_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on CollectionUpdated{
          collection{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_collection_updated_webhook(subscription_webhook):
    return subscription_webhook(
        COLLECTION_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.COLLECTION_UPDATED
    )


COLLECTION_DELETED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on CollectionDeleted{
          collection{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_collection_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        COLLECTION_DELETED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.COLLECTION_DELETED
    )


CHECKOUT_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on CheckoutCreated{
          checkout{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_checkout_created_webhook(subscription_webhook):
    return subscription_webhook(
        CHECKOUT_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.CHECKOUT_CREATED
    )


CHECKOUT_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on CheckoutUpdated{
          checkout{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_checkout_updated_webhook(subscription_webhook):
    return subscription_webhook(
        CHECKOUT_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.CHECKOUT_UPDATED
    )


PAGE_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on PageCreated{
          page{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_page_created_webhook(subscription_webhook):
    return subscription_webhook(
        PAGE_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.PAGE_CREATED
    )


PAGE_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on PageUpdated{
          page{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_page_updated_webhook(subscription_webhook):
    return subscription_webhook(
        PAGE_UPDATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.PAGE_UPDATED,
    )


PAGE_DELETED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on PageDeleted{
          page{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_page_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        PAGE_DELETED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.PAGE_DELETED,
    )


MULTIPLE_EVENTS_SUBSCRIPTION_QUERY = """
subscription{
  event{
    ...on ProductCreated{
      product{
        id
      }
    }
    ...on ProductUpdated{
      product{
        id
      }
    }
    ...on OrderCreated{
      order{
        id
      }
    }
  }
}
"""


@pytest.fixture
def subscription_product_created_multiple_events_webhook(subscription_webhook):
    return subscription_webhook(
        MULTIPLE_EVENTS_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.TRANSLATION_CREATED,
    )


TRANSLATION_CREATED_SUBSCRIPTION_QUERY = """
subscription {
  event {
    ... on TranslationCreated {
      translation {
        ... on ProductTranslation {
          id
        }
        ... on CollectionTranslation {
          id
        }
        ... on CategoryTranslation {
          id
        }
        ... on AttributeTranslation {
          id
        }
        ... on ProductVariantTranslation {
          id
        }
        ... on PageTranslation {
          id
        }
        ... on ShippingMethodTranslation {
          id
        }
        ... on SaleTranslation {
          id
        }
        ... on VoucherTranslation {
          id
        }
        ... on MenuItemTranslation {
          id
        }
        ... on AttributeValueTranslation {
          id
        }
      }
    }
  }
}
"""


@pytest.fixture
def subscription_translation_created_webhook(subscription_webhook):
    return subscription_webhook(
        TRANSLATION_CREATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.TRANSLATION_CREATED,
    )


TRANSLATION_UPDATED_SUBSCRIPTION_QUERY = """
subscription {
  event {
    ... on TranslationUpdated {
      translation {
        ... on ProductTranslation {
          id
        }
        ... on CollectionTranslation {
          id
        }
        ... on CategoryTranslation {
          id
        }
        ... on AttributeTranslation {
          id
        }
        ... on ProductVariantTranslation {
          id
        }
        ... on PageTranslation {
          id
        }
        ... on ShippingMethodTranslation {
          id
        }
        ... on SaleTranslation {
          id
        }
        ... on VoucherTranslation {
          id
        }
        ... on MenuItemTranslation {
          id
        }
        ... on AttributeValueTranslation {
          id
        }
      }
    }
  }
}
"""


@pytest.fixture
def subscription_translation_updated_webhook(subscription_webhook):
    return subscription_webhook(
        TRANSLATION_UPDATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
    )
