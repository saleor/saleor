import graphene

from ...order import OrderEvents, OrderEventsEmails

OrderEventsEnum = graphene.Enum.from_enum(OrderEvents)
OrderEventsEmailsEnum = graphene.Enum.from_enum(OrderEventsEmails)


class OrderStatusFilter(graphene.Enum):
    READY_TO_FULFILL = 'ready_to_fulfill'
    READY_TO_CAPTURE = 'ready_to_capture'
    UNFULFILLED = 'unfulfilled'
    PARTIALLY_FULFILLED = 'partially fulfilled'
    FULFILLED = 'fulfilled'
    CANCELED = 'canceled'
