import graphene
from graphene_federation import build_schema

from .account.schema import AccountMutations, AccountQueries
from .checkout.schema import CheckoutMutations, CheckoutQueries
from .core.schema import CoreMutations, CoreQueries
from .discount.schema import DiscountMutations, DiscountQueries
from .extensions.schema import ExtensionsMutations, ExtensionsQueries
from .giftcard.schema import GiftCardMutations, GiftCardQueries
from .menu.schema import MenuMutations, MenuQueries
from .order.schema import OrderMutations, OrderQueries
from .page.schema import PageMutations, PageQueries
from .payment.schema import PaymentMutations, PaymentQueries
from .product.schema import ProductMutations, ProductQueries
from .shipping.schema import ShippingMutations, ShippingQueries
from .shop.schema import ShopMutations, ShopQueries
from .translations.schema import TranslationQueries
from .webhook.schema import WebhookMutations, WebhookQueries


class Query(
    AccountQueries,
    CheckoutQueries,
    CoreQueries,
    DiscountQueries,
    ExtensionsQueries,
    GiftCardQueries,
    MenuQueries,
    OrderQueries,
    PageQueries,
    PaymentQueries,
    ProductQueries,
    ShippingQueries,
    ShopQueries,
    TranslationQueries,
    WebhookQueries,
):
    node = graphene.Node.Field()


class Mutation(
    AccountMutations,
    CheckoutMutations,
    CoreMutations,
    DiscountMutations,
    ExtensionsMutations,
    GiftCardMutations,
    MenuMutations,
    OrderMutations,
    PageMutations,
    PaymentMutations,
    ProductMutations,
    ShippingMutations,
    ShopMutations,
    WebhookMutations,
):
    pass


schema = build_schema(Query, mutation=Mutation)
