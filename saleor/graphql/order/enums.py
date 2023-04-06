import graphene

from ...order import (
    FulfillmentStatus,
    OrderAuthorizeStatus,
    OrderChargeStatus,
    OrderEvents,
    OrderEventsEmails,
    OrderOrigin,
    OrderStatus,
    StockUpdatePolicy,
    error_codes,
)
from ..core.descriptions import PREVIEW_FEATURE_DEPRECATED_IN_313_FIELD
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.enums import to_enum
from ..core.types import BaseEnum


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
FulfillmentStatusEnum.doc_category = DOC_CATEGORY_ORDERS

OrderEventsEnum = to_enum(OrderEvents, description=order_event_enum_description)
OrderEventsEnum.doc_category = DOC_CATEGORY_ORDERS

OrderEventsEmailsEnum = to_enum(OrderEventsEmails)
OrderEventsEmailsEnum.doc_category = DOC_CATEGORY_ORDERS

OrderOriginEnum = to_enum(OrderOrigin)
OrderOriginEnum.doc_category = DOC_CATEGORY_ORDERS

OrderStatusEnum = to_enum(OrderStatus, type_name="OrderStatus")
OrderStatusEnum.doc_category = DOC_CATEGORY_ORDERS

OrderAuthorizeStatusEnum = to_enum(
    OrderAuthorizeStatus, description=OrderAuthorizeStatus.__doc__
)
OrderAuthorizeStatusEnum.doc_category = DOC_CATEGORY_ORDERS

OrderChargeStatusEnum = to_enum(
    OrderChargeStatus, description=OrderChargeStatus.__doc__
)
StockUpdatePolicyEnum = to_enum(
    StockUpdatePolicy, description=StockUpdatePolicy.__doc__
)
OrderChargeStatusEnum.doc_category = DOC_CATEGORY_ORDERS

OrderGrantRefundCreateErrorCode = graphene.Enum.from_enum(
    error_codes.OrderGrantRefundCreateErrorCode
)
OrderGrantRefundCreateErrorCode.doc_category = DOC_CATEGORY_ORDERS

OrderGrantRefundUpdateErrorCode = graphene.Enum.from_enum(
    error_codes.OrderGrantRefundUpdateErrorCode
)
OrderGrantRefundUpdateErrorCode.doc_category = DOC_CATEGORY_ORDERS


class OrderStatusFilter(BaseEnum):
    READY_TO_FULFILL = "ready_to_fulfill"
    READY_TO_CAPTURE = "ready_to_capture"
    UNFULFILLED = "unfulfilled"
    UNCONFIRMED = "unconfirmed"
    PARTIALLY_FULFILLED = "partially fulfilled"
    FULFILLED = "fulfilled"
    CANCELED = "canceled"

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
