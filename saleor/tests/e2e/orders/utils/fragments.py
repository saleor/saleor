ORDER_LINE_FRAGMENT = """
fragment OrderLine on OrderLine {
    id
    variant {
        id
    }
    productName
    productSku
    variantName
    translatedVariantName
    translatedProductName
    productVariantId
    isShippingRequired
    quantity
    quantityFulfilled
    unitPrice {
        gross {
            amount
        }
        net {
            amount
        }
    }
    unitDiscount {
        amount
    }
    unitDiscountValue
    unitDiscountReason
    unitDiscountType
    totalPrice {
        gross {
            amount
        }
        net {
            amount
        }
    }
    undiscountedUnitPrice{
        gross {
            amount
        }
        net {
            amount
        }
    }
    undiscountedTotalPrice{
        gross {
            amount
        }
        net {
            amount
        }
    }
    metadata {
        key
        value
    }
    privateMetadata {
        key
        value
    }
    taxClass {
        id
    }
    taxClassName
    taxRate
    taxClassMetadata {
        key
        value
    }
    taxClassPrivateMetadata {
        key
        value
    }
}"""
