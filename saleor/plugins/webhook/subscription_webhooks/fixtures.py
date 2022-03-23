import pytest

from saleor.webhook.event_types import WebhookEventAsyncType
from saleor.webhook.models import Webhook

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
def subscription_product_updated_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription product webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=PRODUCT_UPDATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.PRODUCT_UPDATED)
    return webhook


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
def subscription_product_created_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription product webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=PRODUCT_CREATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.PRODUCT_CREATED)
    return webhook


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
def subscription_product_deleted_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription product webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=PRODUCT_DELETED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.PRODUCT_DELETED)
    return webhook


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
def subscription_product_variant_created_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription product variant webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=PRODUCT_VARIANT_CREATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.PRODUCT_VARIANT_CREATED)
    return webhook


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
def subscription_product_variant_updated_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription product variant webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=PRODUCT_VARIANT_UPDATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED)
    return webhook


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
def subscription_product_variant_deleted_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription product variant webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=PRODUCT_VARIANT_DELETED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.PRODUCT_VARIANT_DELETED)
    return webhook


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
def subscription_product_variant_out_of_stock_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription product variant webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=PRODUCT_VARIANT_OUT_OF_STOCK_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK)
    return webhook


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
def subscription_product_variant_back_in_stock_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription product variant webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=PRODUCT_VARIANT_BACK_IN_STOCK_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(
        event_type=WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK
    )
    return webhook


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
def subscription_order_created_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription order webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=ORDER_CREATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CREATED)
    return webhook


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
def subscription_order_updated_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription order webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=ORDER_UPDATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_UPDATED)
    return webhook


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
def subscription_order_confirmed_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription order webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=ORDER_CONFIRMED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CONFIRMED)
    return webhook


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
def subscription_order_fully_paid_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription order webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=ORDER_FULLY_PAID_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_FULLY_PAID)
    return webhook


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
def subscription_order_cancelled_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription order webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=ORDER_CANCELLED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CANCELLED)
    return webhook


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
def subscription_order_fulfilled_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription order webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=ORDER_FULFILLED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_FULFILLED)
    return webhook


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
def subscription_draft_order_created_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription draft order webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=DRAFT_ORDER_CREATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.DRAFT_ORDER_CREATED)
    return webhook


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
def subscription_draft_order_updated_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription draft order webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=DRAFT_ORDER_UPDATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.DRAFT_ORDER_UPDATED)
    return webhook


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
def subscription_draft_order_deleted_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription draft order webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=DRAFT_ORDER_DELETED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.DRAFT_ORDER_DELETED)
    return webhook


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
def subscription_sale_created_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription sale webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=SALE_CREATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.SALE_CREATED)
    return webhook


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
def subscription_sale_updated_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription sale webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=SALE_UPDATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.SALE_UPDATED)
    return webhook


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
def subscription_sale_deleted_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription sale webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=SALE_DELETED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.SALE_DELETED)
    return webhook


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
def subscription_invoice_requested_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription invoice webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=INVOICE_REQUESTED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.INVOICE_REQUESTED)
    return webhook


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
def subscription_invoice_deleted_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription invoice webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=INVOICE_DELETED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.INVOICE_DELETED)
    return webhook


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
def subscription_invoice_sent_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription invoice webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=INVOICE_SENT_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.INVOICE_SENT)
    return webhook


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
def subscription_fulfillment_created_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription fulfillment webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=FULFILLMENT_CREATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.FULFILLMENT_CREATED)
    return webhook


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
def subscription_fulfillment_canceled_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription fulfillment webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=FULFILLMENT_CANCELED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.FULFILLMENT_CANCELED)
    return webhook


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
def subscription_customer_created_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription customer webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=CUSTOMER_CREATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.CUSTOMER_CREATED)
    return webhook


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
def subscription_customer_updated_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription customer webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=CUSTOMER_UPDATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.CUSTOMER_UPDATED)
    return webhook


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
def subscription_collection_created_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription collection webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=COLLECTION_CREATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.COLLECTION_CREATED)
    return webhook


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
def subscription_collection_updated_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription collection webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=COLLECTION_UPDATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.COLLECTION_UPDATED)
    return webhook


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
def subscription_collection_deleted_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription collection webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=COLLECTION_DELETED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.COLLECTION_DELETED)
    return webhook


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
def subscription_checkout_created_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription checkout webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=CHECKOUT_CREATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.CHECKOUT_CREATED)
    return webhook


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
def subscription_checkout_updated_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription checkout webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=CHECKOUT_UPDATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.CHECKOUT_UPDATED)
    return webhook


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
def subscription_page_created_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription page webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=PAGE_CREATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.PAGE_CREATED)
    return webhook


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
def subscription_page_updated_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription page webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=PAGE_UPDATED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.PAGE_UPDATED)
    return webhook


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
def subscription_page_deleted_webhook(app):
    webhook = Webhook.objects.create(
        name="Subscription page webhook",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=PAGE_DELETED_SUBSCRIPTION_QUERY,
    )
    webhook.events.create(event_type=WebhookEventAsyncType.PAGE_DELETED)
    return webhook
