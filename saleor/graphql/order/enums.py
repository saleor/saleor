import graphene

from ...graphql.core.enums import to_enum
from ...order import OrderEvents, OrderEventsEmails, OrderOrigin, OrderPaymentStatus

OrderEventsEnum = to_enum(OrderEvents)
OrderEventsEmailsEnum = to_enum(OrderEventsEmails)
OrderOriginEnum = to_enum(OrderOrigin)
OrderPaymentStatusEnum = to_enum(OrderPaymentStatus)


class OrderStatusFilter(graphene.Enum):
    READY_TO_FULFILL = "ready_to_fulfill"
    READY_TO_CAPTURE = "ready_to_capture"
    UNFULFILLED = "unfulfilled"
    UNCONFIRMED = "unconfirmed"
    PARTIALLY_FULFILLED = "partially fulfilled"
    FULFILLED = "fulfilled"
    CANCELED = "canceled"
    OVERPAID = "overpaid"
