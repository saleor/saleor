from enum import Enum

from graphene.utils.str_converters import to_snake_case

from ....graphql.tests.queries import fragments
from ....graphql.webhook.subscription_types import TRANSLATIONS_TYPES_MAP

ACCOUNT_CONFIRMATION_REQUESTED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on AccountConfirmationRequested{
          user{
            ...CustomerDetails
          }
          token
          redirectUrl
          channel{
            slug
            id
          }
          shop{
            domain{
                host
                url
            }
          }
        }
      }
    }
"""
)

ACCOUNT_CONFIRMED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on AccountConfirmed{
          user{
            ...CustomerDetails
          }
        }
      }
    }
"""
)


ACCOUNT_CHANGE_EMAIL_REQUESTED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on AccountChangeEmailRequested{
          user{
            ...CustomerDetails
          }
          token
          redirectUrl
          channel{
            slug
            id
          }
          shop{
            domain{
                host
                url
            }
          }
          newEmail
        }
      }
    }
"""
)


ACCOUNT_EMAIL_CHANGED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on AccountEmailChanged{
          user{
            ...CustomerDetails
          }
        }
      }
    }
"""
)


ACCOUNT_DELETE_REQUESTED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on AccountDeleteRequested{
          user{
            ...CustomerDetails
          }
          token
          redirectUrl
          channel{
            slug
            id
          }
          shop{
            domain{
                host
                url
            }
          }
        }
      }
    }
"""
)

ACCOUNT_SET_PASSWORD_REQUESTED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on AccountSetPasswordRequested{
          user{
            ...CustomerDetails
          }
          token
          redirectUrl
          channel{
            slug
            id
          }
          shop{
            domain{
                host
                url
            }
          }
        }
      }
    }
"""
)

ACCOUNT_DELETED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on AccountDeleted{
          user{
            ...CustomerDetails
          }
        }
      }
    }
"""
)


ADDRESS_CREATED = (
    fragments.ADDRESS_DETAILS
    + """
    subscription{
      event{
        ...on AddressCreated{
          address{
            ...AddressDetails
          }
        }
      }
    }
"""
)


ADDRESS_UPDATED = (
    fragments.ADDRESS_DETAILS
    + """
    subscription{
      event{
        ...on AddressUpdated{
          address{
            ...AddressDetails
          }
        }
      }
    }
"""
)


ADDRESS_DELETED = (
    fragments.ADDRESS_DETAILS
    + """
    subscription{
      event{
        ...on AddressDeleted{
          address{
            ...AddressDetails
          }
        }
      }
    }
"""
)

APP_INSTALLED = (
    fragments.APP_DETAILS
    + """
    subscription{
      event{
        ...on AppInstalled{
          app{
            ...AppDetails
          }
        }
      }
    }
"""
)

APP_UPDATED = (
    fragments.APP_DETAILS
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


APP_DELETED = (
    fragments.APP_DETAILS
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


APP_STATUS_CHANGED = (
    fragments.APP_DETAILS
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


ATTRIBUTE_CREATED = (
    fragments.ATTRIBUTE_DETAILS
    + """
    subscription{
      event{
        ...on AttributeCreated{
          attribute{
            ...AttributeDetails
          }
        }
      }
    }
"""
)


ATTRIBUTE_UPDATED = (
    fragments.ATTRIBUTE_DETAILS
    + """
    subscription{
      event{
        ...on AttributeUpdated{
          attribute{
            ...AttributeDetails
          }
        }
      }
    }
"""
)


ATTRIBUTE_DELETED = (
    fragments.ATTRIBUTE_DETAILS
    + """
    subscription{
      event{
        ...on AttributeDeleted{
          attribute{
            ...AttributeDetails
          }
        }
      }
    }
"""
)


ATTRIBUTE_VALUE_CREATED = (
    fragments.ATTRIBUTE_VALUE_DETAILS
    + """
    subscription{
      event{
        ...on AttributeValueCreated{
          attributeValue{
            ...AttributeValueDetails
          }
        }
      }
    }
"""
)


ATTRIBUTE_VALUE_UPDATED = (
    fragments.ATTRIBUTE_VALUE_DETAILS
    + """
    subscription{
      event{
        ...on AttributeValueUpdated{
          attributeValue{
            ...AttributeValueDetails
          }
        }
      }
    }
"""
)


ATTRIBUTE_VALUE_DELETED = (
    fragments.ATTRIBUTE_VALUE_DETAILS
    + """
    subscription{
      event{
        ...on AttributeValueDeleted{
          attributeValue{
            ...AttributeValueDetails
          }
        }
      }
    }
"""
)


GIFT_CARD_CREATED = (
    fragments.GIFT_CARD_DETAILS
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


GIFT_CARD_UPDATED = (
    fragments.GIFT_CARD_DETAILS
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

GIFT_CARD_DELETED = (
    fragments.GIFT_CARD_DETAILS
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


GIFT_CARD_SENT = (
    fragments.GIFT_CARD_DETAILS
    + """
    subscription{
      event{
        ...on GiftCardSent {
          giftCard{
            ...GiftCardDetails
          }
          channel
          sentToEmail
        }
      }
    }
"""
)


GIFT_CARD_STATUS_CHANGED = (
    fragments.GIFT_CARD_DETAILS
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

GIFT_CARD_METADATA_UPDATED = (
    fragments.GIFT_CARD_DETAILS
    + """
    subscription{
      event{
        ...on GiftCardMetadataUpdated{
          giftCard{
            ...GiftCardDetails
          }
        }
      }
    }
"""
)

GIFT_CARD_EXPORT_COMPLETED = (
    fragments.GIFT_CARD_EXPORT_DETAILS
    + """
    subscription{
      event{
        ...on GiftCardExportCompleted{
          export{
            ...GiftCardExportDetails
          }
        }
      }
    }
"""
)

VOUCHER_CREATED = (
    fragments.VOUCHER_DETAILS
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


VOUCHER_CREATED_WITH_META = (
    fragments.VOUCHER_DETAILS
    + """
    subscription{
      event{
        __typename
        issuedAt
        version
        issuingPrincipal{
          __typename
          ...on App{
            id
            name
          }
          ...on User{
            id
            email
          }
        }
        recipient{
          id
          name
        }
        ...on VoucherCreated{
          voucher{
            ...VoucherDetails
          }
        }
      }
    }
"""
)

VOUCHER_UPDATED = (
    fragments.VOUCHER_DETAILS
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


VOUCHER_DELETED = (
    fragments.VOUCHER_DETAILS
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


VOUCHER_CODES_CREATED = (
    fragments.VOUCHER_CODE_DETAILS
    + """
    subscription{
      event{
        ...on VoucherCodesCreated{
          voucherCodes{
            ...VoucherCodeDetails
          }
        }
      }
    }
"""
)


VOUCHER_CODES_DELETED = (
    fragments.VOUCHER_CODE_DETAILS
    + """
    subscription{
      event{
        ...on VoucherCodesDeleted{
          voucherCodes{
            ...VoucherCodeDetails
          }
        }
      }
    }
"""
)


VOUCHER_METADATA_UPDATED = (
    fragments.VOUCHER_DETAILS
    + """
    subscription{
      event{
        ...on VoucherMetadataUpdated{
          voucher{
            ...VoucherDetails
          }
        }
      }
    }
"""
)


VOUCHER_CODE_EXPORT_COMPLETED = (
    fragments.VOUCHER_CODE_EXPORT_DETAILS
    + """
    subscription{
      event{
        ...on VoucherCodeExportCompleted{
          export{
            ...VoucherCodeExportDetails
          }
        }
      }
    }
"""
)


SHOP_METADATA_UPDATED = """
    subscription{
      event {
        ...on ShopMetadataUpdated{
          shop {
            id
          }
        }
      }
    }
"""


CHANNEL_CREATED = """
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

CHANNEL_UPDATED = """
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

CHANNEL_DELETED = """
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

CHANNEL_STATUS_CHANGED = """
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


CATEGORY_CREATED = (
    fragments.CATEGORY_DETAILS
    + """
    subscription{
      event{
        ...on CategoryCreated{
          category{
            ...CategoryDetails
          }
        }
      }
    }
    """
)

CATEGORY_UPDATED = (
    fragments.CATEGORY_DETAILS
    + """
    subscription{
      event{
        ...on CategoryUpdated{
          category{
            ...CategoryDetails
          }
        }
      }
    }
    """
)

CATEGORY_DELETED = """
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


SHIPPING_PRICE_CREATED = (
    fragments.SHIPPING_METHOD_DETAILS
    + """
    subscription{
      event{
        ...on ShippingPriceCreated{
          shippingMethod{
            ...ShippingMethodDetails
          }
          shippingZone{
            id
            name
          }
        }
      }
    }
"""
)

SHIPPING_PRICE_UPDATED_UPDATED = (
    fragments.SHIPPING_METHOD_DETAILS
    + """
    subscription{
      event{
        ...on ShippingPriceUpdated{
          shippingMethod{
            ...ShippingMethodDetails
          }
          shippingZone{
            id
            name
          }
        }
      }
    }
"""
)

SHIPPING_PRICE_DELETED = """
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

SHIPPING_ZONE_CREATED = """
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

SHIPPING_ZONE_UPDATED_UPDATED = """
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

SHIPPING_ZONE_DELETED = """
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

SHIPPING_ZONE_METADATA_UPDATED = """
    subscription{
      event{
        ...on ShippingZoneMetadataUpdated{
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

STAFF_CREATED = (
    fragments.STAFF_DETAILS
    + """
    subscription{
      event{
        ...on StaffCreated{
          user{
            ...StaffDetails
          }
        }
      }
    }
"""
)

STAFF_UPDATED = (
    fragments.STAFF_DETAILS
    + """
    subscription{
      event{
        ...on StaffUpdated{
          user{
            ...StaffDetails
          }
        }
      }
    }
"""
)


STAFF_DELETED = (
    fragments.STAFF_DETAILS
    + """
    subscription{
      event{
        ...on StaffDeleted{
          user{
            ...StaffDetails
          }
        }
      }
    }
"""
)


STAFF_SET_PASSWORD_REQUESTED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on StaffSetPasswordRequested{
          user{
            ...CustomerDetails
          }
          token
          redirectUrl
          channel{
            slug
            id
          }
          shop{
            domain{
                host
                url
            }
          }
        }
      }
    }
"""
)


PRODUCT_UPDATED = """
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

PRODUCT_CREATED = """
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

PRODUCT_DELETED = """
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

PRODUCT_METADATA_UPDATED = """
    subscription{
      event{
        ...on ProductMetadataUpdated{
          product{
            id
          }
        }
      }
    }
"""

PRODUCT_EXPORT_COMPLETED = (
    fragments.PRODUCT_EXPORT_DETAILS
    + """
    subscription{
      event{
        ...on ProductExportCompleted{
          export{
            ...ProductExportDetails
          }
        }
      }
    }
"""
)

PRODUCT_MEDIA_CREATED = """
    subscription{
      event{
        ...on ProductMediaCreated{
          productMedia{
            id
            url(size: 0)
            productId
          }
        }
      }
    }
"""

PRODUCT_MEDIA_UPDATED = """
    subscription{
      event{
        ...on ProductMediaUpdated{
          productMedia{
            id
            url(size: 0)
            productId
          }
        }
      }
    }
"""

PRODUCT_MEDIA_DELETED = """
    subscription{
      event{
        ...on ProductMediaDeleted{
          productMedia{
            id
            url(size: 0)
            productId
          }
        }
      }
    }
"""

PRODUCT_VARIANT_CREATED = """
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

PRODUCT_VARIANT_UPDATED = """
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


PRODUCT_VARIANT_DELETED = """
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

PRODUCT_VARIANT_METADATA_UPDATED = """
    subscription{
      event{
        ...on ProductVariantMetadataUpdated{
          productVariant{
            id
          }
        }
      }
    }
"""

PRODUCT_VARIANT_OUT_OF_STOCK = """
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

PRODUCT_VARIANT_BACK_IN_STOCK = """
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

PRODUCT_VARIANT_STOCK_UPDATED = """
    subscription{
      event{
        ...on ProductVariantStockUpdated{
          productVariant{
            id
          }
          warehouse{
            id
          }
        }
      }
    }
"""

ORDER_CREATED = """
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

ORDER_UPDATED = """
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

ORDER_CONFIRMED = """
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

ORDER_FULLY_PAID = """
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

ORDER_PAID = """
    subscription{
      event{
        ...on OrderPaid{
          order{
            id
          }
        }
      }
    }
"""

ORDER_FULLY_REFUNDED = """
    subscription{
      event{
        ...on OrderFullyRefunded{
          order{
            id
          }
        }
      }
    }
"""

ORDER_REFUNDED = """
    subscription{
      event{
        ...on OrderRefunded{
          order{
            id
          }
        }
      }
    }
"""

ORDER_CANCELLED = """
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


ORDER_EXPIRED = """
    subscription{
      event{
        ...on OrderExpired{
          order{
            id
          }
        }
      }
    }
"""


ORDER_FULFILLED = """
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

ORDER_METADATA_UPDATED = """
    subscription{
      event{
        ...on OrderMetadataUpdated{
          order{
            id
          }
        }
      }
    }
"""

ORDER_BULK_CREATED = """
    subscription{
      event{
        ...on OrderBulkCreated{
          orders{
            id
          }
        }
      }
    }
"""

DRAFT_ORDER_CREATED = """
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

DRAFT_ORDER_UPDATED = """
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

DRAFT_ORDER_DELETED = """
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

SALE_CREATED = (
    fragments.SALE_DETAILS
    + """
    subscription{
      event{
        ...on SaleCreated{
          sale{
            ...SaleDetails
          }
        }
      }
    }
"""
)

SALE_UPDATED = (
    fragments.SALE_DETAILS
    + """
    subscription{
      event{
        ...on SaleUpdated{
          sale{
            ...SaleDetails
          }
        }
      }
    }
"""
)

SALE_DELETED = (
    fragments.SALE_DETAILS
    + """
    subscription{
      event{
        ...on SaleDeleted{
          sale{
            ...SaleDetails
          }
        }
      }
    }
"""
)


SALE_TOGGLE = (
    fragments.SALE_DETAILS
    + """
    subscription{
      event{
        ...on SaleToggle{
          sale{
            ...SaleDetails
          }
        }
      }
    }
"""
)


PROMOTION_CREATED = (
    fragments.PROMOTION_DETAILS
    + """
    subscription{
      event{
        ...on PromotionCreated{
          promotion{
            ...PromotionDetails
          }
        }
      }
    }
"""
)

PROMOTION_UPDATED = (
    fragments.PROMOTION_DETAILS
    + """
    subscription{
      event{
        ...on PromotionUpdated{
          promotion{
            ...PromotionDetails
          }
        }
      }
    }
"""
)

PROMOTION_DELETED = (
    fragments.PROMOTION_DETAILS
    + """
    subscription{
      event{
        ...on PromotionDeleted{
          promotion{
            ...PromotionDetails
          }
        }
      }
    }
"""
)


PROMOTION_STARTED = (
    fragments.PROMOTION_DETAILS
    + """
    subscription{
      event{
        ...on PromotionStarted{
          promotion{
            ...PromotionDetails
          }
        }
      }
    }
"""
)


PROMOTION_ENDED = (
    fragments.PROMOTION_DETAILS
    + """
    subscription{
      event{
        ...on PromotionEnded{
          promotion{
            ...PromotionDetails
          }
        }
      }
    }
"""
)


PROMOTION_RULE_CREATED = (
    fragments.PROMOTION_RULE_DETAILS
    + """
    subscription{
      event{
        ...on PromotionRuleCreated{
          promotionRule{
            ...PromotionRuleDetails
          }
        }
      }
    }
"""
)

PROMOTION_RULE_UPDATED = (
    fragments.PROMOTION_RULE_DETAILS
    + """
    subscription{
      event{
        ...on PromotionRuleUpdated{
          promotionRule{
            ...PromotionRuleDetails
          }
        }
      }
    }
"""
)

PROMOTION_RULE_DELETED = (
    fragments.PROMOTION_RULE_DETAILS
    + """
    subscription{
      event{
        ...on PromotionRuleDeleted{
          promotionRule{
            ...PromotionRuleDetails
          }
        }
      }
    }
"""
)


INVOICE_REQUESTED = (
    fragments.INVOICE_DETAILS
    + fragments.INVOICE_ORDER_DETAILS
    + """
    subscription{
      event{
        ...on InvoiceRequested{
          invoice{
            ...InvoiceDetails
          }
          order {
            ...InvoiceOrderDetails
          }
        }
      }
    }
"""
)

INVOICE_DELETED = (
    fragments.INVOICE_DETAILS
    + fragments.INVOICE_ORDER_DETAILS
    + """
    subscription{
      event{
        ...on InvoiceDeleted{
          invoice{
            ...InvoiceDetails
          }
          order {
            ...InvoiceOrderDetails
          }
        }
      }
    }
"""
)

INVOICE_SENT = (
    fragments.INVOICE_DETAILS
    + fragments.INVOICE_ORDER_DETAILS
    + """
    subscription{
      event{
        ...on InvoiceSent{
          invoice{
            ...InvoiceDetails
          }
          order {
            ...InvoiceOrderDetails
          }
        }
      }
    }
"""
)

FULFILLMENT_CREATED = (
    fragments.FULFILLMENT_DETAILS
    + """
    subscription{
      event{
        ...on FulfillmentCreated{
          notifyCustomer
          fulfillment{
            ...FulfillmentDetails
          }
          order{
            id
          }
        }
      }
    }
"""
)

FULFILLMENT_CANCELED = (
    fragments.FULFILLMENT_DETAILS
    + """
    subscription{
      event{
        ...on FulfillmentCanceled{
          fulfillment{
            ...FulfillmentDetails
          }
          order{
            id
          }
        }
      }
    }
"""
)


FULFILLMENT_APPROVED = (
    fragments.FULFILLMENT_DETAILS
    + """
    subscription{
      event{
        ...on FulfillmentApproved{
          notifyCustomer
          fulfillment{
            ...FulfillmentDetails
          }
          order{
            id
          }
        }
      }
    }
"""
)


FULFILLMENT_METADATA_UPDATED = (
    fragments.FULFILLMENT_DETAILS
    + """
    subscription{
      event{
        ...on FulfillmentMetadataUpdated{
          fulfillment{
            ...FulfillmentDetails
          }
          order{
            id
          }
        }
      }
    }
"""
)

FULFILLMENT_TRACKING_NUMBER_UPDATED = (
    fragments.FULFILLMENT_DETAILS
    + """
    subscription{
      event{
        ...on FulfillmentTrackingNumberUpdated{
          fulfillment{
            ...FulfillmentDetails
          }
          order{
            id
          }
        }
      }
    }
"""
)


CUSTOMER_CREATED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on CustomerCreated{
          user{
            ...CustomerDetails
          }
        }
      }
    }
"""
)

CUSTOMER_UPDATED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on CustomerUpdated{
          user{
            ...CustomerDetails
          }
        }
      }
    }
"""
)


CUSTOMER_DELETED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on CustomerDeleted{
          user{
            ...CustomerDetails
          }
        }
      }
    }
"""
)


CUSTOMER_METADATA_UPDATED = (
    fragments.CUSTOMER_DETAILS
    + """
    subscription{
      event{
        ...on CustomerMetadataUpdated{
          user{
            ...CustomerDetails
          }
        }
      }
    }
"""
)


COLLECTION_CREATED = (
    fragments.COLLECTION
    + """
    subscription{
      event{
        ...on CollectionCreated{
          collection(channel: "main"){
            ...CollectionDetails
          }
        }
      }
    }
    """
)


COLLECTION_UPDATED = (
    fragments.COLLECTION
    + """
    subscription{
      event{
        ...on CollectionUpdated{
          collection(channel: "main"){
            ...CollectionDetails
          }
        }
      }
    }
    """
)

COLLECTION_DELETED = (
    fragments.COLLECTION
    + """
    subscription{
      event{
        ...on CollectionDeleted{
          collection(channel: "main"){
            ...CollectionDetails
          }
        }
      }
    }
    """
)


COLLECTION_METADATA_UPDATED = (
    fragments.COLLECTION
    + """
    subscription{
      event{
        ...on CollectionMetadataUpdated{
          collection(channel: "main"){
            ...CollectionDetails
          }
        }
      }
    }
    """
)


CHECKOUT_CREATED = """
    subscription{
      event{
        ...on CheckoutCreated{
          checkout{
            id
            totalPrice{
                currency
            }
          }
        }
      }
    }
"""

CHECKOUT_UPDATED = """
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

CHECKOUT_FULLY_PAID = """
    subscription{
      event{
        ...on CheckoutFullyPaid{
          checkout{
            id
          }
        }
      }
    }
"""

CHECKOUT_FULLY_AUTHORIZED = """
    subscription{
      event{
        ...on CheckoutFullyAuthorized{
          checkout{
            id
          }
        }
      }
    }
"""

CHECKOUT_METADATA_UPDATED = """
    subscription{
      event{
        ...on CheckoutMetadataUpdated{
          checkout{
            id
          }
        }
      }
    }
"""

PAGE_CREATED = (
    fragments.PAGE_DETAILS
    + """
    subscription{
      event{
        ...on PageCreated{
          page{
            ...PageDetails
          }
        }
      }
    }
"""
)

PAGE_UPDATED = (
    fragments.PAGE_DETAILS
    + """
    subscription{
      event{
        ...on PageUpdated{
          page{
            ...PageDetails
          }
        }
      }
    }
"""
)

PAGE_DELETED = (
    fragments.PAGE_DETAILS
    + """
    subscription{
      event{
        ...on PageDeleted{
          page{
            ...PageDetails
          }
        }
      }
    }
"""
)


PAGE_TYPE_CREATED = (
    fragments.PAGE_TYPE_DETAILS
    + """
    subscription{
      event{
        ...on PageTypeCreated{
          pageType{
            ...PageTypeDetails
          }
        }
      }
    }
"""
)

PAGE_TYPE_UPDATED = (
    fragments.PAGE_TYPE_DETAILS
    + """
    subscription{
      event{
        ...on PageTypeUpdated{
          pageType{
            ...PageTypeDetails
          }
        }
      }
    }
"""
)

PAGE_TYPE_DELETED = (
    fragments.PAGE_TYPE_DETAILS
    + """
    subscription{
      event{
        ...on PageTypeDeleted{
          pageType{
            ...PageTypeDetails
          }
        }
      }
    }
"""
)

PERMISSION_GROUP_CREATED = (
    fragments.PERMISSION_GROUP_DETAILS
    + """
    subscription{
      event{
        ...on PermissionGroupCreated{
          permissionGroup{
            ...PermissionGroupDetails
          }
        }
      }
    }
"""
)

PERMISSION_GROUP_UPDATED = (
    fragments.PERMISSION_GROUP_DETAILS
    + """
    subscription{
      event{
        ...on PermissionGroupUpdated{
          permissionGroup{
            ...PermissionGroupDetails
          }
        }
      }
    }
"""
)

PERMISSION_GROUP_DELETED = (
    fragments.PERMISSION_GROUP_DETAILS
    + """
    subscription{
      event{
        ...on PermissionGroupDeleted{
          permissionGroup{
            ...PermissionGroupDetails
          }
        }
      }
    }
"""
)


TRANSACTION_ITEM_METADATA_UPDATED = """
    subscription{
      event{
        ...on TransactionItemMetadataUpdated{
          transaction {
            id
          }
        }
      }
    }
    """


LIST_STORED_PAYMENT_METHODS = """
  subscription {
    event {
      ... on ListStoredPaymentMethods {
        issuingPrincipal {
          ... on Node {
            id
          }
        }
      }
    }
  }
"""


MULTIPLE_EVENTS = """
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

TRANSLATION_CREATED = """
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
          __typename
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
        ... on PromotionTranslation {
          id
          __typename
        }
        ... on PromotionRuleTranslation {
          id
        }
      }
    }
  }
}
"""

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

TranslationTypes = Enum(
    "TranslationTypes",
    {
        to_snake_case(k.__name__).upper(): k.__name__
        for k in TRANSLATIONS_TYPES_MAP.keys()
    },
)


class TranslationQueryType(Enum):
    CREATED = "TranslationCreated"
    UPDATED = "TranslationUpdated"


def build_translation_query(
    type: TranslationTypes,
    query_type: TranslationQueryType,
    translated_object_id: str,
) -> str:
    return (  # noqa: UP031
        """
        subscription {
          event {
            ... on %s {
              translation {
                ... on %s {
                  id
                  name
                  translatableContent {
                    %s
                    name
                  }
                }
              }
            }
          }
        }
        """
    ) % (query_type.value, type.value, translated_object_id)


TRANSLATION_CREATED_PRODUCT = build_translation_query(
    TranslationTypes.PRODUCT_TRANSLATION,
    TranslationQueryType.CREATED,
    "productId",
)
TRANSLATION_CREATED_PRODUCT_VARIANT = build_translation_query(
    TranslationTypes.PRODUCT_VARIANT_TRANSLATION,
    TranslationQueryType.CREATED,
    "productVariantId",
)
TRANSLATION_CREATED_COLLECTION = build_translation_query(
    TranslationTypes.COLLECTION_TRANSLATION,
    TranslationQueryType.CREATED,
    "collectionId",
)
TRANSLATION_CREATED_CATEGORY = build_translation_query(
    TranslationTypes.CATEGORY_TRANSLATION,
    TranslationQueryType.CREATED,
    "categoryId",
)
TRANSLATION_CREATED_ATTRIBUTE = build_translation_query(
    TranslationTypes.ATTRIBUTE_TRANSLATION,
    TranslationQueryType.CREATED,
    "attributeId",
)
TRANSLATION_CREATED_ATTRIBUTE_VALUE = build_translation_query(
    TranslationTypes.ATTRIBUTE_VALUE_TRANSLATION,
    TranslationQueryType.CREATED,
    "attributeValueId",
)
TRANSLATION_CREATED_SHIPPING_METHOD = build_translation_query(
    TranslationTypes.SHIPPING_METHOD_TRANSLATION,
    TranslationQueryType.CREATED,
    "shippingMethodId",
)
TRANSLATION_CREATED_PROMOTION = build_translation_query(
    TranslationTypes.PROMOTION_TRANSLATION,
    TranslationQueryType.CREATED,
    "promotionId",
)
TRANSLATION_CREATED_PROMOTION_RULE = build_translation_query(
    TranslationTypes.PROMOTION_RULE_TRANSLATION,
    TranslationQueryType.CREATED,
    "promotionRuleId",
)
TRANSLATION_CREATED_VOUCHER = build_translation_query(
    TranslationTypes.VOUCHER_TRANSLATION,
    TranslationQueryType.CREATED,
    "voucherId",
)
TRANSLATION_CREATED_MENU_ITEM = build_translation_query(
    TranslationTypes.MENU_ITEM_TRANSLATION,
    TranslationQueryType.CREATED,
    "menuItemId",
)
TRANSLATION_CREATED_PAGE = """
    subscription {
      event {
        ... on TranslationCreated {
          translation {
            ... on PageTranslation {
              id
              title
              translatableContent {
                pageId
                title
              }
            }
          }
        }
      }
    }
"""
TRANSLATION_CREATED_SALE = """
    subscription {
      event {
        ... on TranslationCreated {
          translation {
            ... on SaleTranslation {
              __typename
              id
              name
              translatableContent {
                saleId
                name
              }
            }
          }
        }
      }
    }
"""

TRANSLATION_UPDATED = """
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
          __typename
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
        ... on PromotionTranslation {
          id
          __typename
        }
        ... on PromotionRuleTranslation {
          id
        }
      }
    }
  }
}
"""

TRANSLATION_UPDATED_PRODUCT = build_translation_query(
    TranslationTypes.PRODUCT_TRANSLATION,
    TranslationQueryType.UPDATED,
    "productId",
)
TRANSLATION_UPDATED_PRODUCT_VARIANT = build_translation_query(
    TranslationTypes.PRODUCT_VARIANT_TRANSLATION,
    TranslationQueryType.UPDATED,
    "productVariantId",
)
TRANSLATION_UPDATED_COLLECTION = build_translation_query(
    TranslationTypes.COLLECTION_TRANSLATION,
    TranslationQueryType.UPDATED,
    "collectionId",
)
TRANSLATION_UPDATED_CATEGORY = build_translation_query(
    TranslationTypes.CATEGORY_TRANSLATION,
    TranslationQueryType.UPDATED,
    "categoryId",
)
TRANSLATION_UPDATED_ATTRIBUTE = build_translation_query(
    TranslationTypes.ATTRIBUTE_TRANSLATION,
    TranslationQueryType.UPDATED,
    "attributeId",
)
TRANSLATION_UPDATED_ATTRIBUTE_VALUE = build_translation_query(
    TranslationTypes.ATTRIBUTE_VALUE_TRANSLATION,
    TranslationQueryType.UPDATED,
    "attributeValueId",
)
TRANSLATION_UPDATED_SHIPPING_METHOD = build_translation_query(
    TranslationTypes.SHIPPING_METHOD_TRANSLATION,
    TranslationQueryType.UPDATED,
    "shippingMethodId",
)
TRANSLATION_UPDATED_PROMOTION = build_translation_query(
    TranslationTypes.PROMOTION_TRANSLATION,
    TranslationQueryType.UPDATED,
    "promotionId",
)
TRANSLATION_UPDATED_PROMOTION_RULE = build_translation_query(
    TranslationTypes.PROMOTION_RULE_TRANSLATION,
    TranslationQueryType.UPDATED,
    "promotionRuleId",
)
TRANSLATION_UPDATED_VOUCHER = build_translation_query(
    TranslationTypes.VOUCHER_TRANSLATION,
    TranslationQueryType.UPDATED,
    "voucherId",
)
TRANSLATION_UPDATED_MENU_ITEM = build_translation_query(
    TranslationTypes.MENU_ITEM_TRANSLATION,
    TranslationQueryType.UPDATED,
    "menuItemId",
)
TRANSLATION_UPDATED_PAGE = """
    subscription {
      event {
        ... on TranslationUpdated {
          translation {
            ... on PageTranslation {
              id
              title
              translatableContent {
                pageId
                title
              }
            }
          }
        }
      }
    }
"""

TEST_VALID_SUBSCRIPTION = """
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


TEST_INVALID_SUBSCRIPTION_AND_QUERY = """
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

TEST_INVALID_QUERY_AND_SUBSCRIPTION = """
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


MENU_CREATED = (
    fragments.MENU_DETAILS
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


MENU_UPDATED = (
    fragments.MENU_DETAILS
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


MENU_DELETED = (
    fragments.MENU_DETAILS
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


MENU_ITEM_CREATED = (
    fragments.MENU_ITEM_DETAILS
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


MENU_ITEM_UPDATED = (
    fragments.MENU_ITEM_DETAILS
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


MENU_ITEM_DELETED = (
    fragments.MENU_ITEM_DETAILS
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


WAREHOUSE_CREATED = (
    fragments.WAREHOUSE_DETAILS
    + """
    subscription{
      event{
        ...on WarehouseCreated{
          warehouse{
            ...WarehouseDetails
          }
        }
      }
    }
"""
)

WAREHOUSE_UPDATED = (
    fragments.WAREHOUSE_DETAILS
    + """
    subscription{
      event{
        ...on WarehouseUpdated{
          warehouse{
            ...WarehouseDetails
          }
        }
      }
    }
"""
)

WAREHOUSE_DELETED = (
    fragments.WAREHOUSE_DETAILS
    + """
    subscription{
      event{
        ...on WarehouseDeleted{
          warehouse{
            ...WarehouseDetails
          }
        }
      }
    }
"""
)

WAREHOUSE_METADATA_UPDATED = (
    fragments.WAREHOUSE_DETAILS
    + """
    subscription{
      event{
        ...on WarehouseMetadataUpdated{
          warehouse{
            ...WarehouseDetails
          }
        }
      }
    }
"""
)

PAYMENT_AUTHORIZE = (
    fragments.PAYMENT_DETAILS
    + """
    subscription{
      event{
        ...on PaymentAuthorize{
          payment{
            ...PaymentDetails
          }
        }
      }
    }
    """
)


PAYMENT_CAPTURE = (
    fragments.PAYMENT_DETAILS
    + """
    subscription{
      event{
        ...on PaymentCaptureEvent{
          payment{
            ...PaymentDetails
          }
        }
      }
    }
    """
)


PAYMENT_REFUND = (
    fragments.PAYMENT_DETAILS
    + """
    subscription{
      event{
        ...on PaymentRefundEvent{
          payment{
            ...PaymentDetails
          }
        }
      }
    }
    """
)


PAYMENT_VOID = (
    fragments.PAYMENT_DETAILS
    + """
    subscription{
      event{
        ...on PaymentVoidEvent{
          payment{
            ...PaymentDetails
          }
        }
      }
    }
    """
)


PAYMENT_CONFIRM = (
    fragments.PAYMENT_DETAILS
    + """
    subscription{
      event{
        ...on PaymentConfirmEvent{
          payment{
            ...PaymentDetails
          }
        }
      }
    }
    """
)


PAYMENT_PROCESS = (
    fragments.PAYMENT_DETAILS
    + """
    subscription{
      event{
        ...on PaymentProcessEvent{
          payment{
            ...PaymentDetails
          }
        }
      }
    }
    """
)

PAYMENT_LIST_GATEWAYS = """
    subscription{
      event{
        ...on PaymentListGateways{
          checkout{
            id
          }
        }
      }
    }
    """

ORDER_FILTER_SHIPPING_METHODS = """
subscription{
  event{
    ...on OrderFilterShippingMethods{
      order{
        id
      }
      shippingMethods{
      id
      name
      }
    }
  }
}
"""


CHECKOUT_FILTER_SHIPPING_METHODS = """
subscription{
  event{
    ...on CheckoutFilterShippingMethods{
      checkout{
        id
      }
      shippingMethods{
        name
        id
      }
    }
  }
}
"""


SHIPPING_LIST_METHODS_FOR_CHECKOUT = """
subscription{
  event{
    ...on ShippingListMethodsForCheckout{
      checkout{
        id
      }
      shippingMethods{
        name
        id
      }
    }
  }
}
"""


CHECKOUT_FILTER_SHIPPING_METHODS_CIRCULAR_SHIPPING_METHODS = """
subscription{
  event{
    ...on CheckoutFilterShippingMethods{
      checkout{
        id
        shippingMethods{
          id
        }
      }
    }
  }
}
"""

CHECKOUT_FILTER_SHIPPING_METHODS_AVAILABLE_SHIPPING_METHODS = """
subscription{
  event{
    ...on CheckoutFilterShippingMethods{
      checkout{
        id
        availableShippingMethods{
          id
        }
      }
    }
  }
}
"""

CHECKOUT_FILTER_SHIPPING_METHODS_AVAILABLE_PAYMENT_GATEWAYS = """
subscription{
  event{
    ...on CheckoutFilterShippingMethods{
      checkout{
        id
        availablePaymentGateways{
          id
        }
      }
    }
  }
}
"""

ORDER_FILTER_SHIPPING_METHODS_AVAILABLE_SHIPPING_METHODS = """
subscription{
  event{
    ...on OrderFilterShippingMethods{
      order{
        id
        availableShippingMethods{
          id
        }
      }
    }
  }
}
"""

ORDER_FILTER_SHIPPING_METHODS_CIRCULAR_SHIPPING_METHODS = """
subscription{
  event{
    ...on OrderFilterShippingMethods{
      order{
        id
        shippingMethods{
          id
        }
      }
    }
  }
}
"""


INVALID_MULTIPLE_EVENTS = """
    subscription{
      event{
        ...on ProductUpdated{
          product{
            id
          }
        }
      }
      event{
        ...on ProductCreated{
          product{
            id
          }
        }
      }
    }
"""

INVALID_MULTIPLE_EVENTS_WITH_FRAGMENTS = (
    fragments.PRODUCT_VARIANT
    + fragments.CATEGORY_DETAILS
    + """
    subscription{
      event{
        ...on ProductUpdated{
          product{
              variants{
                ...ProductVariant
                }
              category {
                ...CategoryDetails
              }
          }
        }
      }
      event{
        ...on ProductCreated{
          product{
            variants{
                ...ProductVariant
            }
            category{
              ...CategoryDetails
            }
          }
        }
      }
    }
    """
)


QUERY_WITH_MULTIPLE_FRAGMENTS = (
    fragments.PRODUCT_VARIANT
    + fragments.CATEGORY_DETAILS
    + """
    subscription{
      event{
        ...on ProductUpdated{
          product{
            variants{
              ...ProductVariant
            }
            category{
              ...CategoryDetails
            }
          }
        }
      }
    }
    """
)

THUMBNAIL_CREATED = """
    subscription {
      event {
        ... on ThumbnailCreated {
          url
          id
          objectId
          mediaUrl
        }
      }
    }
"""


ORDER_CALCULATE_TAXES = """
    subscription {
      event {
        ... on CalculateTaxes {
          taxBase {
            sourceObject {
              ...on Order{
                discounts {
                  amount {
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

CHECKOUT_SHIPPING_LIST_AND_FILTER = """
    subscription {
      event {
        ... on CheckoutFilterShippingMethods {
          __typename
          checkout {
            id
          }
        }
        ... on ShippingListMethodsForCheckout {
          __typename
          checkout {
            id
          }
        }
      }
    }
"""
