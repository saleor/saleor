import graphene

from ...events import OrderEvents, OrderEventsEmails
from ...graphql.core.enums import to_enum

OrderEventsEnum = to_enum(OrderEvents)
OrderEventsEmailsEnum = to_enum(OrderEventsEmails)


class OrderStatusFilter(graphene.Enum):
    READY_TO_FULFILL = 'ready_to_fulfill'
    READY_TO_CAPTURE = 'ready_to_capture'
    UNFULFILLED = 'unfulfilled'
    PARTIALLY_FULFILLED = 'partially fulfilled'
    FULFILLED = 'fulfilled'
    CANCELED = 'canceled'
