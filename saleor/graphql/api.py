import graphene
from graphql_jwt.decorators import permission_required

from .account.schema import AccountMutations, AccountQueries
from .core.schema import CoreMutations
from .core.fields import PrefetchingConnectionField
from .menu.schema import MenuMutations, MenuQueries
from .discount.schema import DiscountMutations, DiscountQueries
from .order.schema import OrderMutations, OrderQueries
from .page.schema import PageMutations, PageQueries
from .product.schema import ProductMutations, ProductQueries
from .payment.schema import PaymentMutations, PaymentQueries
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
            MenuQueries, OrderQueries, PageQueries, PaymentQueries):
    shop = graphene.Field(Shop, description='Represents a shop resources.')
    shipping_zone = graphene.Field(
        ShippingZone, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a shipping zone by ID.')
    shipping_zones = PrefetchingConnectionField(
        ShippingZone, description='List of the shop\'s shipping zones.')
    node = graphene.Node.Field()

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
                OrderMutations, PageMutations, PaymentMutations):
    authorization_key_add = AuthorizationKeyAdd.Field()
    authorization_key_delete = AuthorizationKeyDelete.Field()

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
