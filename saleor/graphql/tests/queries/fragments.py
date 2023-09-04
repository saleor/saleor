APP_DETAILS = """
    fragment AppDetails on App{
        id
        isActive
        name
        appUrl
    }
"""

PRICE = """
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

PRODUCT_VARIANT = """
    fragment ProductVariant on ProductVariant {
      id
      name
      product {
        id
        name
      }
    }
"""


SHIPPING_METHOD_DETAILS = """
    fragment ShippingMethodDetails on ShippingMethodType {
      id
      name
      channelListings {
        channel {
          name
        }
      }
    }
"""

COLLECTION_POINT = """
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

PRICING_DETAILS = """
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


CATEGORY_DETAILS = """
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


INVOICE_DETAILS = """
fragment InvoiceDetails on Invoice {
  id
  status
  number
  order {
    id
  }
}
"""

INVOICE_ORDER_DETAILS = """
fragment InvoiceOrderDetails on Order {
  id
  number
  userEmail
  isPaid
}
"""


SHIPPING_METHOD_TYPE = """
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


SHIPPING_ZONE_DETAILS = (
    SHIPPING_METHOD_TYPE
    + """
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

WAREHOUSE_DETAILS = """
fragment WarehouseDetails on Warehouse {
  id
  name
  shippingZones (first: 10) {
    edges {
      node {
        id
      }
    }
  }
  address {
    companyName
  }
}
"""


FULFILLMENT_DETAILS = (
    PRODUCT_VARIANT
    + PRICE
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


ADDRESS_DETAILS = """
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


CUSTOMER_DETAILS = (
    ADDRESS_DETAILS
    + """
fragment CustomerDetails on User {
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

STAFF_DETAILS = """
fragment StaffDetails on User {
  email
  firstName
  lastName
  isStaff
  isActive
}
"""


BASIC_PRODUCT_FIELDS = """
fragment BasicProductFields on Product {
  id
  name
}
"""

PRODUCT_EXPORT_DETAILS = """
fragment ProductExportDetails on ExportFile{
  id
  createdAt
  updatedAt
  status
  url
  message
}
"""


COLLECTION = (
    BASIC_PRODUCT_FIELDS
    + """
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


PAGE_DETAILS = """
fragment PageDetails on Page{
  id
  title
  content
  slug
  isPublished
  publishedAt
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


PAGE_TYPE_DETAILS = """
fragment PageTypeDetails on PageType{
  id
  name
  slug
  attributes {
    slug
  }
}
"""


PERMISSION_GROUP_DETAILS = """
fragment PermissionGroupDetails on Group{
  name
  permissions {
    name
  }
  users {
    email
  }
}
"""


SALE_DETAILS = """
fragment SaleDetails on Sale {
  id
  name
  startDate
  endDate
  categories(first:10){
    edges {
      node {
        id
        name
      }
    }
  }
}
"""

GIFT_CARD_DETAILS = """
fragment GiftCardDetails on GiftCard{
  id
  isActive
  code
  createdBy {
    email
  }
}
"""

GIFT_CARD_EXPORT_DETAILS = """
fragment GiftCardExportDetails on ExportFile{
  id
  createdAt
  updatedAt
  status
  url
  message
}
"""


VOUCHER_DETAILS = """
fragment VoucherDetails on Voucher{
  id
  name
  code
  usageLimit
}
"""


MENU_DETAILS = """
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

MENU_ITEM_DETAILS = """
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

ATTRIBUTE_DETAILS = """
fragment AttributeDetails on Attribute {
  name
  slug
  type
  inputType
}
"""

ATTRIBUTE_VALUE_DETAILS = """
fragment AttributeValueDetails on AttributeValue {
  name
  slug
  value
}
"""

PAYMENT_DETAILS = """
fragment PaymentDetails on Payment {
  id
  total {
    amount
    currency
  }
  isActive
  gateway
}
"""


TRANSACTION_ITEM_DETAILS = """
fragment TransactionFragment on TransactionItem {
  id
  createdAt
  actions
  authorizedAmount {
    currency
    amount
  }
  refundedAmount {
    currency
    amount
  }
  canceledAmount {
    currency
    amount
  }
  chargedAmount {
    currency
    amount
  }
  events {
    id
  }
  pspReference
  order {
    id
  }
}
"""
