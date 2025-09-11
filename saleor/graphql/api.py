import enum

from django.urls import reverse
from django.utils.functional import SimpleLazyObject
from graphene_federation import LATEST_VERSION, build_schema
from graphql import GraphQLEnumType, GraphQLSchema

from ..graphql.notifications.schema import ExternalNotificationMutations
from .account.schema import AccountMutations, AccountQueries
from .app.schema import AppMutations, AppQueries
from .attribute.schema import AttributeMutations, AttributeQueries
from .channel.schema import ChannelMutations, ChannelQueries
from .checkout.schema import CheckoutMutations, CheckoutQueries
from .core.enums import unit_enums
from .core.schema import CoreMutations, CoreQueries
from .csv.schema import CsvMutations, CsvQueries
from .directives import DocDirective, WebhookEventsDirective
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
from .schema import patch_federation_schema
from .shipping.schema import ShippingMutations, ShippingQueries
from .shop.schema import ShopMutations, ShopQueries
from .tax.schema import TaxMutations, TaxQueries
from .translations.schema import TranslationQueries
from .warehouse.schema import (
    StockMutations,
    StockQueries,
    WarehouseMutations,
    WarehouseQueries,
)
from .webhook.schema import WebhookMutations, WebhookQueries
from .webhook.subscription_types import WEBHOOK_TYPES_MAP, Subscription

API_PATH = SimpleLazyObject(lambda: reverse("api"))


class Query(
    AccountQueries,
    AppQueries,
    AttributeQueries,
    ChannelQueries,
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
    TaxQueries,
    TranslationQueries,
    WarehouseQueries,
    WebhookQueries,
):
    pass


class Mutation(
    AccountMutations,
    AppMutations,
    AttributeMutations,
    ChannelMutations,
    CheckoutMutations,
    CoreMutations,
    CsvMutations,
    DiscountMutations,
    ExternalNotificationMutations,
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
    StockMutations,
    TaxMutations,
    WarehouseMutations,
    WebhookMutations,
):
    pass


def wrap_enum(resolver):
    def wrapped_resolver(*args, **kwargs):
        result = resolver(*args, **kwargs)
        if isinstance(result, enum.Enum):
            return result.value
        return result

    return wrapped_resolver


def patch_schema(schema: GraphQLSchema):
    """GraphQL Core 3.x returns enum values by default.

    Saleor is not ready for that.
    """
    for type in schema.type_map.values():
        if isinstance(type, GraphQLEnumType):
            type.parse_literal = wrap_enum(type.parse_literal)
            type.parse_value = wrap_enum(type.parse_value)


patch_federation_schema()
schema = build_schema(
    query=Query,
    mutation=Mutation,
    types=list(WEBHOOK_TYPES_MAP.values()),
    subscription=Subscription,
    directives=(DocDirective, WebhookEventsDirective),
    federation_version=LATEST_VERSION,
)
patch_schema(schema.graphql_schema)
