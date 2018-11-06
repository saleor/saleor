import graphene

from .account.schema import AccountMutations, AccountQueries
from .checkout.schema import CheckoutMutations, CheckoutQueries
from .core.schema import CoreMutations
from .discount.schema import DiscountMutations, DiscountQueries
from .menu.schema import MenuMutations, MenuQueries
from .order.schema import OrderMutations, OrderQueries
from .page.schema import PageMutations, PageQueries
from .payment.schema import PaymentMutations, PaymentQueries
from .product.schema import ProductMutations, ProductQueries
from .shipping.schema import ShippingMutations, ShippingQueries
from .shop.schema import ShopMutations, ShopQueries


class Query(ProductQueries, AccountQueries, CheckoutQueries, DiscountQueries,
            MenuQueries, OrderQueries, PageQueries, PaymentQueries,
            ShippingQueries, ShopQueries):
    node = graphene.Node.Field()


class Mutations(ProductMutations, AccountMutations, CheckoutMutations,
                CoreMutations, DiscountMutations, MenuMutations,
                OrderMutations, PageMutations, PaymentMutations,
                ShippingMutations, ShopMutations):
    pass


schema = graphene.Schema(Query, Mutations)
