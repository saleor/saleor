from textwrap import dedent

import graphene
from graphql_jwt.decorators import login_required, permission_required

from .account.schema import AccountMutations, AccountQueries
from .core.schema import CoreMutations
from .core.types import TaxedMoney, ReportingPeriod
from .core.fields import PrefetchingConnectionField
from .menu.schema import MenuMutations, MenuQueries
from .descriptions import DESCRIPTIONS
from .discount.schema import DiscountMutations, DiscountQueries
from .order.mutations.draft_orders import (
    DraftOrderComplete, DraftOrderCreate, DraftOrderDelete,
    DraftOrderLineCreate, DraftOrderLineDelete, DraftOrderLineUpdate,
    DraftOrderUpdate)
from .order.mutations.fulfillments import (
    FulfillmentCancel, FulfillmentCreate, FulfillmentUpdateTracking)
from .order.mutations.orders import (
    OrderAddNote, OrderCancel, OrderCapture, OrderMarkAsPaid, OrderRefund,
    OrderVoid, OrderUpdate, OrderUpdateShipping)
from .order.resolvers import (
    resolve_homepage_events, resolve_order, resolve_orders,
    resolve_orders_total)
from .order.types import Order, OrderEvent, OrderStatusFilter
from .page.mutations import PageCreate, PageDelete, PageUpdate
from .page.resolvers import resolve_page, resolve_pages
from .page.types import Page
from .product.schema import ProductMutations, ProductQueries
from .payment.types import Payment, PaymentGatewayEnum
from .payment.resolvers import (
    resolve_payments, resolve_payment_client_token)
from .payment.mutations import (
    PaymentCapture, PaymentRefund,
    PaymentVoid)
from .shipping.resolvers import resolve_shipping_zones
from .shipping.types import ShippingZone
from .shipping.mutations import (
    ShippingZoneCreate, ShippingZoneDelete, ShippingZoneUpdate,
    ShippingPriceCreate, ShippingPriceDelete, ShippingPriceUpdate)
from .checkout.schema import CheckoutMutations, CheckoutQueries

from .shop.mutations import (
    AuthorizationKeyAdd, AuthorizationKeyDelete, HomepageCollectionUpdate,
    ShopDomainUpdate, ShopSettingsUpdate)
from .shop.types import Shop


class Query(ProductQueries, AccountQueries, CheckoutQueries, DiscountQueries,
            MenuQueries):
    order = graphene.Field(
        Order, description='Lookup an order by ID.',
        id=graphene.Argument(graphene.ID, required=True))
    orders_total = graphene.Field(
        TaxedMoney, description='Total sales.',
        period=graphene.Argument(
            ReportingPeriod,
            description='Get total sales for selected span of time.'))
    orders = PrefetchingConnectionField(
        Order,
        query=graphene.String(description=DESCRIPTIONS['order']),
        created=graphene.Argument(
            ReportingPeriod,
            description='Filter orders from a selected timespan.'),
        status=graphene.Argument(
            OrderStatusFilter, description='Filter order by status'),
        description='List of the shop\'s orders.')
    homepage_events = PrefetchingConnectionField(
        OrderEvent, description=dedent('''List of activity events to display on
        homepage (at the moment it only contains order-events).'''))
    page = graphene.Field(
        Page, id=graphene.Argument(graphene.ID), slug=graphene.String(),
        description='Lookup a page by ID or by slug.')
    pages = PrefetchingConnectionField(
        Page, query=graphene.String(
            description=DESCRIPTIONS['page']),
        description='List of the shop\'s pages.')
    payment = graphene.Field(Payment, id=graphene.Argument(graphene.ID))
    payment_client_token = graphene.Field(
        graphene.String, args={'gateway': PaymentGatewayEnum()})
    payments = PrefetchingConnectionField(
        Payment, description='List of payments')
    shop = graphene.Field(Shop, description='Represents a shop resources.')
    shipping_zone = graphene.Field(
        ShippingZone, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a shipping zone by ID.')
    shipping_zones = PrefetchingConnectionField(
        ShippingZone, description='List of the shop\'s shipping zones.')
    node = graphene.Node.Field()

    def resolve_page(self, info, id=None, slug=None):
        return resolve_page(info, id, slug)

    def resolve_pages(self, info, query=None, **kwargs):
        return resolve_pages(info, query=query)

    @login_required
    def resolve_order(self, info, id):
        return resolve_order(info, id)

    @permission_required('order.manage_orders')
    def resolve_orders_total(self, info, period, **kwargs):
        return resolve_orders_total(info, period)

    @login_required
    def resolve_orders(self, info, query=None, **kwargs):
        return resolve_orders(info, query)

    def resolve_payment(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Payment)

    def resolve_payment_client_token(self, info, gateway=None):
        return resolve_payment_client_token(gateway)

    @permission_required('order.manage_orders')
    def resolve_payments(self, info, query=None, **kwargs):
        return resolve_payments(info, query)

    @login_required
    def resolve_orders(
            self, info, created=None, status=None, query=None, **kwargs):
        return resolve_orders(info, created, status, query)

    @permission_required('order.manage_orders')
    def resolve_homepage_events(self, info, **kwargs):
        return resolve_homepage_events(info)

    def resolve_shop(self, info):
        return Shop()

    @permission_required('shipping.manage_shipping')
    def resolve_shipping_zone(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ShippingZone)

    @permission_required('shipping.manage_shipping')
    def resolve_shipping_zones(self, info, **kwargs):
        return resolve_shipping_zones(info)


class Mutations(ProductMutations, AccountMutations, CheckoutMutations,
                CoreMutations, DiscountMutations, MenuMutations):
    authorization_key_add = AuthorizationKeyAdd.Field()
    authorization_key_delete = AuthorizationKeyDelete.Field()

    draft_order_create = DraftOrderCreate.Field()
    draft_order_complete = DraftOrderComplete.Field()
    draft_order_delete = DraftOrderDelete.Field()
    draft_order_line_create = DraftOrderLineCreate.Field()
    draft_order_line_delete = DraftOrderLineDelete.Field()
    draft_order_line_update = DraftOrderLineUpdate.Field()
    draft_order_update = DraftOrderUpdate.Field()
    order_fulfillment_cancel = FulfillmentCancel.Field()
    order_fulfillment_create = FulfillmentCreate.Field()
    order_fulfillment_update_tracking = FulfillmentUpdateTracking.Field()
    order_add_note = OrderAddNote.Field()
    order_cancel = OrderCancel.Field()
    order_capture = OrderCapture.Field()
    order_mark_as_paid = OrderMarkAsPaid.Field()
    order_update_shipping = OrderUpdateShipping.Field()
    order_refund = OrderRefund.Field()
    order_void = OrderVoid.Field()
    order_update = OrderUpdate.Field()

    page_create = PageCreate.Field()
    page_delete = PageDelete.Field()
    page_update = PageUpdate.Field()

    payment_capture = PaymentCapture.Field()
    payment_refund = PaymentRefund.Field()
    payment_void = PaymentVoid.Field()

    shop_domain_update = ShopDomainUpdate.Field()
    shop_settings_update = ShopSettingsUpdate.Field()
    homepage_collection_update = HomepageCollectionUpdate.Field()

    shipping_zone_create = ShippingZoneCreate.Field()
    shipping_zone_delete = ShippingZoneDelete.Field()
    shipping_zone_update = ShippingZoneUpdate.Field()

    shipping_price_create = ShippingPriceCreate.Field()
    shipping_price_delete = ShippingPriceDelete.Field()
    shipping_price_update = ShippingPriceUpdate.Field()


schema = graphene.Schema(Query, Mutations)
