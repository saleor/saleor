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

WAREHOUSE_DETAILS = (
    SHIPPING_ZONE_DETAILS
    + """
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
"""
)


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


USER_DETAILS = (
    ADDRESS_DETAILS
    + """
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


BASIC_PRODUCT_FIELDS = """
fragment BasicProductFields on Product {
  id
  name
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


VOUCHER_DETAILS = """
fragment VoucherDetails on Voucher{
  id
  name
  code
  usageLimit
}
"""
