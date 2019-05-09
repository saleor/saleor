import graphene

from ...graphql.core.enums import to_enum
from ...order import OrderEvents, OrderEventsEmails

OrderEventsEnum = to_enum(OrderEvents)
OrderEventsEmailsEnum = to_enum(OrderEventsEmails)


class OrderStatusFilter(graphene.Enum):
    UNFULFILLED = 'unfulfilled'
    PARTIALLY_FULFILLED = 'partially fulfilled'
    FULFILLED = 'fulfilled'
    CANCELED = 'canceled'
    READY_TO_FULFILL = 'ready_to_fulfill'
    READY_TO_CAPTURE = 'ready_to_capture'
