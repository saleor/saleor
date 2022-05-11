import graphene

from ...core.permissions import OrderPermissions
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import DEPRECATED_IN_3X_FIELD
from ..core.enums import ReportingPeriod
from ..core.fields import ConnectionField, FilterConnectionField, PermissionsField
from ..core.scalars import UUID
from ..core.types import FilterInputObjectType, TaxedMoney
from ..core.utils import from_global_id_or_error
from .bulk_mutations.draft_orders import DraftOrderBulkDelete, DraftOrderLinesBulkDelete
from .bulk_mutations.orders import OrderBulkCancel
from .filters import DraftOrderFilter, OrderFilter
from .mutations.discount_order import (
    OrderDiscountAdd,
    OrderDiscountDelete,
    OrderDiscountUpdate,
    OrderLineDiscountRemove,
    OrderLineDiscountUpdate,
)
from .mutations.draft_orders import (
    DraftOrderComplete,
    DraftOrderCreate,
    DraftOrderDelete,
    DraftOrderUpdate,
)
from .mutations.fulfillments import (
    FulfillmentApprove,
    FulfillmentCancel,
    FulfillmentRefundProducts,
    FulfillmentReturnProducts,
    FulfillmentUpdateTracking,
    OrderFulfill,
)
from .mutations.orders import (
    OrderAddNote,
    OrderCancel,
    OrderCapture,
    OrderConfirm,
    OrderLineDelete,
    OrderLinesCreate,
    OrderLineUpdate,
    OrderMarkAsPaid,
    OrderRefund,
    OrderUpdate,
    OrderUpdateShipping,
    OrderVoid,
)
from .resolvers import (
    resolve_draft_orders,
    resolve_homepage_events,
    resolve_order,
    resolve_order_by_token,
    resolve_orders,
    resolve_orders_total,
)
from .sorters import OrderSortingInput
from .types import Order, OrderCountableConnection, OrderEventCountableConnection


class OrderFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = OrderFilter


class OrderDraftFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = DraftOrderFilter


class OrderQueries(graphene.ObjectType):
    homepage_events = ConnectionField(
        OrderEventCountableConnection,
        description=(
            "List of activity events to display on "
            "homepage (at the moment it only contains order-events)."
        ),
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
    )
    order = graphene.Field(
        Order,
        description="Look up an order by ID.",
        id=graphene.Argument(graphene.ID, description="ID of an order.", required=True),
    )
    orders = FilterConnectionField(
        OrderCountableConnection,
        sort_by=OrderSortingInput(description="Sort orders."),
        filter=OrderFilterInput(description="Filtering options for orders."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of orders.",
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
    )
    draft_orders = FilterConnectionField(
        OrderCountableConnection,
        sort_by=OrderSortingInput(description="Sort draft orders."),
        filter=OrderDraftFilterInput(description="Filtering options for draft orders."),
        description="List of draft orders.",
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
    )
    orders_total = PermissionsField(
        TaxedMoney,
        description="Return the total sales amount from a specific period.",
        period=graphene.Argument(ReportingPeriod, description="A period of time."),
        channel=graphene.Argument(
            graphene.String,
            description="Slug of a channel for which the data should be returned.",
        ),
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
    )
    order_by_token = graphene.Field(
        Order,
        description="Look up an order by token.",
        deprecation_reason=DEPRECATED_IN_3X_FIELD,
        token=graphene.Argument(UUID, description="The order's token.", required=True),
    )

    @staticmethod
    def resolve_homepage_events(_root, info, **kwargs):
        qs = resolve_homepage_events()
        return create_connection_slice(qs, info, kwargs, OrderEventCountableConnection)

    @staticmethod
    def resolve_order(_root, _info, **data):
        _, id = from_global_id_or_error(data.get("id"), Order)
        return resolve_order(id)

    @staticmethod
    def resolve_orders(_root, info, *, channel=None, **kwargs):
        qs = resolve_orders(info, channel)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, OrderCountableConnection)

    @staticmethod
    def resolve_draft_orders(_root, info, **kwargs):
        qs = resolve_draft_orders(info)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, OrderCountableConnection)

    @staticmethod
    def resolve_orders_total(_root, info, *, period, channel=None):
        return resolve_orders_total(info, period, channel)

    @staticmethod
    def resolve_order_by_token(_root, _info, *, token):
        return resolve_order_by_token(token)


class OrderMutations(graphene.ObjectType):
    draft_order_complete = DraftOrderComplete.Field()
    draft_order_create = DraftOrderCreate.Field()
    draft_order_delete = DraftOrderDelete.Field()
    draft_order_bulk_delete = DraftOrderBulkDelete.Field()
    draft_order_lines_bulk_delete = DraftOrderLinesBulkDelete.Field(
        deprecation_reason=DEPRECATED_IN_3X_FIELD
    )
    draft_order_update = DraftOrderUpdate.Field()

    order_add_note = OrderAddNote.Field()
    order_cancel = OrderCancel.Field()
    order_capture = OrderCapture.Field()
    order_confirm = OrderConfirm.Field()

    order_fulfill = OrderFulfill.Field()
    order_fulfillment_cancel = FulfillmentCancel.Field()
    order_fulfillment_approve = FulfillmentApprove.Field()
    order_fulfillment_update_tracking = FulfillmentUpdateTracking.Field()
    order_fulfillment_refund_products = FulfillmentRefundProducts.Field()
    order_fulfillment_return_products = FulfillmentReturnProducts.Field()

    order_lines_create = OrderLinesCreate.Field()
    order_line_delete = OrderLineDelete.Field()
    order_line_update = OrderLineUpdate.Field()

    order_discount_add = OrderDiscountAdd.Field()
    order_discount_update = OrderDiscountUpdate.Field()
    order_discount_delete = OrderDiscountDelete.Field()

    order_line_discount_update = OrderLineDiscountUpdate.Field()
    order_line_discount_remove = OrderLineDiscountRemove.Field()

    order_mark_as_paid = OrderMarkAsPaid.Field()
    order_refund = OrderRefund.Field()
    order_update = OrderUpdate.Field()
    order_update_shipping = OrderUpdateShipping.Field()
    order_void = OrderVoid.Field()
    order_bulk_cancel = OrderBulkCancel.Field()
