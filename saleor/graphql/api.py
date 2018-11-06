import graphene

from .account.schema import AccountMutations, AccountQueries
from .core.schema import CoreMutations

from .menu.schema import MenuMutations, MenuQueries
from .discount.schema import DiscountMutations, DiscountQueries
from .order.schema import OrderMutations, OrderQueries
from .page.schema import PageMutations, PageQueries
from .product.schema import ProductMutations, ProductQueries
from .payment.schema import PaymentMutations, PaymentQueries
from .shipping.schema import ShippingMutations, ShippingQueries
from .checkout.schema import CheckoutMutations, CheckoutQueries

from .shop.mutations import (
    AuthorizationKeyAdd, AuthorizationKeyDelete, HomepageCollectionUpdate,
    ShopDomainUpdate, ShopSettingsUpdate)
from .shop.types import Shop


class Query(ProductQueries, AccountQueries, CheckoutQueries, DiscountQueries,
            MenuQueries, OrderQueries, PageQueries, PaymentQueries,
            ShippingQueries):
    shop = graphene.Field(Shop, description='Represents a shop resources.')
    node = graphene.Node.Field()

    def resolve_shop(self, info):
        return Shop()


class Mutations(ProductMutations, AccountMutations, CheckoutMutations,
                CoreMutations, DiscountMutations, MenuMutations,
                OrderMutations, PageMutations, PaymentMutations,
                ShippingMutations):
    authorization_key_add = AuthorizationKeyAdd.Field()
    authorization_key_delete = AuthorizationKeyDelete.Field()

    shop_domain_update = ShopDomainUpdate.Field()
    shop_settings_update = ShopSettingsUpdate.Field()
    homepage_collection_update = HomepageCollectionUpdate.Field()


schema = graphene.Schema(Query, Mutations)
