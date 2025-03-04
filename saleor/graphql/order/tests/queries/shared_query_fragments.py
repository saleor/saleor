ORDER_FRAGMENT_WITH_WEBHOOK_RELATED_FIELDS = """
fragment price on Money {
  amount
}

fragment taxPrice on TaxedMoney {
  gross {
    ...price
  }
}

fragment order on Order {
  shippingMethods {
    id
  }
  availableShippingMethods{
    id
  }
  errors {
    field
    orderLines
    code
  }
  canFinalize
  deliveryMethod {
    ... on ShippingMethod {
      id
    }
  }
  shippingMethodName
  total {
    ...taxPrice
  }
  undiscountedTotal {
    ...taxPrice
  }
  subtotal {
    ...taxPrice
  }
  shippingPrice {
    ...taxPrice
  }
  totalRemainingGrant {
    ...price
  }
  totalCancelPending {
    ...price
  }
  totalChargePending {
    ...price
  }
  totalAuthorizePending {
    ...price
  }
  totalRefundPending {
    ...price
  }
  totalRefunded {
    ...price
  }
  totalGrantedRefund {
    ...price
  }
  grantedRefunds {
    amount {
      ...price
    }
    lines {
      orderLine {
        unitPrice {
          ...taxPrice
        }
      }
    }
  }
  fulfillments {
    lines {
      orderLine {
        unitPrice {
          ...taxPrice
        }
      }
    }
  }
  lines {
    undiscountedTotalPrice {
      ...taxPrice
    }
    unitPrice {
      ...taxPrice
    }
    unitDiscount {
      ...price
    }
    undiscountedUnitPrice {
      ...taxPrice
    }
    totalPrice {
      ...taxPrice
    }
  }
  events {
    relatedOrder {
      total {
        ...taxPrice
      }
    }
    fulfilledItems {
      quantity
      orderLine {
        productName
        variantName
      }
    }
    lines {
      orderLine {
        unitPrice {
          ...taxPrice
        }
      }
    }
  }
}
"""
