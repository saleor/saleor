import graphene

from ...order import OrderEvents, OrderEventsEmails

OrderEventsEnum = graphene.Enum.from_enum(OrderEvents)
OrderEventsEmailsEnum = graphene.Enum.from_enum(OrderEventsEmails)


class OrderStatusFilter(graphene.Enum):
    READY_TO_FULFILL = 'READY_TO_FULFILL'
    READY_TO_CAPTURE = 'READY_TO_CAPTURE'
