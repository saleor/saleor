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
from ..directives import doc


def order_event_enum_description(enum):
    if enum is None:
        return "The different order event types. "
    return None


FulfillmentStatusEnum = doc(
    DOC_CATEGORY_ORDERS, to_enum(FulfillmentStatus, type_name="FulfillmentStatus")
)

OrderEventsEnum = doc(
    DOC_CATEGORY_ORDERS, to_enum(OrderEvents, description=order_event_enum_description)
)

OrderEventsEmailsEnum = doc(DOC_CATEGORY_ORDERS, to_enum(OrderEventsEmails))

OrderOriginEnum = doc(DOC_CATEGORY_ORDERS, to_enum(OrderOrigin))

OrderStatusEnum = doc(
    DOC_CATEGORY_ORDERS, to_enum(OrderStatus, type_name="OrderStatus")
)

OrderAuthorizeStatusEnum = doc(
    DOC_CATEGORY_ORDERS,
    to_enum(OrderAuthorizeStatus, description=OrderAuthorizeStatus.__doc__),
)

OrderChargeStatusEnum = to_enum(
    OrderChargeStatus, description=OrderChargeStatus.__doc__
)

StockUpdatePolicyEnum = doc(
    DOC_CATEGORY_ORDERS,
    to_enum(StockUpdatePolicy, description=StockUpdatePolicy.__doc__),
)

OrderGrantRefundCreateErrorCode = graphene.Enum.from_enum(
    error_codes.OrderGrantRefundCreateErrorCode
)

OrderGrantRefundCreateLineErrorCode = graphene.Enum.from_enum(
    error_codes.OrderGrantRefundCreateLineErrorCode
)

OrderGrantRefundUpdateLineErrorCode = doc(
    DOC_CATEGORY_ORDERS,
    graphene.Enum.from_enum(error_codes.OrderGrantRefundUpdateLineErrorCode),
)

OrderGrantRefundUpdateErrorCode = doc(
    DOC_CATEGORY_ORDERS,
    graphene.Enum.from_enum(error_codes.OrderGrantRefundUpdateErrorCode),
)

OrderGrantedRefundStatusEnum = doc(
    DOC_CATEGORY_ORDERS,
    to_enum(OrderGrantedRefundStatus, description=OrderGrantedRefundStatus.__doc__),
)


@doc(category=DOC_CATEGORY_ORDERS)
class OrderStatusFilter(graphene.Enum):
    READY_TO_FULFILL = "ready_to_fulfill"
    READY_TO_CAPTURE = "ready_to_capture"
    UNFULFILLED = "unfulfilled"
    UNCONFIRMED = "unconfirmed"
    PARTIALLY_FULFILLED = "partially fulfilled"
    FULFILLED = "fulfilled"
    CANCELED = "canceled"
