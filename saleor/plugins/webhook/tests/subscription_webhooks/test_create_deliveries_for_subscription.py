import json
from unittest.mock import patch

import graphene

from .....graphql.webhook.subscription_payload import validate_subscription_query
from .....webhook.event_types import WebhookEventAsyncType
from ...tasks import create_deliveries_for_subscriptions, logger


def test_product_created(product, subscription_product_created_webhook):
    webhooks = [subscription_product_created_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_CREATED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps([{"product": {"id": product_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_updated(product, subscription_product_updated_webhook):
    webhooks = [subscription_product_updated_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_UPDATED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps([{"product": {"id": product_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_deleted(product, subscription_product_deleted_webhook):
    webhooks = [subscription_product_deleted_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_DELETED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps([{"product": {"id": product_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_created(variant, subscription_product_variant_created_webhook):
    webhooks = [subscription_product_variant_created_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_CREATED
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, variant, webhooks)
    expected_payload = json.dumps(
        [{"productVariant": {"id": variant_id}, "meta": None}]
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_updated(variant, subscription_product_variant_updated_webhook):
    webhooks = [subscription_product_variant_updated_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, variant, webhooks)
    expected_payload = json.dumps(
        [{"productVariant": {"id": variant_id}, "meta": None}]
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_deleted(variant, subscription_product_variant_deleted_webhook):
    webhooks = [subscription_product_variant_deleted_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_DELETED
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, variant, webhooks)
    expected_payload = json.dumps(
        [{"productVariant": {"id": variant_id}, "meta": None}]
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_out_of_stock(
    stock, subscription_product_variant_out_of_stock_webhook
):
    webhooks = [subscription_product_variant_out_of_stock_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK
    variant_id = graphene.Node.to_global_id("ProductVariant", stock.product_variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, stock, webhooks)
    expected_payload = json.dumps(
        [{"productVariant": {"id": variant_id}, "meta": None}]
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_back_in_stock(
    stock, subscription_product_variant_back_in_stock_webhook
):
    webhooks = [subscription_product_variant_back_in_stock_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK
    variant_id = graphene.Node.to_global_id("ProductVariant", stock.product_variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, stock, webhooks)
    expected_payload = json.dumps(
        [{"productVariant": {"id": variant_id}, "meta": None}]
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_created(order, subscription_order_created_webhook):
    webhooks = [subscription_order_created_webhook]
    event_type = WebhookEventAsyncType.ORDER_CREATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps([{"order": {"id": order_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_confirmed(order, subscription_order_confirmed_webhook):
    webhooks = [subscription_order_confirmed_webhook]
    event_type = WebhookEventAsyncType.ORDER_CONFIRMED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps([{"order": {"id": order_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_fully_paid(order, subscription_order_fully_paid_webhook):
    webhooks = [subscription_order_fully_paid_webhook]
    event_type = WebhookEventAsyncType.ORDER_FULLY_PAID
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps([{"order": {"id": order_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_updated(order, subscription_order_updated_webhook):
    webhooks = [subscription_order_updated_webhook]
    event_type = WebhookEventAsyncType.ORDER_UPDATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps([{"order": {"id": order_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_cancelled(order, subscription_order_cancelled_webhook):
    webhooks = [subscription_order_cancelled_webhook]
    event_type = WebhookEventAsyncType.ORDER_CANCELLED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps([{"order": {"id": order_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_fulfilled(order, subscription_order_fulfilled_webhook):
    webhooks = [subscription_order_fulfilled_webhook]
    event_type = WebhookEventAsyncType.ORDER_FULFILLED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps([{"order": {"id": order_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_draft_order_created(order, subscription_draft_order_created_webhook):
    webhooks = [subscription_draft_order_created_webhook]
    event_type = WebhookEventAsyncType.DRAFT_ORDER_CREATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps([{"order": {"id": order_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_draft_order_updated(order, subscription_draft_order_updated_webhook):
    webhooks = [subscription_draft_order_updated_webhook]
    event_type = WebhookEventAsyncType.DRAFT_ORDER_UPDATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps([{"order": {"id": order_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_draft_order_deleted(order, subscription_draft_order_deleted_webhook):
    webhooks = [subscription_draft_order_deleted_webhook]
    event_type = WebhookEventAsyncType.DRAFT_ORDER_DELETED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps([{"order": {"id": order_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_sale_created(sale, subscription_sale_created_webhook):
    webhooks = [subscription_sale_created_webhook]
    event_type = WebhookEventAsyncType.SALE_CREATED
    sale_id = graphene.Node.to_global_id("Sale", sale.id)
    deliveries = create_deliveries_for_subscriptions(event_type, sale, webhooks)
    expected_payload = json.dumps([{"sale": {"id": sale_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_sale_updated(sale, subscription_sale_updated_webhook):
    webhooks = [subscription_sale_updated_webhook]
    event_type = WebhookEventAsyncType.SALE_UPDATED
    sale_id = graphene.Node.to_global_id("Sale", sale.id)
    deliveries = create_deliveries_for_subscriptions(event_type, sale, webhooks)
    expected_payload = json.dumps([{"sale": {"id": sale_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_sale_deleted(sale, subscription_sale_deleted_webhook):
    webhooks = [subscription_sale_deleted_webhook]
    event_type = WebhookEventAsyncType.SALE_DELETED
    sale_id = graphene.Node.to_global_id("Sale", sale.id)
    deliveries = create_deliveries_for_subscriptions(event_type, sale, webhooks)
    expected_payload = json.dumps([{"sale": {"id": sale_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_invoice_requested(fulfilled_order, subscription_invoice_requested_webhook):
    webhooks = [subscription_invoice_requested_webhook]
    event_type = WebhookEventAsyncType.INVOICE_REQUESTED
    invoice = fulfilled_order.invoices.first()
    invoice_id = graphene.Node.to_global_id("Invoice", invoice.id)
    deliveries = create_deliveries_for_subscriptions(event_type, invoice, webhooks)
    expected_payload = json.dumps([{"invoice": {"id": invoice_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_invoice_deleted(fulfilled_order, subscription_invoice_deleted_webhook):
    webhooks = [subscription_invoice_deleted_webhook]
    event_type = WebhookEventAsyncType.INVOICE_DELETED
    invoice = fulfilled_order.invoices.first()
    invoice_id = graphene.Node.to_global_id("Invoice", invoice.id)
    deliveries = create_deliveries_for_subscriptions(event_type, invoice, webhooks)
    expected_payload = json.dumps([{"invoice": {"id": invoice_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_invoice_sent(fulfilled_order, subscription_invoice_sent_webhook):
    webhooks = [subscription_invoice_sent_webhook]
    event_type = WebhookEventAsyncType.INVOICE_SENT
    invoice = fulfilled_order.invoices.first()
    invoice_id = graphene.Node.to_global_id("Invoice", invoice.id)
    deliveries = create_deliveries_for_subscriptions(event_type, invoice, webhooks)
    expected_payload = json.dumps([{"invoice": {"id": invoice_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_fulfillment_created(fulfillment, subscription_fulfillment_created_webhook):
    webhooks = [subscription_fulfillment_created_webhook]
    event_type = WebhookEventAsyncType.FULFILLMENT_CREATED
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    deliveries = create_deliveries_for_subscriptions(event_type, fulfillment, webhooks)
    expected_payload = json.dumps(
        [{"fulfillment": {"id": fulfillment_id}, "meta": None}]
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_fulfillment_canceled(fulfillment, subscription_fulfillment_canceled_webhook):
    webhooks = [subscription_fulfillment_canceled_webhook]
    event_type = WebhookEventAsyncType.FULFILLMENT_CANCELED
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)
    deliveries = create_deliveries_for_subscriptions(event_type, fulfillment, webhooks)
    expected_payload = json.dumps(
        [{"fulfillment": {"id": fulfillment_id}, "meta": None}]
    )

    assert deliveries[0].payload.payload == expected_payload

    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_customer_created(customer_user, subscription_customer_created_webhook):
    webhooks = [subscription_customer_created_webhook]
    event_type = WebhookEventAsyncType.CUSTOMER_CREATED
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, customer_user, webhooks
    )
    expected_payload = json.dumps([{"user": {"id": user_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_customer_updated(customer_user, subscription_customer_updated_webhook):
    webhooks = [subscription_customer_updated_webhook]
    event_type = WebhookEventAsyncType.CUSTOMER_UPDATED
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, customer_user, webhooks
    )
    expected_payload = json.dumps([{"user": {"id": user_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_collection_created(collection, subscription_collection_created_webhook):
    webhooks = [subscription_collection_created_webhook]
    event_type = WebhookEventAsyncType.COLLECTION_CREATED
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    deliveries = create_deliveries_for_subscriptions(event_type, collection, webhooks)
    expected_payload = json.dumps([{"collection": {"id": collection_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_collection_updated(collection, subscription_collection_updated_webhook):
    webhooks = [subscription_collection_updated_webhook]
    event_type = WebhookEventAsyncType.COLLECTION_UPDATED
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    deliveries = create_deliveries_for_subscriptions(event_type, collection, webhooks)
    expected_payload = json.dumps([{"collection": {"id": collection_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_collection_deleted(collection, subscription_collection_deleted_webhook):
    webhooks = [subscription_collection_deleted_webhook]
    event_type = WebhookEventAsyncType.COLLECTION_DELETED
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    deliveries = create_deliveries_for_subscriptions(event_type, collection, webhooks)
    expected_payload = json.dumps([{"collection": {"id": collection_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_checkout_create(checkout, subscription_checkout_created_webhook):
    webhooks = [subscription_checkout_created_webhook]
    event_type = WebhookEventAsyncType.CHECKOUT_CREATED
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)
    expected_payload = json.dumps([{"checkout": {"id": checkout_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_checkout_update(checkout, subscription_checkout_updated_webhook):
    webhooks = [subscription_checkout_updated_webhook]
    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)
    expected_payload = json.dumps([{"checkout": {"id": checkout_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_page_created(page, subscription_page_created_webhook):
    webhooks = [subscription_page_created_webhook]
    event_type = WebhookEventAsyncType.PAGE_CREATED
    page_id = graphene.Node.to_global_id("Page", page.pk)
    deliveries = create_deliveries_for_subscriptions(event_type, page, webhooks)
    expected_payload = json.dumps([{"page": {"id": page_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_page_updated(page, subscription_page_updated_webhook):
    webhooks = [subscription_page_updated_webhook]
    event_type = WebhookEventAsyncType.PAGE_UPDATED
    page_id = graphene.Node.to_global_id("Page", page.pk)
    deliveries = create_deliveries_for_subscriptions(event_type, page, webhooks)
    expected_payload = json.dumps([{"page": {"id": page_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_page_deleted(page, subscription_page_deleted_webhook):
    webhooks = [subscription_page_deleted_webhook]
    event_type = WebhookEventAsyncType.PAGE_DELETED
    page_id = graphene.Node.to_global_id("Page", page.pk)
    deliveries = create_deliveries_for_subscriptions(event_type, page, webhooks)
    expected_payload = json.dumps([{"page": {"id": page_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_created_multiple_events_in_subscription(
    product, subscription_product_created_multiple_events_webhook
):
    webhooks = [subscription_product_created_multiple_events_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_CREATED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps([{"product": {"id": product_id}, "meta": None}])

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


@patch.object(logger, "info")
def test_create_deliveries_for_subscriptions_unsubscribable_event(
    mocked_logger, product, subscription_product_updated_webhook, any_webhook
):
    webhooks = [subscription_product_updated_webhook]
    event_type = "unsubscribable_type"

    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)

    mocked_logger.assert_called_with(
        "Skipping subscription webhook. Event %s is not subscribable.", event_type
    )
    assert len(deliveries) == 0


TEST_VALID_SUBSCRIPTION_QUERY = """
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


def test_validate_subscription_query_valid():
    result = validate_subscription_query(TEST_VALID_SUBSCRIPTION_QUERY)
    assert result is True


def test_validate_subscription_query_invalid():

    result = validate_subscription_query("invalid_query")
    assert result is False


TEST_VALID_SUBSCRIPTION_QUERY_WITH_FRAGMENT = """
fragment productFragment on Product{
  name
}
subscription{
  event{
    ...on ProductUpdated{
      product{
        id
        ...productFragment
      }
    }
  }
}
"""


def test_validate_subscription_query_valid_with_fragment():

    result = validate_subscription_query(TEST_VALID_SUBSCRIPTION_QUERY_WITH_FRAGMENT)
    assert result is True


TEST_INVALID_MULTIPLE_QUERY_AND_SUBSCRIPTION = """
query{
  products(first:100){
    edges{
      node{
        id
      }
    }
  }
}
subscription{
  event{
    ...on ProductUpdated{
      product{
        id
      }
    }
  }
}"""


def test_validate_invalid_query_and_subscription():

    result = validate_subscription_query(TEST_INVALID_MULTIPLE_QUERY_AND_SUBSCRIPTION)
    assert result is False


TEST_INVALID_MULTIPLE_SUBSCRIPTION_AND_QUERY = """
subscription{
  event{
    ...on ProductUpdated{
      product{
        id
      }
    }
  }
}
query{
  products(first:100){
    edges{
      node{
        id
      }
    }
  }
}
"""


def test_validate_invalid_subscription_and_query():

    result = validate_subscription_query(TEST_INVALID_MULTIPLE_SUBSCRIPTION_AND_QUERY)
    assert result is False


TEST_INVALID_MULTIPLE_SUBSCRIPTION = """
subscription{
  event{
    ...on ProductUpdated{
      product{
        id
      }
    }
  }
}
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


def test_validate_invalid_multiple_subscriptions():

    result = validate_subscription_query(TEST_INVALID_MULTIPLE_SUBSCRIPTION)
    assert result is False
