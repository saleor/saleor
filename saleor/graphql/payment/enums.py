import graphene

from ...graphql.core.enums import to_enum
from ...payment import ChargeStatus

PaymentChargeStatusEnum = to_enum(ChargeStatus, type_name="PaymentChargeStatusEnum")


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
