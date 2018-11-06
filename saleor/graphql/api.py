from textwrap import dedent

import graphene
from graphql_jwt.decorators import login_required, permission_required

from .account.schema import AccountMutations, AccountQueries
from .core.schema import CoreMutations
from .core.fields import PrefetchingConnectionField
from .menu.schema import MenuMutations, MenuQueries
from .descriptions import DESCRIPTIONS
from .discount.schema import DiscountMutations, DiscountQueries
from .order.schema import OrderMutations, OrderQueries
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
            MenuQueries, OrderQueries):

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

    def resolve_payment(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Payment)

    def resolve_payment_client_token(self, info, gateway=None):
        return resolve_payment_client_token(gateway)

    @permission_required('order.manage_orders')
    def resolve_payments(self, info, query=None, **kwargs):
        return resolve_payments(info, query)

    def resolve_shop(self, info):
        return Shop()

    @permission_required('shipping.manage_shipping')
    def resolve_shipping_zone(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ShippingZone)

    @permission_required('shipping.manage_shipping')
    def resolve_shipping_zones(self, info, **kwargs):
        return resolve_shipping_zones(info)


class Mutations(ProductMutations, AccountMutations, CheckoutMutations,
                CoreMutations, DiscountMutations, MenuMutations,
                OrderMutations):
    authorization_key_add = AuthorizationKeyAdd.Field()
    authorization_key_delete = AuthorizationKeyDelete.Field()

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
