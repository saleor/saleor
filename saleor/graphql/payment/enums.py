import graphene

from ...payment import (
    ChargeStatus,
    StorePaymentMethod,
    TransactionAction,
    TransactionKind,
    TransactionStatus,
)
from ..core.enums import to_enum

TransactionKindEnum = to_enum(TransactionKind, type_name="TransactionKind")
PaymentChargeStatusEnum = to_enum(ChargeStatus, type_name="PaymentChargeStatusEnum")
TransactionActionEnum = to_enum(
    TransactionAction,
    type_name="TransactionActionEnum",
    description=TransactionAction.__doc__,
)
TransactionStatusEnum = to_enum(TransactionStatus, type_name="TransactionStatus")


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
        raise ValueError("Unsupported enum value: %s" % self.value)


def description(enum):
    if enum is None:
        return "Enum representing the type of a payment storage in a gateway."
    elif enum == StorePaymentMethodEnum.NONE:
        return "Storage is disabled. The payment is not stored."
    elif enum == StorePaymentMethodEnum.ON_SESSION:
        return (
            "On session storage type. "
            "The payment is stored only to be reused when "
            "the customer is present in the checkout flow."
        )
    elif enum == StorePaymentMethodEnum.OFF_SESSION:
        return (
            "Off session storage type. "
            "The payment is stored to be reused even if the customer is absent."
        )
    return None


StorePaymentMethodEnum = to_enum(
    StorePaymentMethod, type_name="StorePaymentMethodEnum", description=description
)
