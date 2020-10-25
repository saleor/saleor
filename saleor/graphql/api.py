from django.conf import settings
from graphene_federation import build_schema

from .account.schema import AccountMutations, AccountQueries
from .app.schema import AppMutations, AppQueries
from .checkout.schema import CheckoutMutations, CheckoutQueries
from .core.schema import CoreQueries
from .csv.schema import CsvMutations, CsvQueries
from .discount.schema import DiscountMutations, DiscountQueries
from .giftcard.schema import GiftCardMutations, GiftCardQueries
from .invoice.schema import InvoiceMutations
from .menu.schema import MenuMutations, MenuQueries
from .meta.schema import MetaMutations
from .order.schema import OrderMutations, OrderQueries
from .page.schema import PageMutations, PageQueries
from .payment.schema import PaymentMutations, PaymentQueries
from .plugins.schema import PluginsMutations, PluginsQueries
from .product.schema import ProductMutations, ProductQueries
from .shipping.schema import ShippingMutations, ShippingQueries
from .shop.schema import ShopMutations, ShopQueries
from .translations.schema import TranslationQueries
from .warehouse.schema import StockQueries, WarehouseMutations, WarehouseQueries
from .webhook.schema import WebhookMutations, WebhookQueries

QUERY_CLASSES = (
    AccountQueries,
    AppQueries,
    CheckoutQueries,
    CoreQueries,
    CsvQueries,
    DiscountQueries,
    PluginsQueries,
    GiftCardQueries,
    MenuQueries,
    OrderQueries,
    PageQueries,
    PaymentQueries,
    ProductQueries,
    ShippingQueries,
    ShopQueries,
    StockQueries,
    TranslationQueries,
    WarehouseQueries,
    WebhookQueries,
)

MUTATION_CLASSES = (
    AccountMutations,
    AppMutations,
    CheckoutMutations,
    CsvMutations,
    DiscountMutations,
    PluginsMutations,
    GiftCardMutations,
    InvoiceMutations,
    MenuMutations,
    MetaMutations,
    OrderMutations,
    PageMutations,
    PaymentMutations,
    ProductMutations,
    ShippingMutations,
    ShopMutations,
    WarehouseMutations,
    WebhookMutations,
)

QUERY_CLASSES += getattr(settings, "GRAPHQL_QUERY_CLASSES", tuple())
MUTATION_CLASSES += getattr(settings, "GRAPHQL_MUTATION_CLASSES", tuple())

QueryClass = type("Query", QUERY_CLASSES, {})
MutationClass = type("Mutation", MUTATION_CLASSES, {})

schema = build_schema(QueryClass, mutation=MutationClass)
