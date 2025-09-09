import graphene

from ...payment import (
    ChargeStatus,
    PaymentMethodType,
    StorePaymentMethod,
    TokenizedPaymentFlow,
    TransactionAction,
    TransactionEventType,
    TransactionKind,
)
from ...payment.interface import (
    PaymentGatewayInitializeTokenizationResult,
    PaymentMethodTokenizationResult,
    StoredPaymentMethodRequestDeleteResult,
)
from ..core.doc_category import DOC_CATEGORY_PAYMENTS
from ..core.enums import to_enum
from ..directives import doc

TransactionKindEnum = doc(
    DOC_CATEGORY_PAYMENTS, to_enum(TransactionKind, type_name="TransactionKind")
)

PaymentChargeStatusEnum = doc(
    DOC_CATEGORY_PAYMENTS, to_enum(ChargeStatus, type_name="PaymentChargeStatusEnum")
)

TransactionActionEnum = doc(
    DOC_CATEGORY_PAYMENTS,
    to_enum(
        TransactionAction,
        type_name="TransactionActionEnum",
        description=TransactionAction.__doc__,
    ),
)

TransactionEventTypeEnum = doc(
    DOC_CATEGORY_PAYMENTS,
    to_enum(TransactionEventType, description=TransactionEventType.__doc__),
)

PaymentMethodTypeEnum = doc(
    DOC_CATEGORY_PAYMENTS,
    field=to_enum(
        PaymentMethodType,
        type_name="PaymentMethodTypeEnum",
        description=PaymentMethodType.__doc__,
    ),
)


@doc(category=DOC_CATEGORY_PAYMENTS)
class OrderAction(graphene.Enum):
    CAPTURE = "CAPTURE"
    MARK_AS_PAID = "MARK_AS_PAID"
    REFUND = "REFUND"
    VOID = "VOID"

    @property
    def description(self):
        if self == OrderAction.CAPTURE:
            return "Represents the capture action."
        if self == OrderAction.MARK_AS_PAID:
            return "Represents a mark-as-paid action."
        if self == OrderAction.REFUND:
            return "Represents a refund action."
        if self == OrderAction.VOID:
            return "Represents a void action."
        raise ValueError(f"Unsupported enum value: {self.value}")


def description(enum):
    if enum is None:
        return "Enum representing the type of a payment storage in a gateway."
    if enum == StorePaymentMethodEnum.NONE:
        return "Storage is disabled. The payment is not stored."
    if enum == StorePaymentMethodEnum.ON_SESSION:
        return (
            "On session storage type. "
            "The payment is stored only to be reused when "
            "the customer is present in the checkout flow."
        )
    if enum == StorePaymentMethodEnum.OFF_SESSION:
        return (
            "Off session storage type. "
            "The payment is stored to be reused even if the customer is absent."
        )
    return None


StorePaymentMethodEnum = doc(
    DOC_CATEGORY_PAYMENTS,
    to_enum(
        StorePaymentMethod, type_name="StorePaymentMethodEnum", description=description
    ),
)

TokenizedPaymentFlowEnum = doc(
    DOC_CATEGORY_PAYMENTS,
    to_enum(
        TokenizedPaymentFlow,
        type_name="TokenizedPaymentFlowEnum",
        description=TokenizedPaymentFlow.__doc__,
    ),
)

PaymentGatewayInitializeTokenizationResultEnum = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(
        PaymentGatewayInitializeTokenizationResult,
    ),
)

PaymentMethodTokenizationResultEnum = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(PaymentMethodTokenizationResult),
)

StoredPaymentMethodRequestDeleteResultEnum = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(StoredPaymentMethodRequestDeleteResult),
)
