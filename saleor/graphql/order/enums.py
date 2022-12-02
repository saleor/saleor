import graphene

from ...graphql.core.enums import to_enum
from ...order import (
    FulfillmentStatus,
    OrderAuthorizeStatus,
    OrderChargeStatus,
    OrderEvents,
    OrderEventsEmails,
    OrderOrigin,
    OrderStatus,
)

FulfillmentStatusEnum = to_enum(FulfillmentStatus, type_name="FulfillmentStatus")
OrderEventsEnum = to_enum(OrderEvents)
OrderEventsEmailsEnum = to_enum(OrderEventsEmails)
OrderOriginEnum = to_enum(OrderOrigin)
OrderStatusEnum = to_enum(OrderStatus, type_name="OrderStatus")
OrderAuthorizeStatusEnum = to_enum(
    OrderAuthorizeStatus, description=OrderAuthorizeStatus.__doc__
)
OrderChargeStatusEnum = to_enum(
    OrderChargeStatus, description=OrderChargeStatus.__doc__
)


class OrderStatusFilter(graphene.Enum):
    READY_TO_FULFILL = "ready_to_fulfill"
    READY_TO_CAPTURE = "ready_to_capture"
    UNFULFILLED = "unfulfilled"
    UNCONFIRMED = "unconfirmed"
    PARTIALLY_FULFILLED = "partially fulfilled"
    FULFILLED = "fulfilled"
    CANCELED = "canceled"
