from saleor.graphql.tests.utils import get_graphql_content

from .fragments import ORDER_LINE_FRAGMENT

ORDER_BULK_CREATE_MUTATION = (
    """
 mutation OrderBulkCreate(
    $orders: [OrderBulkCreateInput!]!,
    $errorPolicy: ErrorPolicyEnum,
    $stockUpdatePolicy: StockUpdatePolicyEnum
) {
    orderBulkCreate(
        orders: $orders,
        errorPolicy: $errorPolicy,
        stockUpdatePolicy: $stockUpdatePolicy
    ) {
        count
        results {
            order {
                id
                user {
                    id
                    email
                }
                metadata {
                    key
                    value
                }
                privateMetadata {
                    key
                    value
                }
                lines {
                    ...OrderLine
                }
                billingAddress{
                    postalCode
                    metadata{
                        key
                        value
                    }
                }
                shippingAddress{
                    postalCode
                    metadata{
                        key
                        value
                    }
                }
                shippingMethodName
                shippingTaxClass{
                    name
                }
                shippingTaxClassName
                shippingTaxClassMetadata {
                    key
                    value
                }
                shippingTaxClassPrivateMetadata {
                    key
                    value
                }
                shippingPrice {
                    gross {
                        amount
                    }
                    net {
                        amount
                    }
                }
                subtotal{
                    gross {
                        amount
                    }
                    net {
                        amount
                    }
                }
                total{
                    gross {
                        amount
                    }
                    net {
                        amount
                    }
                }
                undiscountedTotal{
                    gross {
                        amount
                    }
                    net {
                        amount
                    }
                }
                events {
                    message
                    user {
                        id
                    }
                    app {
                        id
                    }
                }
                weight {
                    value
                }
                externalReference
                trackingClientId
                displayGrossPrices
                channel {
                    slug
                }
                status
                created
                languageCode
                collectionPointName
                redirectUrl
                origin
                fulfillments {
                    lines {
                        id
                        quantity
                        orderLine {
                            id
                        }
                    }
                    trackingNumber
                    fulfillmentOrder
                    status
                }
                transactions {
                    id
                    pspReference
                    message
                    name
                    authorizedAmount {
                        amount
                        currency
                    }
                    canceledAmount{
                        currency
                        amount
                    }
                    chargedAmount{
                        currency
                        amount
                    }
                    refundedAmount{
                        currency
                        amount
                    }
                    events {
                        amount {
                            amount
                        }
                        type
                    }
                }
                invoices {
                    number
                    url
                }
                discounts {
                    type
                    valueType
                    value
                    reason
                }
                voucher {
                    id
                    code
                }
                voucherCode
            }
            errors {
                path
                message
                code
            }
        }
        errors {
            message
            code
        }
    }
}
"""
    + ORDER_LINE_FRAGMENT
)


def order_bulk_create(api_client, orders):
    variables = {"orders": orders}

    response = api_client.post_graphql(
        ORDER_BULK_CREATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["orderBulkCreate"]

    return data
