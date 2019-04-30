import graphene
from graphql_jwt.decorators import login_required, permission_required

from ..core.enums import ReportingPeriod
from ..core.fields import (
    FilterInputConnectionField, PrefetchingConnectionField)
from ..core.types import FilterInputObjectType, TaxedMoney
from ..descriptions import DESCRIPTIONS
from .bulk_mutations.draft_orders import (
    DraftOrderBulkDelete, DraftOrderLinesBulkDelete)
from .bulk_mutations.orders import OrderBulkCancel
from .enums import OrderStatusFilter
from .filters import DraftOrderFilter, OrderFilter
from .mutations.draft_orders import (
    DraftOrderComplete, DraftOrderCreate, DraftOrderDelete,
    DraftOrderLineDelete, DraftOrderLinesCreate, DraftOrderLineUpdate,
    DraftOrderUpdate)
from .mutations.fulfillments import (
    FulfillmentCancel, FulfillmentCreate, FulfillmentUpdateTracking)
from .mutations.orders import (
    OrderAddNote, OrderCancel, OrderCapture, OrderMarkAsPaid, OrderRefund,
    OrderUpdate, OrderUpdateShipping, OrderVoid)
from .resolvers import (
    resolve_draft_orders, resolve_homepage_events, resolve_order,
    resolve_order_by_token, resolve_orders, resolve_orders_total)
from .types import Order, OrderEvent


class OrderFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = OrderFilter


class OrderDraftFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = DraftOrderFilter


class OrderQueries(graphene.ObjectType):
    homepage_events = PrefetchingConnectionField(
        OrderEvent, description='''List of activity events to display on
        homepage (at the moment it only contains order-events).''')
    order = graphene.Field(
        Order, description='Lookup an order by ID.',
        id=graphene.Argument(graphene.ID, required=True))
    orders = FilterInputConnectionField(
        Order,
        filter=OrderFilterInput(),
        query=graphene.String(description=DESCRIPTIONS['order']),
        created=graphene.Argument(
            ReportingPeriod,
            description='Filter orders from a selected timespan.'),
        status=graphene.Argument(
            OrderStatusFilter, description='Filter order by status'),
        description='List of the shop\'s orders.')
    draft_orders = FilterInputConnectionField(
        Order,
        filter=OrderDraftFilterInput(),
        query=graphene.String(description=DESCRIPTIONS['order']),
        created=graphene.Argument(
            ReportingPeriod,
            description='Filter draft orders from a selected timespan.'),
        description='List of the shop\'s draft orders.')
    orders_total = graphene.Field(
        TaxedMoney, description='Total sales.',
        period=graphene.Argument(
            ReportingPeriod,
            description='Get total sales for selected span of time.'))
    order_by_token = graphene.Field(
        Order, description='Lookup an order by token.',
        token=graphene.Argument(graphene.String, required=True))

    @permission_required('order.manage_orders')
    def resolve_homepage_events(self, *_args, **_kwargs):
        return resolve_homepage_events()

    @login_required
    def resolve_order(self, info, **data):
        return resolve_order(info, data.get('id'))

    @permission_required('order.manage_orders')
    def resolve_orders(
            self, info, created=None, status=None, query=None, **_kwargs):
        return resolve_orders(info, created, status, query)

    @permission_required('order.manage_orders')
    def resolve_draft_orders(self, info, created=None, query=None, **_kwargs):
        return resolve_draft_orders(info, created, query)

    @permission_required('order.manage_orders')
    def resolve_orders_total(self, info, period, **_kwargs):
        return resolve_orders_total(info, period)

    def resolve_order_by_token(self, _info, token):
        return resolve_order_by_token(token)


class OrderMutations(graphene.ObjectType):
    draft_order_complete = DraftOrderComplete.Field()
    draft_order_create = DraftOrderCreate.Field()
    draft_order_delete = DraftOrderDelete.Field()
    draft_order_bulk_delete = DraftOrderBulkDelete.Field()
    draft_order_lines_bulk_delete = DraftOrderLinesBulkDelete.Field()
    draft_order_lines_create = DraftOrderLinesCreate.Field()
    draft_order_line_delete = DraftOrderLineDelete.Field()
    draft_order_line_update = DraftOrderLineUpdate.Field()
    draft_order_update = DraftOrderUpdate.Field()

    order_add_note = OrderAddNote.Field()
    order_cancel = OrderCancel.Field()
    order_capture = OrderCapture.Field()
    order_fulfillment_cancel = FulfillmentCancel.Field()
    order_fulfillment_create = FulfillmentCreate.Field()
    order_fulfillment_update_tracking = FulfillmentUpdateTracking.Field()
    order_mark_as_paid = OrderMarkAsPaid.Field()
    order_refund = OrderRefund.Field()
    order_update = OrderUpdate.Field()
    order_update_shipping = OrderUpdateShipping.Field()
    order_void = OrderVoid.Field()

    order_bulk_cancel = OrderBulkCancel.Field()
