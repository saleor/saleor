import graphene
import pytest
from django.utils import timezone

from .....order import OrderStatus
from ....tests.utils import get_graphql_content

ORDER_BULK_CREATE = """
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
                    lines {
                        id
                        variant {
                            id
                        }
                        productName
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
                    }
                    billingAddress{
                        postalCode
                    }
                    shippingAddress{
                        postalCode
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
                            quantity
                            orderLine {
                                id
                            }
                        }
                        trackingNumber
                        fulfillmentOrder
                        status
                    }
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    }
"""


@pytest.fixture
def order_bulk_input(
    app,
    channel_PLN,
    customer_user,
    default_tax_class,
    graphql_address_data,
    shipping_method_channel_PLN,
    variant,
    warehouse,
):
    shipping_method = shipping_method_channel_PLN
    user = {
        "id": graphene.Node.to_global_id("User", customer_user.id),
        "email": None,
    }
    delivery_method = {
        "shippingMethodId": graphene.Node.to_global_id(
            "ShippingMethod", shipping_method.id
        ),
        "shippingTaxClassId": graphene.Node.to_global_id(
            "TaxClass", default_tax_class.id
        ),
        "shippingPrice": {
            "gross": 120,
            "net": 100,
        },
        "shippingTaxRate": 0.2,
        "shippingTaxClassMetadata": [
            {
                "key": "md key",
                "value": "md value",
            }
        ],
        "shippingTaxClassPrivateMetadata": [
            {
                "key": "pmd key",
                "value": "pmd value",
            }
        ],
    }
    line = {
        "variantId": graphene.Node.to_global_id("ProductVariant", variant.id),
        "createdAt": timezone.now(),
        "productName": "Product Name",
        "variantName": "Variant Name",
        "translatedProductName": "Nazwa Produktu",
        "translatedVariantName": "Nazwa Wariantu",
        "isShippingRequired": True,
        "isGiftCard": False,
        "quantity": 5,
        "totalPrice": {
            "gross": 120,
            "net": 100,
        },
        "undiscountedTotalPrice": {
            "gross": 120,
            "net": 100,
        },
        "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
        "taxRate": 0.2,
        "taxClassId": graphene.Node.to_global_id("TaxClass", default_tax_class.id),
        "taxClassName": "Line Tax Class Name",
        "taxClassMetadata": [
            {
                "key": "md key",
                "value": "md value",
            }
        ],
        "taxClassPrivateMetadata": [
            {
                "key": "pmd key",
                "value": "pmd value",
            }
        ],
    }
    note = {
        "message": "Test message",
        "date": timezone.now(),
        "userId": graphene.Node.to_global_id("User", customer_user.id),
    }
    fulfillment_line = {
        "variantId": graphene.Node.to_global_id("ProductVariant", variant.id),
        "quantity": 5,
        "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
        "orderLineIndex": 0,
    }
    fulfillment = {"trackingCode": "abc-123", "lines": [fulfillment_line]}

    return {
        "channel": channel_PLN.slug,
        "createdAt": timezone.now(),
        "status": OrderStatus.DRAFT,
        "user": user,
        "billingAddress": graphql_address_data,
        "shippingAddress": graphql_address_data,
        "currency": "PLN",
        "languageCode": "PL",
        "deliveryMethod": delivery_method,
        "lines": [line],
        "notes": [note],
        "fulfillments": [fulfillment],
        "weight": "10.15",
        "trackingClientId": "tracking-id-123",
        "redirectUrl": "https://www.example.com",
    }


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_order_bulk_create(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input,
):
    order = order_bulk_input

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {"orders": [order]}

    get_graphql_content(staff_api_client.post_graphql(ORDER_BULK_CREATE, variables))
