import graphene

from ... import order as order_module
from ...graphql.core.enums import to_enum

OrderEventsEnum = to_enum(order_module.OrderEvents)
OrderEventsEmailsEnum = to_enum(order_module.OrderEventsEmails)
OrderEventsDiscount = to_enum(order_module.OrderEventsDiscount)


class OrderStatusFilter(graphene.Enum):
    READY_TO_FULFILL = "ready_to_fulfill"
    READY_TO_CAPTURE = "ready_to_capture"
    UNFULFILLED = "unfulfilled"
    UNCONFIRMED = "unconfirmed"
    PARTIALLY_FULFILLED = "partially fulfilled"
    FULFILLED = "fulfilled"
    CANCELED = "canceled"
