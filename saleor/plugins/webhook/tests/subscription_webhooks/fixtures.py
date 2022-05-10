import pytest

from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.models import Webhook


@pytest.fixture
def subscription_webhook(webhook_app):
    def fun(query, event_type, name="Subscription"):
        webhook = Webhook.objects.create(
            name=name,
            app=webhook_app,
            target_url="http://www.example.com/any",
            subscription_query=query,
        )
        webhook.events.create(event_type=event_type)
        return webhook

    return fun


APP_DETAILS_FRAGMENT = """
    fragment AppDetails on App{
        id
        isActive
        name
        appUrl
    }
"""


APP_CREATED_SUBSCRIPTION_QUERY = (
    APP_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on AppCreated{
          app{
            ...AppDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_app_created_webhook(subscription_webhook):
    return subscription_webhook(
        APP_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.APP_CREATED
    )


APP_UPDATED_SUBSCRIPTION_QUERY = (
    APP_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on AppUpdated{
          app{
            ...AppDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_app_updated_webhook(subscription_webhook):
    return subscription_webhook(
        APP_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.APP_UPDATED
    )


APP_DELETED_SUBSCRIPTION_QUERY = (
    APP_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on AppDeleted{
          app{
            ...AppDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_app_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        APP_DELETED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.APP_DELETED
    )


APP_STATUS_CHANGED_SUBSCRIPTION_QUERY = (
    APP_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on AppStatusChanged{
          app{
            ...AppDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_app_status_changed_webhook(subscription_webhook):
    return subscription_webhook(
        APP_STATUS_CHANGED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.APP_STATUS_CHANGED,
    )


CATEGORY_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on CategoryCreated{
          category{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_category_created_webhook(subscription_webhook):
    return subscription_webhook(
        CATEGORY_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.CATEGORY_CREATED
    )


CATEGORY_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on CategoryUpdated{
          category{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_category_updated_webhook(subscription_webhook):
    return subscription_webhook(
        CATEGORY_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.CATEGORY_UPDATED
    )


CATEGORY_DELETED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on CategoryDeleted{
          category{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_category_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        CATEGORY_DELETED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.CATEGORY_DELETED
    )


CHANNEL_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ChannelCreated{
          channel{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_channel_created_webhook(subscription_webhook):
    return subscription_webhook(
        CHANNEL_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.CHANNEL_CREATED
    )


CHANNEL_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ChannelUpdated{
          channel{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_channel_updated_webhook(subscription_webhook):
    return subscription_webhook(
        CHANNEL_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.CHANNEL_UPDATED
    )


CHANNEL_DELETED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ChannelDeleted{
          channel{
            id
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_channel_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        CHANNEL_DELETED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.CHANNEL_DELETED
    )


CHANNEL_STATUS_CHANGED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ChannelStatusChanged{
          channel{
            id
            isActive
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_channel_status_changed_webhook(subscription_webhook):
    return subscription_webhook(
        CHANNEL_STATUS_CHANGED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.CHANNEL_STATUS_CHANGED,
    )


GIFT_CARD_DETAILS_FRAGMENT = """
    fragment GiftCardDetails on GiftCard{
        id
        isActive
        code
        createdBy {
            email
        }
    }
"""

GIFT_CARD_CREATED_SUBSCRIPTION_QUERY = (
    GIFT_CARD_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on GiftCardCreated{
          giftCard{
            ...GiftCardDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_gift_card_created_webhook(subscription_webhook):
    return subscription_webhook(
        GIFT_CARD_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.GIFT_CARD_CREATED
    )


GIFT_CARD_UPDATED_SUBSCRIPTION_QUERY = (
    GIFT_CARD_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on GiftCardUpdated{
          giftCard{
            ...GiftCardDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_gift_card_updated_webhook(subscription_webhook):
    return subscription_webhook(
        GIFT_CARD_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.GIFT_CARD_UPDATED
    )


GIFT_CARD_DELETED_SUBSCRIPTION_QUERY = (
    GIFT_CARD_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on GiftCardDeleted{
          giftCard{
            ...GiftCardDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_gift_card_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        GIFT_CARD_DELETED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.GIFT_CARD_DELETED
    )


GIFT_CARD_STATUS_CHANGED_SUBSCRIPTION_QUERY = (
    GIFT_CARD_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on GiftCardStatusChanged{
          giftCard{
            ...GiftCardDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_gift_card_status_changed_webhook(subscription_webhook):
    return subscription_webhook(
        GIFT_CARD_STATUS_CHANGED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED,
    )


MENU_DETAILS_FRAGMENT = """
    fragment MenuDetails on Menu{
        id
        name
        slug
        items {
            id
            name
        }
    }
"""

MENU_CREATED_SUBSCRIPTION_QUERY = (
    MENU_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on MenuCreated{
          menu{
            ...MenuDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_menu_created_webhook(subscription_webhook):
    return subscription_webhook(
        MENU_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.MENU_CREATED
    )


MENU_UPDATED_SUBSCRIPTION_QUERY = (
    MENU_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on MenuUpdated{
          menu{
            ...MenuDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_menu_updated_webhook(subscription_webhook):
    return subscription_webhook(
        MENU_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.MENU_UPDATED
    )


MENU_DELETED_SUBSCRIPTION_QUERY = (
    MENU_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on MenuDeleted{
          menu{
            ...MenuDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_menu_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        MENU_DELETED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.MENU_DELETED
    )


MENU_ITEM_DETAILS_FRAGMENT = """
    fragment MenuItemDetails on MenuItem{
        id
        name
        menu {
            id
        }
        page {
            id
        }
    }
"""

MENU_ITEM_CREATED_SUBSCRIPTION_QUERY = (
    MENU_ITEM_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on MenuItemCreated{
          menuItem{
            ...MenuItemDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_menu_item_created_webhook(subscription_webhook):
    return subscription_webhook(
        MENU_ITEM_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.MENU_ITEM_CREATED
    )


MENU_ITEM_UPDATED_SUBSCRIPTION_QUERY = (
    MENU_ITEM_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on MenuItemUpdated{
          menuItem{
            ...MenuItemDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_menu_item_updated_webhook(subscription_webhook):
    return subscription_webhook(
        MENU_ITEM_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.MENU_ITEM_UPDATED
    )


MENU_ITEM_DELETED_SUBSCRIPTION_QUERY = (
    MENU_ITEM_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on MenuItemDeleted{
          menuItem{
            ...MenuItemDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_menu_item_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        MENU_ITEM_DELETED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.MENU_ITEM_DELETED
    )


SHIPPING_PRICE_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ShippingPriceCreated{
          shippingMethod{
            id
            name
            channelListings {
              channel {
                name
              }
            }
          }
          shippingZone{
            id
            name
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_shipping_price_created_webhook(subscription_webhook):
    return subscription_webhook(
        SHIPPING_PRICE_CREATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.SHIPPING_PRICE_CREATED,
    )


SHIPPING_PRICE_UPDATED_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ShippingPriceUpdated{
          shippingMethod{
            id
            name
            channelListings {
              channel {
                name
              }
            }
          }
          shippingZone{
            id
            name
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_shipping_price_updated_webhook(subscription_webhook):
    return subscription_webhook(
        SHIPPING_PRICE_UPDATED_UPDATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.SHIPPING_PRICE_UPDATED,
    )


SHIPPING_PRICE_DELETED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ShippingPriceDeleted{
          shippingMethod{
            id
            name
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_shipping_price_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        SHIPPING_PRICE_DELETED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.SHIPPING_PRICE_DELETED,
    )


SHIPPING_ZONE_CREATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ShippingZoneCreated{
          shippingZone{
            id
            name
            countries {
                code
            }
            channels {
                name
            }
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_shipping_zone_created_webhook(subscription_webhook):
    return subscription_webhook(
        SHIPPING_ZONE_CREATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.SHIPPING_ZONE_CREATED,
    )


SHIPPING_ZONE_UPDATED_UPDATED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ShippingZoneUpdated{
          shippingZone{
            id
            name
            countries {
                code
            }
            channels {
                name
            }
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_shipping_zone_updated_webhook(subscription_webhook):
    return subscription_webhook(
        SHIPPING_ZONE_UPDATED_UPDATED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.SHIPPING_ZONE_UPDATED,
    )


SHIPPING_ZONE_DELETED_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ShippingZoneDeleted{
          shippingZone{
            id
            name
          }
        }
      }
    }
"""


@pytest.fixture
def subscription_shipping_zone_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        SHIPPING_ZONE_DELETED_SUBSCRIPTION_QUERY,
        WebhookEventAsyncType.SHIPPING_ZONE_DELETED,
    )


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


VOUCHER_DETAILS_FRAGMENT = """
    fragment VoucherDetails on Voucher{
        id
        name
        code
        usageLimit
    }
"""

VOUCHER_CREATED_SUBSCRIPTION_QUERY = (
    VOUCHER_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on VoucherCreated{
          voucher{
            ...VoucherDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_voucher_created_webhook(subscription_webhook):
    return subscription_webhook(
        VOUCHER_CREATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.VOUCHER_CREATED
    )


VOUCHER_UPDATED_SUBSCRIPTION_QUERY = (
    VOUCHER_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on VoucherUpdated{
          voucher{
            ...VoucherDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_voucher_updated_webhook(subscription_webhook):
    return subscription_webhook(
        VOUCHER_UPDATED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.VOUCHER_UPDATED
    )


VOUCHER_DELETED_SUBSCRIPTION_QUERY = (
    VOUCHER_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on VoucherDeleted{
          voucher{
            ...VoucherDetails
          }
        }
      }
    }
"""
)


@pytest.fixture
def subscription_voucher_deleted_webhook(subscription_webhook):
    return subscription_webhook(
        VOUCHER_DELETED_SUBSCRIPTION_QUERY, WebhookEventAsyncType.VOUCHER_DELETED
    )
