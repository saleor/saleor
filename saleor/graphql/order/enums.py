from typing import Final

import graphene

from ...order import (
    FulfillmentStatus,
    OrderAuthorizeStatus,
    OrderChargeStatus,
    OrderEvents,
    OrderEventsEmails,
    OrderGrantedRefundStatus,
    OrderOrigin,
    OrderStatus,
    StockUpdatePolicy,
    error_codes,
)
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.enums import to_enum
from ..core.types import BaseEnum


def order_event_enum_description(enum):
    if enum is None:
        return "The different order event types. "
    return None


FulfillmentStatusEnum: Final[graphene.Enum] = to_enum(
    FulfillmentStatus, type_name="FulfillmentStatus"
)
FulfillmentStatusEnum.doc_category = DOC_CATEGORY_ORDERS

OrderEventsEnum: Final[graphene.Enum] = to_enum(
    OrderEvents, description=order_event_enum_description
)
OrderEventsEnum.doc_category = DOC_CATEGORY_ORDERS

OrderEventsEmailsEnum: Final[graphene.Enum] = to_enum(OrderEventsEmails)
OrderEventsEmailsEnum.doc_category = DOC_CATEGORY_ORDERS

OrderOriginEnum: Final[graphene.Enum] = to_enum(OrderOrigin)
OrderOriginEnum.doc_category = DOC_CATEGORY_ORDERS

OrderStatusEnum: Final[graphene.Enum] = to_enum(OrderStatus, type_name="OrderStatus")
OrderStatusEnum.doc_category = DOC_CATEGORY_ORDERS

OrderAuthorizeStatusEnum: Final[graphene.Enum] = to_enum(
    OrderAuthorizeStatus, description=OrderAuthorizeStatus.__doc__
)
OrderAuthorizeStatusEnum.doc_category = DOC_CATEGORY_ORDERS

OrderChargeStatusEnum: Final[graphene.Enum] = to_enum(
    OrderChargeStatus, description=OrderChargeStatus.__doc__
)
StockUpdatePolicyEnum: Final[graphene.Enum] = to_enum(
    StockUpdatePolicy, description=StockUpdatePolicy.__doc__
)
OrderChargeStatusEnum.doc_category = DOC_CATEGORY_ORDERS

OrderGrantRefundCreateErrorCode: Final[graphene.Enum] = graphene.Enum.from_enum(
    error_codes.OrderGrantRefundCreateErrorCode
)
OrderGrantRefundCreateLineErrorCode: Final[graphene.Enum] = graphene.Enum.from_enum(
    error_codes.OrderGrantRefundCreateLineErrorCode
)

OrderGrantRefundUpdateLineErrorCode: Final[graphene.Enum] = graphene.Enum.from_enum(
    error_codes.OrderGrantRefundUpdateLineErrorCode
)

OrderGrantRefundCreateErrorCode.doc_category = DOC_CATEGORY_ORDERS

OrderGrantRefundUpdateErrorCode: Final[graphene.Enum] = graphene.Enum.from_enum(
    error_codes.OrderGrantRefundUpdateErrorCode
)
OrderGrantRefundUpdateErrorCode.doc_category = DOC_CATEGORY_ORDERS


OrderGrantedRefundStatusEnum: Final[graphene.Enum] = to_enum(
    OrderGrantedRefundStatus, description=OrderGrantedRefundStatus.__doc__
)
OrderGrantedRefundStatusEnum.doc_category = DOC_CATEGORY_ORDERS


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
