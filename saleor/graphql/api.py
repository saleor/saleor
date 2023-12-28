from functools import partial

import graphql
from django.urls import reverse
from django.utils.functional import SimpleLazyObject
from graphql import (
    GraphQLCachedBackend,
    GraphQLCoreBackend,
    GraphQLScalarType,
    GraphQLSchema,
    execute,
    parse,
    validate,
)
from graphql.backend.base import GraphQLDocument
from graphql.execution import ExecutionResult

from ..core.utils.cache import CacheDict
from ..graphql.notifications.schema import ExternalNotificationMutations
from .account.schema import AccountMutations, AccountQueries
from .app.schema import AppMutations, AppQueries
from .attribute.schema import AttributeMutations, AttributeQueries
from .channel.schema import ChannelMutations, ChannelQueries
from .checkout.schema import CheckoutMutations, CheckoutQueries
from .core.enums import unit_enums
from .core.federation.schema import build_federated_schema
from .core.schema import CoreMutations, CoreQueries
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


GraphQLDocDirective = graphql.GraphQLDirective(
    name="doc",
    description="Groups fields and operations into named groups.",
    args={
        "category": graphql.GraphQLArgument(
            type_=graphql.GraphQLNonNull(graphql.GraphQLString),
            description="Name of the grouping category",
        )
    },
    locations=[
        graphql.DirectiveLocation.ENUM,
        graphql.DirectiveLocation.FIELD,
        graphql.DirectiveLocation.FIELD_DEFINITION,
        graphql.DirectiveLocation.INPUT_OBJECT,
        graphql.DirectiveLocation.OBJECT,
    ],
)


def serialize_webhook_event(value):
    return value


GraphQLWebhookEventAsyncType = GraphQLScalarType(
    name="WebhookEventTypeAsyncEnum",
    description="",
    serialize=serialize_webhook_event,
)

GraphQLWebhookEventSyncType = GraphQLScalarType(
    name="WebhookEventTypeSyncEnum",
    description="",
    serialize=serialize_webhook_event,
)

GraphQLWebhookEventsInfoDirective = graphql.GraphQLDirective(
    name="webhookEventsInfo",
    description="Webhook events triggered by a specific location.",
    args={
        "asyncEvents": graphql.GraphQLArgument(
            type_=graphql.GraphQLNonNull(
                graphql.GraphQLList(
                    graphql.GraphQLNonNull(GraphQLWebhookEventAsyncType)
                )
            ),
            description=(
                "List of asynchronous webhook events triggered by a specific location."
            ),
        ),
        "syncEvents": graphql.GraphQLArgument(
            type_=graphql.GraphQLNonNull(
                graphql.GraphQLList(graphql.GraphQLNonNull(GraphQLWebhookEventSyncType))
            ),
            description=(
                "List of synchronous webhook events triggered by a specific location."
            ),
        ),
    },
    locations=[
        graphql.DirectiveLocation.FIELD,
        graphql.DirectiveLocation.FIELD_DEFINITION,
        graphql.DirectiveLocation.INPUT_OBJECT,
        graphql.DirectiveLocation.OBJECT,
    ],
)
schema = build_federated_schema(
    Query,
    mutation=Mutation,
    types=unit_enums + list(WEBHOOK_TYPES_MAP.values()),
    subscription=Subscription,
    directives=graphql.specified_directives
    + [GraphQLDocDirective, GraphQLWebhookEventsInfoDirective],
)


def _fail(errors, **_kwargs) -> ExecutionResult:
    return ExecutionResult(errors=errors, invalid=True)


class SaleorGraphQLBackend(GraphQLCoreBackend):
    def document_from_string(
        self,
        schema: GraphQLSchema,
        document_string: str,  # type: ignore[override]
    ) -> GraphQLDocument:
        # validate eagerly so we can cache the result
        document_ast = parse(document_string)
        validation_errors = validate(schema, document_ast)
        if validation_errors:
            return GraphQLDocument(
                schema=schema,
                document_string=document_string,
                document_ast=document_ast,
                execute=partial(_fail, validation_errors),
            )

        return GraphQLDocument(
            schema=schema,
            document_string=document_string,
            document_ast=document_ast,
            execute=partial(execute, schema, document_ast, **self.execute_params),
        )


backend = GraphQLCachedBackend(SaleorGraphQLBackend(), cache_map=CacheDict(1000))
