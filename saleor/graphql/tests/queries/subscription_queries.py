
FRAGMENT_PRICE = """
    fragment Price on TaxedMoney {
      currency
      gross {
        amount
      }
      net {
        amount
      }
    }
"""

FRAGMENT_PRODUCT_VARIANT = """
        fragment ProductVariant on ProductVariant {
          id
          name
          product {
            id
            name
          }
        }
    """

FRAGMENT_CHECKOUT_LINE = (
    FRAGMENT_PRODUCT_VARIANT
    + """
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
    """
)

FRAGMENT_ADDRESS = """
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
"""


FRAGMENT_SHIPPING_METHOD_DETAILS = """
    fragment ShippingMethodDetails on ShippingMethodType {
        id
        name
        price {
            amount
        }
    }
"""

FRAGMENT_COLLECTION_POINT = """
   fragment CollectionPoint on Warehouse {
        id
        name
        isPrivate
        clickAndCollectOption
        address {
             streetAddress1
          }
     }
"""


FRAGMENT_CHECKOUT = (
        FRAGMENT_CHECKOUT_LINE
        + FRAGMENT_ADDRESS
        + FRAGMENT_SHIPPING_METHOD_DETAILS
        + """
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
          stockReservationExpires
          isShippingRequired
          discount {
            currency
            amount
          }
          discountName
          translatedDiscountName
          voucherCode
        }
    """
)

FRAGMENT_CHECKOUT_FOR_CC = (
        FRAGMENT_CHECKOUT_LINE
        + FRAGMENT_ADDRESS
        + FRAGMENT_SHIPPING_METHOD_DETAILS
        + FRAGMENT_COLLECTION_POINT
        + """
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
          availableCollectionPoints {
            ...CollectionPoint
          }
          deliveryMethod {
            __typename
            ... on ShippingMethod {
              ...ShippingMethod
            }
            ... on Warehouse {
              ...CollectionPoint
            }
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
    """
)


MUTATION_CHECKOUT_CREATE = (
    FRAGMENT_CHECKOUT
    + """
        mutation CreateCheckout($checkoutInput: CheckoutCreateInput!) {
            checkoutCreate(input: $checkoutInput) {
                errors {
                    field
                    message
                }
                checkout {
                    ...Checkout
                }
            }
        }
    """
)


# DETAILS FRAGMENTS
PRICING_DETAILS_FRAGMENT = """
fragment PricingDetails on Pricing {
  price {
    gross {
      amount
      currency
    }
  }
  discount{
    currency
    gross
    net
  }
}
"""


CATEGORY_DETAILS_FRAGMENT = """
fragment CategoryDetails on Category {
  id
  name
  ancestors(first: 20) {
    edges {
      node {
        name
      }
    }
  }
  children(first: 20) {
    edges {
      node {
        name
      }
    }
  }
  products(first: 10 channel: "main") {
    edges {
      node {
        id
        name
      }
    }
  }
}
"""


# QUERIES

CATEGORY_CREATED_SUBSCRIPTION_QUERY = (
    CATEGORY_DETAILS_FRAGMENT + """
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

CATEGORY_UPDATED_SUBSCRIPTION_QUERY = (
    CATEGORY_DETAILS_FRAGMENT + """
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

CATEGORY_DELETED_SUBSCRIPTION_QUERY = (
    CATEGORY_DETAILS_FRAGMENT + """
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

PRODUCT_VARIANT_UPDATED_SUBSCRIPTION_QUERY = (
    PRICING_DETAILS_FRAGMENT
    + """
    subscription{
      event{
        ...on ProductVariantUpdated{
          productVariant{
          pricing{
            ...PricingDetails
          }
            id
          }
        }
      }
    }
"""
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

FRAGMENT_INVOICE_DETAILS = """
fragment InvoiceDetails on Invoice {
  id
  status
  number
}
"""


INVOICE_REQUESTED_SUBSCRIPTION_QUERY = (
    FRAGMENT_INVOICE_DETAILS + """
    subscription{
      event{
        ...on InvoiceRequested{
          invoice{
            ...InvoiceDetails
          }
        }
      }
    }
"""
)


INVOICE_DELETED_SUBSCRIPTION_QUERY = (
    FRAGMENT_INVOICE_DETAILS + """
    subscription{
      event{
        ...on InvoiceDeleted{
          invoice{
            ...InvoiceDetails
          }
        }
      }
    }
"""
)


INVOICE_SENT_SUBSCRIPTION_QUERY = (
    FRAGMENT_INVOICE_DETAILS + """
    subscription{
      event{
        ...on InvoiceSent{
          invoice{
            ...InvoiceDetails
          }
        }
      }
    }
"""
)

FRAGMENT_SHIPPING_METHOD_TYPE = """
fragment ShippingMethodType on ShippingMethodType{
  id
  name
  type
  maximumOrderPrice{
    amount
  }
  minimumOrderPrice {
    amount
  }
  maximumOrderWeight {
    value
    unit
  }
  maximumOrderWeight {
    value
    unit
  }

}
"""
FRAGMENT_SHIPPING_ZONE_DETAILS = (
    FRAGMENT_SHIPPING_METHOD_TYPE + """
fragment ShippingZoneDetails on ShippingZone {
  id
  countries {
    code
    country
    }
  shippingMethods {
    ...ShippingMethodType
    }
}
"""
)

FRAGMENT_WAREHOUSE_DETAILS = (
    FRAGMENT_SHIPPING_ZONE_DETAILS + """
fragment WarehouseDetails on Warehouse {
  id
  name
  companyName
  shippingZones {
    edges {
      node {
        ...ShippingZoneDetails
      }
    }
  }
}
""")


FRAGMENT_FULFILLMENT_DETAILS = (
    FRAGMENT_PRODUCT_VARIANT
    + FRAGMENT_PRICE
    + """
fragment FulfillmentDetails on Fulfillment {
  id
  fulfillmentOrder
  trackingNumber
  status
  lines {
    id
    quantity
    orderLine {
        variant {
          ...ProductVariant
        }
        unitPrice {
          currency
          ...Price
        }
    }
  }
}
"""
)

FULFILLMENT_CREATED_SUBSCRIPTION_QUERY = (
    FRAGMENT_FULFILLMENT_DETAILS + """
    subscription{
      event{
        ...on FulfillmentCreated{
          fulfillment{
            ...FulfillmentDetails
          }
        }
      }
    }
""")


FULFILLMENT_CANCELED_SUBSCRIPTION_QUERY = (
    FRAGMENT_FULFILLMENT_DETAILS + """
    subscription{
      event{
        ...on FulfillmentCanceled{
          fulfillment{
            ...FulfillmentDetails
          }
        }
      }
    }
""")

FRAGMENT_ADDRESS_DETAILS = """
fragment AddressDetails on Address {
    firstName
    lastName
    companyName
    streetAddress1
    streetAddress2
    city
    cityArea
    postalCode
    countryArea
    phone
    country {
      code
    }
}
    """
# TODO orders frament
FRAGMENT_USER_DETAILS = (
    FRAGMENT_ADDRESS_DETAILS + """
fragment UserDetails on User {
  email
  firstName
  lastName
  isStaff
  isActive
  addresses {
    id
  }
  languageCode
  defaultShippingAddress {
    ...AddressDetails
  }
  defaultBillingAddress {
    ...AddressDetails
  }
}
"""
)

CUSTOMER_CREATED_SUBSCRIPTION_QUERY = (
    FRAGMENT_USER_DETAILS + """
    subscription{
      event{
        ...on CustomerCreated{
          user{
            ...UserDetails
          }
        }
      }
    }
"""
)



CUSTOMER_UPDATED_SUBSCRIPTION_QUERY = (
    FRAGMENT_USER_DETAILS + """
    subscription{
      event{
        ...on CustomerUpdated{
          user{
            ...UserDetails
          }
        }
      }
    }
""")

FRAGMENT_BASIC_PRODUCT_FIELDS = """
fragment BasicProductFields on Product {
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
"""


FRAGMENT_PRODUCT_DETAILS = """
"""
# TODO products fragment
FRAGMENT_COLLECTION = (
    FRAGMENT_BASIC_PRODUCT_FIELDS + """
    fragment CollectionDetails on Collection {
      id
      name
      slug
      channel
      products(first: 10) {
        edges {
            node {
                ...BasicProductFields
            }
        }
      }
    }
    """
)

COLLECTION_CREATED_SUBSCRIPTION_QUERY = (
    FRAGMENT_COLLECTION + """
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


COLLECTION_UPDATED_SUBSCRIPTION_QUERY = (
    FRAGMENT_COLLECTION + """
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


COLLECTION_DELETED_SUBSCRIPTION_QUERY =(
    FRAGMENT_COLLECTION + """
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

# TODO
FRAGMENT_CHECKOUT_FOR_SUBSCRIPTION = """

"""
CHECKOUT_CREATED_SUBSCRIPTION_QUERY = (
    FRAGMENT_CHECKOUT + """
    subscription{
      event{
        ...on CheckoutCreated{
          checkout{
            ...Checkout
          }
        }
      }
    }
"""
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

PAGE_DETAILS_FRAGMENT = """
fragment PageDetails on Page{
  id
  title
  content
  slug
  isPublished
  publicationDate
  pageType {
    id
  }
    attributes {
    attribute {
      slug
    }
    values {
      slug
      name
      reference
      date
      dateTime
      file {
        url
        contentType
      }
    }
  }
}

"""


PAGE_CREATED_SUBSCRIPTION_QUERY = (
    PAGE_DETAILS_FRAGMENT + """
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


PAGE_UPDATED_SUBSCRIPTION_QUERY = (
    PAGE_DETAILS_FRAGMENT + """
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


PAGE_DELETED_SUBSCRIPTION_QUERY = (
    PAGE_DETAILS_FRAGMENT + """
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
