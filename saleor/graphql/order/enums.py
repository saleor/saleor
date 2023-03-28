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
    error_codes,
)
from ..core.descriptions import PREVIEW_FEATURE_DEPRECATED_IN_313_FIELD


def order_event_enum_description(enum):
    if enum is None:
        return "The different order event types. "
    if enum == OrderEventsEnum.TRANSACTION_VOID_REQUESTED:
        return (
            f"{PREVIEW_FEATURE_DEPRECATED_IN_313_FIELD} "
            "Use `TRANSACTION_CANCEL_REQUESTED` instead."
        )
    if enum == OrderEventsEnum.TRANSACTION_CAPTURE_REQUESTED:
        return (
            f"{PREVIEW_FEATURE_DEPRECATED_IN_313_FIELD} "
            "Use `TRANSACTION_CHARGE_REQUESTED` instead."
        )
    return None


FulfillmentStatusEnum = to_enum(FulfillmentStatus, type_name="FulfillmentStatus")
OrderEventsEnum = to_enum(OrderEvents, description=order_event_enum_description)
OrderEventsEmailsEnum = to_enum(OrderEventsEmails)
OrderOriginEnum = to_enum(OrderOrigin)
OrderStatusEnum = to_enum(OrderStatus, type_name="OrderStatus")
OrderAuthorizeStatusEnum = to_enum(
    OrderAuthorizeStatus, description=OrderAuthorizeStatus.__doc__
)
OrderChargeStatusEnum = to_enum(
    OrderChargeStatus, description=OrderChargeStatus.__doc__
)

OrderGrantRefundCreateErrorCode = graphene.Enum.from_enum(
    error_codes.OrderGrantRefundCreateErrorCode
)
OrderGrantRefundUpdateErrorCode = graphene.Enum.from_enum(
    error_codes.OrderGrantRefundUpdateErrorCode
)


class OrderStatusFilter(graphene.Enum):
    READY_TO_FULFILL = "ready_to_fulfill"
    READY_TO_CAPTURE = "ready_to_capture"
    UNFULFILLED = "unfulfilled"
    UNCONFIRMED = "unconfirmed"
    PARTIALLY_FULFILLED = "partially fulfilled"
    FULFILLED = "fulfilled"
    CANCELED = "canceled"
