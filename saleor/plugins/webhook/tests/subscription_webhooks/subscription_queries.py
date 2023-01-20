from .....graphql.tests.queries import fragments

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
            ...CategoryDetails
          }
        }
      }
      event{
        ...on ProductCreated{
          product{
          variants{
                ...ProductVariant
            }
            ...CategoryDetails
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
            ...CategoryDetails
          }
        }
      }
    }
    """
)
