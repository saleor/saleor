from textwrap import dedent

import graphene
from graphql_jwt.decorators import login_required, permission_required

from ..core.fields import PrefetchingConnectionField
from ..core.enums import ReportingPeriod
from ..core.types import TaxedMoney
from ..descriptions import DESCRIPTIONS
from .enums import OrderStatusFilter
from .mutations.draft_orders import (
    DraftOrderComplete, DraftOrderCreate, DraftOrderDelete,
    DraftOrderLineCreate, DraftOrderLineDelete, DraftOrderLineUpdate,
    DraftOrderUpdate)
from .mutations.fulfillments import (
    FulfillmentCancel, FulfillmentCreate, FulfillmentUpdateTracking)
from .mutations.orders import (
    OrderAddNote, OrderCancel, OrderCapture, OrderMarkAsPaid, OrderRefund,
    OrderUpdate, OrderUpdateShipping, OrderVoid)
from .resolvers import (
    resolve_homepage_events, resolve_order, resolve_orders,
    resolve_orders_total)
from .types import Order, OrderEvent


class OrderQueries(graphene.ObjectType):
    homepage_events = PrefetchingConnectionField(
        OrderEvent, description=dedent('''List of activity events to display on
        homepage (at the moment it only contains order-events).'''))
    order = graphene.Field(
        Order, description='Lookup an order by ID.',
        id=graphene.Argument(graphene.ID, required=True))
    orders = PrefetchingConnectionField(
        Order,
        query=graphene.String(description=DESCRIPTIONS['order']),
        created=graphene.Argument(
            ReportingPeriod,
            description='Filter orders from a selected timespan.'),
        status=graphene.Argument(
            OrderStatusFilter, description='Filter order by status'),
        description='List of the shop\'s orders.')
    orders_total = graphene.Field(
        TaxedMoney, description='Total sales.',
        period=graphene.Argument(
            ReportingPeriod,
            description='Get total sales for selected span of time.'))

    @permission_required('order.manage_orders')
    def resolve_homepage_events(self, info, **kwargs):
        return resolve_homepage_events(info)

    @login_required
    def resolve_order(self, info, id):
        return resolve_order(info, id)

    @login_required
    def resolve_orders(
            self, info, created=None, status=None, query=None, **kwargs):
        return resolve_orders(info, created, status, query)

    @permission_required('order.manage_orders')
    def resolve_orders_total(self, info, period, **kwargs):
        return resolve_orders_total(info, period)


class OrderMutations(graphene.ObjectType):
    draft_order_complete = DraftOrderComplete.Field()
    draft_order_create = DraftOrderCreate.Field()
    draft_order_delete = DraftOrderDelete.Field()
    draft_order_line_create = DraftOrderLineCreate.Field()
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
