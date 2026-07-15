from ...api import schema
from ...core.descriptions import DEPRECATED_LEGACY_PAYMENTS

DEPRECATED_FIELDS = {
    "Query": ["payment", "payments"],
    "Mutation": [
        "checkoutPaymentCreate",
        "orderCapture",
        "orderRefund",
        "orderVoid",
        "paymentCapture",
        "paymentCheckBalance",
        "paymentInitialize",
        "paymentRefund",
        "paymentVoid",
    ],
    "Checkout": ["availablePaymentGateways"],
    "Order": ["payments"],
    "PaymentAuthorize": ["payment"],
    "PaymentCaptureEvent": ["payment"],
    "PaymentConfirmEvent": ["payment"],
    "PaymentProcessEvent": ["payment"],
    "PaymentRefundEvent": ["payment"],
    "PaymentVoidEvent": ["payment"],
    "Shop": ["availablePaymentGateways"],
    "Transaction": ["gatewayResponse"],
    "User": ["storedPaymentSources"],
}

DEPRECATED_ENUM_VALUES = {
    "CheckoutSortField": ["PAYMENT"],
    "MarkAsPaidStrategyEnum": ["PAYMENT_FLOW"],
    "OrderAction": ["CAPTURE", "REFUND", "VOID"],
    "OrderSortField": ["PAYMENT"],
    "StorePaymentMethodEnum": ["NONE", "OFF_SESSION", "ON_SESSION"],
    "TransactionKind": [
        "ACTION_TO_CONFIRM",
        "AUTH",
        "CANCEL",
        "CAPTURE",
        "CONFIRM",
        "EXTERNAL",
        "PENDING",
        "REFUND",
        "REFUND_ONGOING",
        "VOID",
    ],
    "WebhookEventTypeEnum": [
        "PAYMENT_AUTHORIZE",
        "PAYMENT_CAPTURE",
        "PAYMENT_CONFIRM",
        "PAYMENT_LIST_GATEWAYS",
        "PAYMENT_PROCESS",
        "PAYMENT_REFUND",
        "PAYMENT_VOID",
    ],
    "WebhookEventTypeSyncEnum": [
        "PAYMENT_AUTHORIZE",
        "PAYMENT_CAPTURE",
        "PAYMENT_CONFIRM",
        "PAYMENT_LIST_GATEWAYS",
        "PAYMENT_PROCESS",
        "PAYMENT_REFUND",
        "PAYMENT_VOID",
    ],
}

DEPRECATED_TYPE_DESCRIPTIONS = [
    "CardInput",
    "Payment",
    "PaymentAuthorize",
    "PaymentCaptureEvent",
    "PaymentCheckBalanceInput",
    "PaymentConfirmEvent",
    "PaymentFilterInput",
    "PaymentInitialized",
    "PaymentInput",
    "PaymentListGateways",
    "PaymentProcessEvent",
    "PaymentRefundEvent",
    "PaymentSource",
    "PaymentVoidEvent",
    "Transaction",
]

TRANSACTIONS_API_FIELDS = {
    "Checkout": ["storedPaymentMethods", "transactions"],
    "Mutation": [
        "paymentGatewayInitialize",
        "transactionCreate",
        "transactionEventReport",
        "transactionInitialize",
        "transactionProcess",
        "transactionRequestAction",
        "transactionRequestRefundForGrantedRefund",
        "transactionUpdate",
    ],
    "Order": ["transactions"],
    "Query": ["transaction", "transactions"],
    "StoredPaymentMethod": ["gateway"],
    "User": ["storedPaymentMethods"],
}


def test_legacy_payment_fields_are_deprecated():
    for type_name, field_names in DEPRECATED_FIELDS.items():
        graphql_type = schema.get_type(type_name)

        for field_name in field_names:
            field = graphql_type.fields[field_name]

            assert field.deprecation_reason == DEPRECATED_LEGACY_PAYMENTS


def test_legacy_payment_enum_values_are_deprecated():
    for type_name, value_names in DEPRECATED_ENUM_VALUES.items():
        graphql_type = schema.get_type(type_name)
        enum_values = {value.name: value for value in graphql_type.values}

        for value_name in value_names:
            value = enum_values[value_name]

            assert value.deprecation_reason == DEPRECATED_LEGACY_PAYMENTS


def test_legacy_payment_types_have_deprecation_description():
    for type_name in DEPRECATED_TYPE_DESCRIPTIONS:
        graphql_type = schema.get_type(type_name)

        assert DEPRECATED_LEGACY_PAYMENTS in graphql_type.description


def test_order_payment_status_filter_has_deprecation_description():
    graphql_type = schema.get_type("OrderFilterInput")

    field = graphql_type.fields["paymentStatus"]

    assert field.description == DEPRECATED_LEGACY_PAYMENTS


def test_shared_payment_gateway_type_is_not_deprecated():
    graphql_type = schema.get_type("PaymentGateway")

    assert DEPRECATED_LEGACY_PAYMENTS not in graphql_type.description


def test_transactions_api_fields_are_not_deprecated():
    for type_name, field_names in TRANSACTIONS_API_FIELDS.items():
        graphql_type = schema.get_type(type_name)

        for field_name in field_names:
            field = graphql_type.fields[field_name]

            assert field.deprecation_reason is None
