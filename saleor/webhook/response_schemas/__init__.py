from .payment import (
    ListStoredPaymentMethodsSchema,
    PaymentGatewayInitializeTokenizationSessionSchema,
    PaymentMethodTokenizationFailedSchema,
    PaymentMethodTokenizationPendingSchema,
    PaymentMethodTokenizationSuccessSchema,
    StoredPaymentMethodDeleteRequestedSchema,
)
from .shipping import FilterShippingMethodsSchema, ListShippingMethodsSchema
from .taxes import CalculateTaxesSchema
from .transaction import (
    PaymentGatewayInitializeSessionSchema,
    TransactionCancelationRequestedAsyncSchema,
    TransactionCancelationRequestedSyncFailureSchema,
    TransactionCancelationRequestedSyncSuccessSchema,
    TransactionChargeRequestedAsyncSchema,
    TransactionChargeRequestedSyncFailureSchema,
    TransactionChargeRequestedSyncSuccessSchema,
    TransactionRefundRequestedAsyncSchema,
    TransactionRefundRequestedSyncFailureSchema,
    TransactionRefundRequestedSyncSuccessSchema,
    TransactionSessionActionRequiredSchema,
    TransactionSessionFailureSchema,
    TransactionSessionSuccessSchema,
)

# The list with schemas that should be exported to JSON files.
SCHEMAS_TO_EXPORT = [
    # taxes
    {
        "title": "CheckoutCalculateTaxes",
        "schema": CalculateTaxesSchema,
    },
    {
        "title": "OrderCalculateTaxes",
        "schema": CalculateTaxesSchema,
    },
    {
        "title": "ShippingListMethodsForCheckout",
        "schema": ListShippingMethodsSchema,
    },
    # shipping
    {
        "title": "ShippingListMethodsForOrder",
        "schema": ListShippingMethodsSchema,
    },
    {
        "title": "CheckoutFilterShippingMethods",
        "schema": FilterShippingMethodsSchema,
    },
    {
        "title": "OrderFilterShippingMethods",
        "schema": FilterShippingMethodsSchema,
    },
    # payment
    {
        "title": "ListStoredPaymentMethods",
        "schema": ListStoredPaymentMethodsSchema,
    },
    {
        "title": "StoredPaymentMethodDeleteRequested",
        "schema": StoredPaymentMethodDeleteRequestedSchema,
    },
    {
        "title": "PaymentGatewayInitializeTokenizationSession",
        "schema": PaymentGatewayInitializeTokenizationSessionSchema,
    },
    # transaction
    {
        "title": "PaymentGatewayInitializeSession",
        "schema": PaymentGatewayInitializeSessionSchema,
    },
]

COMBINED_SCHEMAS_TO_EXPORT = [
    # transaction
    {
        "title": "TransactionChargeRequested",
        "schemas": [
            TransactionChargeRequestedSyncSuccessSchema,
            TransactionChargeRequestedSyncFailureSchema,
            TransactionChargeRequestedAsyncSchema,
        ],
    },
    {
        "title": "TransactionRefundRequested",
        "schemas": [
            TransactionRefundRequestedSyncSuccessSchema,
            TransactionRefundRequestedSyncFailureSchema,
            TransactionRefundRequestedAsyncSchema,
        ],
    },
    {
        "title": "TransactionCancelationRequested",
        "schemas": [
            TransactionCancelationRequestedSyncSuccessSchema,
            TransactionCancelationRequestedSyncFailureSchema,
            TransactionCancelationRequestedAsyncSchema,
        ],
    },
    {
        "title": "TransactionInitializeSession",
        "schemas": [
            TransactionSessionSuccessSchema,
            TransactionSessionFailureSchema,
            TransactionSessionActionRequiredSchema,
        ],
    },
    {
        "title": "TransactionProcessSession",
        "schemas": [
            TransactionSessionSuccessSchema,
            TransactionSessionFailureSchema,
            TransactionSessionActionRequiredSchema,
        ],
    },
    # payment
    {
        "title": "PaymentGatewayInitializeTokenizationSession",
        "schemas": [
            PaymentMethodTokenizationSuccessSchema,
            PaymentMethodTokenizationPendingSchema,
            PaymentMethodTokenizationFailedSchema,
        ],
    },
]
