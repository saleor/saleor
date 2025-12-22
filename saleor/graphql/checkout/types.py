import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import graphene
from django.utils import timezone
from promise import Promise

from ...account.models import User
from ...checkout import calculations, models, problems
from ...checkout.calculations import fetch_checkout_data
from ...checkout.fetch import fetch_shipping_methods_for_checkout
from ...checkout.utils import get_valid_collection_points_for_checkout
from ...core.db.connection import allow_writer_in_context
from ...core.prices import quantize_price
from ...core.taxes import zero_money, zero_taxed_money
from ...graphql.core.context import (
    SyncWebhookControlContext,
    get_database_connection_name,
)
from ...payment.gateway import get_payment_gateways
from ...payment.interface import ListStoredPaymentMethodsRequestData
from ...permission.auth_filters import AuthorizationFilters
from ...permission.enums import (
    AccountPermissions,
    CheckoutPermissions,
    DiscountPermissions,
    PaymentPermissions,
)
from ...shipping.interface import ShippingMethodData
from ...shipping.utils import convert_checkout_delivery_to_shipping_method_data
from ...tax.utils import get_display_gross_prices
from ...warehouse import models as warehouse_models
from ...warehouse.reservations import is_reservation_enabled
from ...webhook.event_types import WebhookEventSyncType
from ..account.dataloaders import AddressByIdLoader, UserByUserIdLoader
from ..account.utils import check_is_owner_or_has_one_of_perms
from ..channel.dataloaders.by_checkout import ChannelByCheckoutIDLoader
from ..channel.dataloaders.by_self import ChannelByIdLoader
from ..channel.types import Channel
from ..checkout.dataloaders import (
    CheckoutLinesProblemsByCheckoutIdLoader,
    CheckoutProblemsByCheckoutIdDataloader,
)
from ..core import ResolveInfo
from ..core.connection import CountableConnection
from ..core.context import ChannelContext
from ..core.descriptions import (
    ADDED_IN_318,
    ADDED_IN_319,
    ADDED_IN_321,
    ADDED_IN_323,
    PREVIEW_FEATURE,
)
from ..core.doc_category import DOC_CATEGORY_CHECKOUT
from ..core.enums import LanguageCodeEnum
from ..core.fields import BaseField, PermissionsField
from ..core.scalars import UUID, DateTime, PositiveDecimal
from ..core.tracing import traced_resolver
from ..core.types import Money, NonNullList, TaxedMoney
from ..core.types.sync_webhook_control import (
    SyncWebhookControlContextModelObjectType,
    SyncWebhookControlContextObjectType,
)
from ..core.utils import CHECKOUT_CALCULATE_TAXES_MESSAGE, WebhookEventInfo, str_to_enum
from ..decorators import one_of_permissions_required
from ..discount.dataloaders import VoucherByCodeLoader
from ..giftcard.dataloaders import GiftCardsByCheckoutIdLoader
from ..giftcard.types import GiftCard
from ..meta import resolvers as MetaResolvers
from ..meta.types import ObjectWithMetadata, _filter_metadata
from ..payment.types import PaymentGateway, StoredPaymentMethod, TransactionItem
from ..plugins.dataloaders import (
    get_plugin_manager_promise,
    plugin_manager_promise_callback,
)
from ..product.dataloaders import (
    ProductTypeByProductIdLoader,
    ProductTypeByVariantIdLoader,
    ProductVariantByIdLoader,
)
from ..shipping.types import ShippingMethod
from ..site.dataloaders import load_site_callback
from ..tax.dataloaders import (
    TaxConfigurationByChannelId,
    TaxConfigurationPerCountryByTaxConfigurationIDLoader,
)
from ..utils import get_user_or_app_from_context
from ..warehouse.dataloaders import (
    StocksReservationsByCheckoutTokenLoader,
    WarehouseByIdLoader,
)
from ..warehouse.types import Warehouse
from ..webhook.dataloaders.pregenerated_payload_for_checkout_tax import (
    PregeneratedCheckoutTaxPayloadsByCheckoutTokenLoader,
)
from ..webhook.dataloaders.pregenerated_payloads_for_checkout_filter_shipping_methods import (
    PregeneratedCheckoutFilterShippingMethodPayloadsByCheckoutTokenLoader,
)
from .dataloaders import (
    CheckoutByTokenLoader,
    CheckoutInfoByCheckoutTokenLoader,
    CheckoutLinesInfoByCheckoutTokenLoader,
    CheckoutMetadataByCheckoutIdLoader,
    TransactionItemsByCheckoutIDLoader,
)
from .dataloaders.checkout_delivery import (
    CheckoutDeliveriesOnlyValidByCheckoutIdLoader,
    CheckoutDeliveryByIdLoader,
)
from .enums import CheckoutAuthorizeStatusEnum, CheckoutChargeStatusEnum
from .utils import prevent_sync_event_circular_query

if TYPE_CHECKING:
    from ...account.models import Address
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...plugins.manager import PluginsManager


def get_dataloaders_for_fetching_checkout_data(
    root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
) -> tuple[
    Promise["Address"] | None,
    Promise[list["CheckoutLineInfo"]],
    Promise["CheckoutInfo"],
    Promise["PluginsManager"],
    Promise[dict[str, Any]] | None,
    Promise[dict[str, Any]] | None,
]:
    checkout = root.node
    address_id = checkout.shipping_address_id or checkout.billing_address_id
    address = AddressByIdLoader(info.context).load(address_id) if address_id else None
    lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(checkout.token)
    checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(checkout.token)
    manager = get_plugin_manager_promise(info.context)
    tax_payloads = None
    excluded_shipping_methods_payloads = None
    if root.allow_sync_webhooks:
        tax_payloads = PregeneratedCheckoutTaxPayloadsByCheckoutTokenLoader(
            info.context
        ).load(checkout.token)
        excluded_shipping_methods_payloads = (
            PregeneratedCheckoutFilterShippingMethodPayloadsByCheckoutTokenLoader(
                info.context
            ).load(checkout.token)
        )
    return (
        address,
        lines,
        checkout_info,
        manager,
        tax_payloads,
        excluded_shipping_methods_payloads,
    )


def get_dataloaders_for_recalculate_discounts(
    root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
) -> tuple[
    Promise[list["CheckoutLineInfo"]],
    Promise["CheckoutInfo"],
]:
    checkout = root.node
    lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(checkout.token)
    checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(checkout.token)
    return lines, checkout_info


class CheckoutLineProblemInsufficientStock(
    SyncWebhookControlContextObjectType[problems.CheckoutLineProblemInsufficientStock],
):
    available_quantity = graphene.Int(description="Available quantity of a variant.")
    line = graphene.Field(
        "saleor.graphql.checkout.types.CheckoutLine",
        description="The line that has variant with insufficient stock.",
        required=True,
    )
    variant = graphene.Field(
        "saleor.graphql.product.types.ProductVariant",
        description="The variant with insufficient stock.",
        required=True,
    )

    class Meta:
        default_resolver = SyncWebhookControlContextObjectType.resolver_with_context
        description = (
            "Indicates insufficient stock for a given checkout line."
            "Placing the order will not be possible until solving this problem."
        )
        doc_category = DOC_CATEGORY_CHECKOUT

    @staticmethod
    def resolve_line(
        root: SyncWebhookControlContext[problems.CheckoutLineProblemInsufficientStock],
        _info: ResolveInfo,
    ):
        return SyncWebhookControlContext(
            node=root.node.line, allow_sync_webhooks=root.allow_sync_webhooks
        )


class CheckoutLineProblemVariantNotAvailable(
    SyncWebhookControlContextObjectType[problems.CheckoutLineProblemVariantNotAvailable]
):
    line = graphene.Field(
        "saleor.graphql.checkout.types.CheckoutLine",
        description="The line that has variant that is not available.",
        required=True,
    )

    class Meta:
        description = (
            "The variant assigned to the checkout line is not available."
            "Placing the order will not be possible until solving this problem."
        )
        doc_category = DOC_CATEGORY_CHECKOUT

    @staticmethod
    def resolve_line(
        root: SyncWebhookControlContext[
            problems.CheckoutLineProblemVariantNotAvailable
        ],
        _info: ResolveInfo,
    ):
        return SyncWebhookControlContext(
            node=root.node.line, allow_sync_webhooks=root.allow_sync_webhooks
        )


def _resolve_line_problem_type(
    instance: SyncWebhookControlContext[problems.CHECKOUT_PROBLEM_TYPE],
) -> (
    type[CheckoutLineProblemInsufficientStock]
    | type[CheckoutLineProblemVariantNotAvailable]
    | None
):
    problem_instance = instance.node

    if isinstance(problem_instance, problems.CheckoutLineProblemInsufficientStock):
        return CheckoutLineProblemInsufficientStock
    if isinstance(problem_instance, problems.CheckoutLineProblemVariantNotAvailable):
        return CheckoutLineProblemVariantNotAvailable
    return None


class CheckoutProblemDeliveryMethodStale(
    SyncWebhookControlContextObjectType[problems.CheckoutProblemDeliveryMethodStale]
):
    delivery = graphene.Field("saleor.graphql.checkout.types.Delivery", required=True)

    class Meta:
        default_resolver = SyncWebhookControlContextObjectType.resolver_with_context
        description = "Indicates that the delivery methods are stale." + ADDED_IN_323
        doc_category = DOC_CATEGORY_CHECKOUT


class CheckoutProblemDeliveryMethodInvalid(
    SyncWebhookControlContextObjectType[problems.CheckoutProblemDeliveryMethodInvalid]
):
    delivery = graphene.Field("saleor.graphql.checkout.types.Delivery", required=True)

    class Meta:
        default_resolver = SyncWebhookControlContextObjectType.resolver_with_context
        description = (
            "Indicates that the selected delivery method is invalid." + ADDED_IN_323
        )
        doc_category = DOC_CATEGORY_CHECKOUT


class CheckoutLineProblem(graphene.Union):
    class Meta:
        types = (
            CheckoutLineProblemInsufficientStock,
            CheckoutLineProblemVariantNotAvailable,
        )
        description = "Represents an problem in the checkout line."
        doc_category = DOC_CATEGORY_CHECKOUT

    @classmethod
    def resolve_type(
        cls,
        instance: SyncWebhookControlContext[problems.CHECKOUT_PROBLEM_TYPE],
        info: ResolveInfo,
    ):
        problem_type = _resolve_line_problem_type(instance)
        if problem_type:
            return problem_type
        return super().resolve_type(instance.node, info)


class CheckoutProblem(graphene.Union):
    class Meta:
        types = [
            CheckoutProblemDeliveryMethodStale,
            CheckoutProblemDeliveryMethodInvalid,
        ] + list(CheckoutLineProblem._meta.types)
        description = "Represents an problem in the checkout."
        doc_category = DOC_CATEGORY_CHECKOUT

    @classmethod
    def resolve_type(
        cls,
        instance: SyncWebhookControlContext[problems.CHECKOUT_PROBLEM_TYPE],
        info: ResolveInfo,
    ):
        line_problem_type = _resolve_line_problem_type(instance)
        if line_problem_type:
            return line_problem_type

        problem_instance = instance.node
        if isinstance(problem_instance, problems.CheckoutProblemDeliveryMethodStale):
            return CheckoutProblemDeliveryMethodStale
        if isinstance(problem_instance, problems.CheckoutProblemDeliveryMethodInvalid):
            return CheckoutProblemDeliveryMethodInvalid

        return super().resolve_type(instance.node, info)


class CheckoutLine(SyncWebhookControlContextModelObjectType[models.CheckoutLine]):
    id = graphene.GlobalID(required=True, description="The ID of the checkout line.")
    variant = graphene.Field(
        "saleor.graphql.product.types.ProductVariant",
        required=True,
        description="The product variant from which the checkout line was created.",
    )
    quantity = graphene.Int(
        required=True,
        description="The quantity of product variant assigned to the checkout line.",
    )
    unit_price = BaseField(
        TaxedMoney,
        description="The unit price of the checkout line, with taxes and discounts.",
        required=True,
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
                description=CHECKOUT_CALCULATE_TAXES_MESSAGE,
            ),
        ],
    )
    undiscounted_unit_price = graphene.Field(
        Money,
        description="The unit price of the checkout line, without discounts.",
        required=True,
    )
    prior_unit_price = graphene.Field(
        Money,
        description="The unit price of the checkout line prior to promotion."
        + ADDED_IN_321,
    )
    total_price = BaseField(
        TaxedMoney,
        description="The sum of the checkout line price, taxes and discounts.",
        required=True,
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
                description=CHECKOUT_CALCULATE_TAXES_MESSAGE,
            ),
        ],
    )
    undiscounted_total_price = graphene.Field(
        Money,
        description="The sum of the checkout line price, without discounts.",
        required=True,
    )
    prior_total_price = graphene.Field(
        Money,
        description="The sum of the checkout line price prior to promotion."
        + ADDED_IN_321,
    )
    requires_shipping = graphene.Boolean(
        description="Indicates whether the item need to be delivered.",
        required=True,
    )
    problems = NonNullList(
        CheckoutLineProblem, description="List of problems with the checkout line."
    )
    is_gift = graphene.Boolean(
        description="Determine if the line is a gift." + ADDED_IN_319 + PREVIEW_FEATURE,
    )

    class Meta:
        default_resolver = (
            SyncWebhookControlContextModelObjectType.resolver_with_context
        )
        description = "Represents an item in the checkout."
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.CheckoutLine

    @staticmethod
    def resolve_variant(
        root: SyncWebhookControlContext[models.CheckoutLine], info: ResolveInfo
    ):
        variant = ProductVariantByIdLoader(info.context).load(root.node.variant_id)
        channel = ChannelByCheckoutIDLoader(info.context).load(root.node.checkout_id)

        return Promise.all([variant, channel]).then(
            lambda data: ChannelContext(node=data[0], channel_slug=data[1].slug)
        )

    @staticmethod
    @prevent_sync_event_circular_query
    def resolve_unit_price(
        root: SyncWebhookControlContext[models.CheckoutLine], info: ResolveInfo
    ):
        def with_checkout(data):
            checkout, manager = data
            checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )
            lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )
            tax_payloads = None
            excluded_shipping_methods_payloads = None
            if root.allow_sync_webhooks:
                tax_payloads = PregeneratedCheckoutTaxPayloadsByCheckoutTokenLoader(
                    info.context
                ).load(checkout.token)
                excluded_shipping_methods_payloads = PregeneratedCheckoutFilterShippingMethodPayloadsByCheckoutTokenLoader(
                    info.context
                ).load(checkout.token)

            @allow_writer_in_context(info.context)
            def calculate_line_unit_price(data):
                checkout_info, lines, tax_payloads, excluded_payloads = data
                checkout_info.allow_sync_webhooks = root.allow_sync_webhooks
                checkout_info.pregenerated_payloads_for_excluded_shipping_method = (
                    excluded_shipping_methods_payloads
                )
                database_connection_name = get_database_connection_name(info.context)
                for line_info in lines:
                    if line_info.line.pk == root.node.pk:
                        return calculations.checkout_line_unit_price(
                            manager=manager,
                            checkout_info=checkout_info,
                            lines=lines,
                            checkout_line_info=line_info,
                            database_connection_name=database_connection_name,
                            pregenerated_subscription_payloads=tax_payloads,
                            allow_sync_webhooks=root.allow_sync_webhooks,
                        )
                return None

            return Promise.all(
                [checkout_info, lines, tax_payloads, excluded_shipping_methods_payloads]
            ).then(calculate_line_unit_price)

        return Promise.all(
            [
                CheckoutByTokenLoader(info.context).load(root.node.checkout_id),
                get_plugin_manager_promise(info.context),
            ]
        ).then(with_checkout)

    @staticmethod
    def resolve_undiscounted_unit_price(
        root: SyncWebhookControlContext[models.CheckoutLine], info: ResolveInfo
    ):
        def with_checkout(checkout):
            checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )

            lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )

            def calculate_undiscounted_unit_price(data):
                (
                    checkout_info,
                    lines,
                ) = data
                for line_info in lines:
                    if line_info.line.pk == root.node.pk:
                        return calculations.checkout_line_undiscounted_unit_price(
                            checkout_info=checkout_info,
                            checkout_line_info=line_info,
                        )

                return None

            return Promise.all(
                [
                    checkout_info,
                    lines,
                ]
            ).then(calculate_undiscounted_unit_price)

        return (
            CheckoutByTokenLoader(info.context)
            .load(root.node.checkout_id)
            .then(with_checkout)
        )

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_total_price(
        root: SyncWebhookControlContext[models.CheckoutLine], info: ResolveInfo
    ):
        def with_checkout(data):
            checkout, manager = data
            checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )

            lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )
            tax_payloads = None
            excluded_shipping_methods_payloads = None
            if root.allow_sync_webhooks:
                tax_payloads = PregeneratedCheckoutTaxPayloadsByCheckoutTokenLoader(
                    info.context
                ).load(checkout.token)
                excluded_shipping_methods_payloads = PregeneratedCheckoutFilterShippingMethodPayloadsByCheckoutTokenLoader(
                    info.context
                ).load(checkout.token)

            @allow_writer_in_context(info.context)
            def calculate_line_total_price(data):
                checkout_info, lines, tax_payloads, excluded_payloads = data
                checkout_info.pregenerated_payloads_for_excluded_shipping_method = (
                    excluded_payloads
                )
                checkout_info.allow_sync_webhooks = root.allow_sync_webhooks
                database_connection_name = get_database_connection_name(info.context)
                for line_info in lines:
                    if line_info.line.pk == root.node.pk:
                        return calculations.checkout_line_total(
                            manager=manager,
                            checkout_info=checkout_info,
                            lines=lines,
                            checkout_line_info=line_info,
                            database_connection_name=database_connection_name,
                            pregenerated_subscription_payloads=tax_payloads,
                            allow_sync_webhooks=root.allow_sync_webhooks,
                        )
                return None

            return Promise.all(
                [checkout_info, lines, tax_payloads, excluded_shipping_methods_payloads]
            ).then(calculate_line_total_price)

        return Promise.all(
            [
                CheckoutByTokenLoader(info.context).load(root.node.checkout_id),
                get_plugin_manager_promise(info.context),
            ]
        ).then(with_checkout)

    @staticmethod
    def resolve_undiscounted_total_price(
        root: SyncWebhookControlContext[models.CheckoutLine], info: ResolveInfo
    ):
        def with_checkout(checkout):
            checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )
            lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )

            def calculate_undiscounted_total_price(data):
                (
                    checkout_info,
                    lines,
                ) = data
                for line_info in lines:
                    if line_info.line.pk == root.node.pk:
                        return calculations.checkout_line_undiscounted_total_price(
                            checkout_info=checkout_info,
                            checkout_line_info=line_info,
                        )
                return None

            return Promise.all(
                [
                    checkout_info,
                    lines,
                ]
            ).then(calculate_undiscounted_total_price)

        return (
            CheckoutByTokenLoader(info.context)
            .load(root.node.checkout_id)
            .then(with_checkout)
        )

    @staticmethod
    def resolve_prior_total_price(
        root: SyncWebhookControlContext[models.CheckoutLine], info: ResolveInfo
    ) -> Money | None:
        checkout = root.node
        if checkout.prior_unit_price is None:
            return None

        quantized_amount = quantize_price(
            checkout.prior_unit_price.amount * checkout.quantity, checkout.currency
        )

        return Money(amount=quantized_amount, currency=checkout.currency)

    @staticmethod
    def resolve_requires_shipping(
        root: SyncWebhookControlContext[models.CheckoutLine], info: ResolveInfo
    ):
        def is_shipping_required(product_type):
            return product_type.is_shipping_required

        return (
            ProductTypeByVariantIdLoader(info.context)
            .load(root.node.variant_id)
            .then(is_shipping_required)
        )

    @staticmethod
    @traced_resolver
    def resolve_problems(
        root: SyncWebhookControlContext[models.CheckoutLine], info: ResolveInfo
    ):
        problems_dataloader = CheckoutLinesProblemsByCheckoutIdLoader(
            info.context
        ).load(root.node.checkout_id)

        def get_problem_for_line(problems):
            line_problems = problems.get(str(root.node.pk), [])
            return [
                SyncWebhookControlContext(
                    node=problem, allow_sync_webhooks=root.allow_sync_webhooks
                )
                for problem in line_problems
            ]

        return problems_dataloader.then(get_problem_for_line)


class CheckoutLineCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT
        node = CheckoutLine


class DeliveryMethod(graphene.Union):
    class Meta:
        description = (
            "Represents a delivery method chosen for the checkout. "
            '`Warehouse` type is used when checkout is marked as "click and collect" '
            "and `ShippingMethod` otherwise."
        )
        types = (Warehouse, ShippingMethod)

    @classmethod
    def resolve_type(cls, instance, info: ResolveInfo):
        if isinstance(instance, ShippingMethodData):
            return ShippingMethod
        if isinstance(instance, warehouse_models.Warehouse):
            return Warehouse

        return super().resolve_type(instance, info)


class Delivery(graphene.ObjectType):
    id = graphene.ID(required=True, description="The ID of the delivery.")
    shipping_method = graphene.Field(
        ShippingMethod,
        description="Shipping method represented by the delivery.",
    )

    class Meta:
        description = "Represents a delivery option for the checkout." + ADDED_IN_323
        doc_category = DOC_CATEGORY_CHECKOUT

    def resolve_id(root: models.CheckoutDelivery, info: ResolveInfo) -> str:
        return graphene.Node.to_global_id("CheckoutDelivery", root.pk)

    def resolve_shipping_method(
        root: models.CheckoutDelivery, _info: ResolveInfo
    ) -> ShippingMethodData | None:
        return convert_checkout_delivery_to_shipping_method_data(root)


def _should_load_denormalized_checkout_deliveries(
    checkout_context: SyncWebhookControlContext[models.Checkout],
):
    return not checkout_context.allow_sync_webhooks or (
        checkout_context.node.delivery_methods_stale_at
        and checkout_context.node.delivery_methods_stale_at > timezone.now()
    )


def _load_denormalized_checkout_deliveries(checkout_pk: uuid.UUID, info: ResolveInfo):
    return (
        CheckoutDeliveriesOnlyValidByCheckoutIdLoader(info.context)
        .load(checkout_pk)
        .then(
            lambda shipping_methods: [
                convert_checkout_delivery_to_shipping_method_data(sm)
                for sm in shipping_methods
            ]
        )
    )


def _resolve_checkout_deliveries(
    root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
):
    checkout = root.node

    def with_checkout_info(data):
        if _should_load_denormalized_checkout_deliveries(root):
            return _load_denormalized_checkout_deliveries(checkout.pk, info)

        checkout_info, excluded_payloads = data
        checkout_info.pregenerated_payloads_for_excluded_shipping_method = (
            excluded_payloads
        )
        checkout_info.allow_sync_webhooks = root.allow_sync_webhooks
        shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)
        checkout.delivery_methods_stale_at = (
            checkout_info.checkout.delivery_methods_stale_at
        )
        CheckoutDeliveriesOnlyValidByCheckoutIdLoader(info.context).prime(
            checkout.pk, shipping_methods
        )
        return [
            convert_checkout_delivery_to_shipping_method_data(sm)
            for sm in shipping_methods
        ]

    if _should_load_denormalized_checkout_deliveries(root):
        return _load_denormalized_checkout_deliveries(checkout.pk, info)

    excluded_shipping_methods_payloads_dataloader = (
        PregeneratedCheckoutFilterShippingMethodPayloadsByCheckoutTokenLoader(
            info.context
        ).load(root.node.token)
    )
    checkout_info_dataloader = CheckoutInfoByCheckoutTokenLoader(info.context).load(
        root.node.token
    )
    dataloaders_promise = Promise.all(
        [
            checkout_info_dataloader,
            excluded_shipping_methods_payloads_dataloader,
        ]
    )
    return dataloaders_promise.then(with_checkout_info)


def _resolve_checkout_delivery(
    root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
) -> Promise[ShippingMethodData | None] | None:
    checkout = root.node

    assigned_delivery_id = checkout.assigned_delivery_id
    if not assigned_delivery_id:
        return None

    if (
        checkout.delivery_methods_stale_at
        and checkout.delivery_methods_stale_at > timezone.now()
    ) or not root.allow_sync_webhooks:
        return (
            CheckoutDeliveryByIdLoader(info.context)
            .load(assigned_delivery_id)
            .then(
                lambda sm: (
                    convert_checkout_delivery_to_shipping_method_data(sm)
                    if sm.is_valid and sm.active
                    else None
                )
            )
        )

    def with_checkout_info(data):
        checkout_info, excluded_payloads = data
        checkout_info.pregenerated_payloads_for_excluded_shipping_method = (
            excluded_payloads
        )
        checkout_info.allow_sync_webhooks = root.allow_sync_webhooks
        shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)
        root.node.delivery_methods_stale_at = (
            checkout_info.checkout.delivery_methods_stale_at
        )
        CheckoutDeliveriesOnlyValidByCheckoutIdLoader(info.context).prime(
            checkout.pk, shipping_methods
        )
        CheckoutInfoByCheckoutTokenLoader(info.context).clear(root.node.token)

        for sm in shipping_methods:
            if sm.id == assigned_delivery_id:
                CheckoutDeliveryByIdLoader(info.context).prime(assigned_delivery_id, sm)
                return convert_checkout_delivery_to_shipping_method_data(sm)

        CheckoutDeliveryByIdLoader(info.context).clear(assigned_delivery_id)
        return None

    excluded_shipping_methods_payloads_dataloader = (
        PregeneratedCheckoutFilterShippingMethodPayloadsByCheckoutTokenLoader(
            info.context
        ).load(root.node.token)
    )
    checkout_info_dataloader = CheckoutInfoByCheckoutTokenLoader(info.context).load(
        root.node.token
    )
    dataloaders_promise = Promise.all(
        [
            checkout_info_dataloader,
            excluded_shipping_methods_payloads_dataloader,
        ]
    )
    return dataloaders_promise.then(with_checkout_info)


class Checkout(SyncWebhookControlContextModelObjectType[models.Checkout]):
    id = graphene.ID(required=True, description="The ID of the checkout.")
    created = DateTime(
        required=True, description="The date and time when the checkout was created."
    )
    updated_at = DateTime(
        required=True,
        description="Time of last modification of the given checkout.",
    )
    last_change = DateTime(
        required=True,
        deprecation_reason="Use `updatedAt` instead.",
    )
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description=(
            "The user assigned to the checkout. Requires one of the following "
            "permissions: "
            f"{AccountPermissions.MANAGE_USERS.name}, "
            f"{PaymentPermissions.HANDLE_PAYMENTS.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
    )
    channel = graphene.Field(
        Channel,
        required=True,
        description="The channel for which checkout was created.",
    )
    billing_address = graphene.Field(
        "saleor.graphql.account.types.Address",
        description="The billing address of the checkout.",
    )
    shipping_address = graphene.Field(
        "saleor.graphql.account.types.Address",
        description="The shipping address of the checkout.",
    )
    customer_note = graphene.String(
        required=True, description=f"The customer note for the checkout. {ADDED_IN_321}"
    )
    note = graphene.String(
        required=True,
        description="The note for the checkout.",
        deprecation_reason="Use `customerNote` instead.",
    )
    discount = graphene.Field(
        Money,
        description=(
            "The total discount applied to the checkout. "
            "Note: Only discount created via voucher are included in this field."
        ),
    )
    discount_name = graphene.String(
        description="The name of voucher assigned to the checkout."
    )
    translated_discount_name = graphene.String(
        description=(
            "Translation of the discountName field in the language "
            "set in Checkout.languageCode field."
            "Note: this field is set automatically when "
            "Checkout.languageCode is defined; otherwise it's null"
        )
    )
    voucher = PermissionsField(
        "saleor.graphql.discount.types.vouchers.Voucher",
        description="The voucher assigned to the checkout." + ADDED_IN_318,
        permissions=[DiscountPermissions.MANAGE_DISCOUNTS],
    )
    voucher_code = graphene.String(
        description="The code of voucher assigned to the checkout."
    )
    available_shipping_methods = BaseField(
        NonNullList(ShippingMethod),
        required=True,
        description="Shipping methods that can be used with this checkout.",
        deprecation_reason="Use `shippingMethods` instead.",
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                description=(
                    "Optionally triggered when cached external shipping methods are "
                    "invalid."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
                description=(
                    "Optionally triggered when cached filtered shipping methods are "
                    "invalid."
                ),
            ),
        ],
    )
    shipping_methods = BaseField(
        NonNullList(ShippingMethod),
        required=True,
        description="Shipping methods that can be used with this checkout.",
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                description=(
                    "Optionally triggered when cached external shipping methods are "
                    "invalid."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
                description=(
                    "Optionally triggered when cached filtered shipping methods are "
                    "invalid."
                ),
            ),
        ],
    )
    available_collection_points = NonNullList(
        Warehouse,
        required=True,
        description="Collection points that can be used for this order.",
    )
    available_payment_gateways = BaseField(
        NonNullList(PaymentGateway),
        description="List of available payment gateways.",
        required=True,
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.PAYMENT_LIST_GATEWAYS,
                description="Fetch payment gateways available for checkout.",
            ),
        ],
    )
    email = graphene.String(description="Email of a customer.", required=False)
    gift_cards = NonNullList(
        GiftCard,
        description="List of gift cards associated with this checkout.",
        required=True,
    )
    is_shipping_required = graphene.Boolean(
        description="Returns True, if checkout requires shipping.", required=True
    )
    quantity = graphene.Int(description="The number of items purchased.", required=True)
    stock_reservation_expires = DateTime(
        description=(
            "Date when oldest stock reservation for this checkout "
            "expires or null if no stock is reserved."
        ),
    )
    lines = NonNullList(
        CheckoutLine,
        description=(
            "A list of checkout lines, each containing information about "
            "an item in the checkout."
        ),
        required=True,
    )
    shipping_price = BaseField(
        TaxedMoney,
        description=(
            "The price of the shipping, with all the taxes included. Set to 0 when no "
            "delivery method is selected."
        ),
        required=True,
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
                description=CHECKOUT_CALCULATE_TAXES_MESSAGE,
            ),
        ],
    )
    delivery = BaseField(
        Delivery,
        description="The delivery method selected for this checkout." + ADDED_IN_323,
    )

    shipping_method = BaseField(
        ShippingMethod,
        description="The shipping method related with checkout.",
        deprecation_reason="Use `delivery` instead.",
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                description=(
                    "Optionally triggered when cached external shipping methods are "
                    "invalid."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
                description=(
                    "Optionally triggered when cached filtered shipping methods are "
                    "invalid."
                ),
            ),
        ],
    )
    delivery_method = BaseField(
        DeliveryMethod,
        description="The delivery method selected for this checkout.",
        deprecation_reason="Use `delivery` instead.",
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                description=(
                    "Optionally triggered when cached external shipping methods are "
                    "invalid."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
                description=(
                    "Optionally triggered when cached filtered shipping methods are "
                    "invalid."
                ),
            ),
        ],
    )
    subtotal_price = BaseField(
        TaxedMoney,
        description="The price of the checkout before shipping, with taxes included.",
        required=True,
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
                description=CHECKOUT_CALCULATE_TAXES_MESSAGE,
            ),
        ],
    )
    tax_exemption = graphene.Boolean(
        description="Returns True if checkout has to be exempt from taxes.",
        required=True,
    )
    token = graphene.Field(UUID, description="The checkout's token.", required=True)
    total_price = BaseField(
        TaxedMoney,
        description=(
            "The sum of the checkout line prices, with all the taxes,"
            "shipping costs, and discounts included."
        ),
        required=True,
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
                description=CHECKOUT_CALCULATE_TAXES_MESSAGE,
            ),
        ],
    )

    total_balance = BaseField(
        Money,
        description="The difference between the paid and the checkout total amount.",
        required=True,
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
                description=CHECKOUT_CALCULATE_TAXES_MESSAGE,
            ),
        ],
    )

    language_code = graphene.Field(
        LanguageCodeEnum, description="Checkout language code.", required=True
    )
    transactions = NonNullList(
        TransactionItem,
        description=(
            "List of transactions for the checkout. Requires one of the "
            "following permissions: MANAGE_CHECKOUTS, HANDLE_PAYMENTS."
        ),
    )
    display_gross_prices = graphene.Boolean(
        description="Determines whether displayed prices should include taxes.",
        required=True,
    )
    authorize_status = BaseField(
        CheckoutAuthorizeStatusEnum,
        description="The authorize status of the checkout.",
        required=True,
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
                description=CHECKOUT_CALCULATE_TAXES_MESSAGE,
            ),
        ],
    )
    charge_status = BaseField(
        CheckoutChargeStatusEnum,
        description="The charge status of the checkout.",
        required=True,
        webhook_events_info=[
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
                description=CHECKOUT_CALCULATE_TAXES_MESSAGE,
            ),
        ],
    )
    stored_payment_methods = NonNullList(
        StoredPaymentMethod,
        description=(
            "List of user's stored payment methods that can be used in this checkout "
            "session. It uses the channel that the checkout was created in. "
            "When `amount` is not provided, `checkout.total` will be used as a default "
            "value."
        ),
        amount=PositiveDecimal(
            description="Amount that will be used to fetch stored payment methods."
        ),
    )

    problems = NonNullList(
        CheckoutProblem,
        description="List of problems with the checkout.",
    )

    class Meta:
        default_resolver = (
            SyncWebhookControlContextModelObjectType.resolver_with_context
        )
        description = "Checkout object."
        model = models.Checkout
        interfaces = [graphene.relay.Node, ObjectWithMetadata]

    @staticmethod
    def resolve_customer_note(
        root: SyncWebhookControlContext[models.Checkout], _info: ResolveInfo
    ):
        return root.node.note

    @staticmethod
    def resolve_created(
        root: SyncWebhookControlContext[models.Checkout], _info: ResolveInfo
    ):
        return root.node.created_at

    @staticmethod
    def resolve_channel(root: SyncWebhookControlContext[models.Checkout], info):
        return ChannelByIdLoader(info.context).load(root.node.channel_id)

    @staticmethod
    def resolve_id(
        root: SyncWebhookControlContext[models.Checkout], _info: ResolveInfo
    ):
        return graphene.Node.to_global_id("Checkout", root.node.pk)

    @staticmethod
    def resolve_shipping_address(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        if not root.node.shipping_address_id:
            return None
        return AddressByIdLoader(info.context).load(root.node.shipping_address_id)

    @staticmethod
    def resolve_billing_address(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        if not root.node.billing_address_id:
            return None
        return AddressByIdLoader(info.context).load(root.node.billing_address_id)

    @staticmethod
    def resolve_user(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        if not root.node.user_id:
            return None
        user = root.node.user
        requestor = get_user_or_app_from_context(info.context)
        check_is_owner_or_has_one_of_perms(
            requestor,
            user,
            AccountPermissions.MANAGE_USERS,
            PaymentPermissions.HANDLE_PAYMENTS,
            CheckoutPermissions.HANDLE_TAXES,
        )
        return user

    @staticmethod
    def resolve_email(
        root: SyncWebhookControlContext[models.Checkout], _info: ResolveInfo
    ):
        return root.node.get_customer_email()

    @staticmethod
    def resolve_shipping_method(root: SyncWebhookControlContext[models.Checkout], info):
        return _resolve_checkout_delivery(root, info)

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_shipping_methods(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        return _resolve_checkout_deliveries(root, info)

    @staticmethod
    def resolve_delivery_method(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        checkout = root.node
        if checkout.collection_point_id:
            return WarehouseByIdLoader(info.context).load(checkout.collection_point_id)

        return _resolve_checkout_delivery(root, info)

    @staticmethod
    def resolve_delivery(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        if not root.node.assigned_delivery_id:
            return None

        return CheckoutDeliveryByIdLoader(info.context).load(
            root.node.assigned_delivery_id
        )

    @staticmethod
    def resolve_quantity(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        checkout_info = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
            root.node.token
        )

        def calculate_quantity(lines):
            return sum([line_info.line.quantity for line_info in lines])

        return checkout_info.then(calculate_quantity)

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_total_price(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        @allow_writer_in_context(info.context)
        def calculate_total_price(data):
            address, lines, checkout_info, manager, tax_payloads, excluded_payloads = (
                data
            )
            database_connection_name = get_database_connection_name(info.context)
            checkout_info.allow_sync_webhooks = root.allow_sync_webhooks
            checkout_info.pregenerated_payloads_for_excluded_shipping_method = (
                excluded_payloads
            )

            taxed_total = calculations.calculate_checkout_total_with_gift_cards(
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                address=address,
                database_connection_name=database_connection_name,
                pregenerated_subscription_payloads=tax_payloads,
                allow_sync_webhooks=root.allow_sync_webhooks,
            )
            return max(taxed_total, zero_taxed_money(root.node.currency))

        dataloaders = list(get_dataloaders_for_fetching_checkout_data(root, info))
        return Promise.all(dataloaders).then(calculate_total_price)

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_subtotal_price(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        @allow_writer_in_context(info.context)
        def calculate_subtotal_price(data):
            address, lines, checkout_info, manager, tax_payloads, excluded_payloads = (
                data
            )
            database_connection_name = get_database_connection_name(info.context)
            checkout_info.allow_sync_webhooks = root.allow_sync_webhooks
            checkout_info.pregenerated_payloads_for_excluded_shipping_method = (
                excluded_payloads
            )

            return calculations.checkout_subtotal(
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                address=address,
                database_connection_name=database_connection_name,
                pregenerated_subscription_payloads=tax_payloads,
                allow_sync_webhooks=root.allow_sync_webhooks,
            )

        dataloaders = list(get_dataloaders_for_fetching_checkout_data(root, info))
        return Promise.all(dataloaders).then(calculate_subtotal_price)

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_shipping_price(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        @allow_writer_in_context(info.context)
        def calculate_shipping_price(data):
            address, lines, checkout_info, manager, tax_payloads, excluded_payloads = (
                data
            )
            database_connection_name = get_database_connection_name(info.context)
            checkout_info.allow_sync_webhooks = root.allow_sync_webhooks

            return calculations.checkout_shipping_price(
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                address=address,
                database_connection_name=database_connection_name,
                pregenerated_subscription_payloads=tax_payloads,
                allow_sync_webhooks=root.allow_sync_webhooks,
            )

        dataloaders = list(get_dataloaders_for_fetching_checkout_data(root, info))
        return Promise.all(dataloaders).then(calculate_shipping_price)

    @staticmethod
    def resolve_lines(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        @allow_writer_in_context(info.context)
        def get_lines(data):
            lines_info, checkout_info = data
            database_connection_name = get_database_connection_name(info.context)
            # we need to recalculate discount as the gift line might be added / changed
            calculations.recalculate_discounts(
                checkout_info, lines_info, database_connection_name
            )
            return (
                SyncWebhookControlContext(
                    line_info.line, allow_sync_webhooks=root.allow_sync_webhooks
                )
                for line_info in lines_info
            )

        dataloaders = list(get_dataloaders_for_recalculate_discounts(root, info))
        return Promise.all(dataloaders).then(get_lines)

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_available_shipping_methods(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        return _resolve_checkout_deliveries(root, info).then(
            lambda methods: [method for method in methods if method.active]
        )

    @staticmethod
    @traced_resolver
    def resolve_available_collection_points(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        @allow_writer_in_context(info.context)
        def get_available_collection_points(lines):
            database_connection_name = get_database_connection_name(info.context)
            result = get_valid_collection_points_for_checkout(
                lines,
                root.node.channel_id,
                database_connection_name=database_connection_name,
            )
            return list(result)

        return (
            CheckoutLinesInfoByCheckoutTokenLoader(info.context)
            .load(root.node.token)
            .then(get_available_collection_points)
        )

    @staticmethod
    @prevent_sync_event_circular_query
    @plugin_manager_promise_callback
    def resolve_available_payment_gateways(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo, manager
    ):
        token = root.node.token
        checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(token)
        checkout_lines_info = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
            token
        )

        @allow_writer_in_context(info.context)
        def get_available_payment_gateways(results):
            checkout_info, lines_info = results
            return get_payment_gateways(
                manager=manager,
                currency=root.node.currency,
                checkout_info=checkout_info,
                checkout_lines=lines_info,
                channel_slug=checkout_info.channel.slug,
            )

        return Promise.all([checkout_info, checkout_lines_info]).then(
            get_available_payment_gateways
        )

    @staticmethod
    def resolve_gift_cards(root: SyncWebhookControlContext[models.Checkout], info):
        return GiftCardsByCheckoutIdLoader(info.context).load(root.node.pk)

    @staticmethod
    def resolve_is_shipping_required(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        def is_shipping_required(lines):
            product_ids = [line_info.product.id for line_info in lines]

            def with_product_types(product_types):
                return any(pt.is_shipping_required for pt in product_types)

            return (
                ProductTypeByProductIdLoader(info.context)
                .load_many(product_ids)
                .then(with_product_types)
            )

        return (
            CheckoutLinesInfoByCheckoutTokenLoader(info.context)
            .load(root.node.token)
            .then(is_shipping_required)
        )

    @staticmethod
    def resolve_language_code(root: SyncWebhookControlContext[models.Checkout], _info):
        return LanguageCodeEnum[str_to_enum(root.node.language_code)]

    @staticmethod
    @traced_resolver
    @load_site_callback
    def resolve_stock_reservation_expires(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo, site
    ):
        with allow_writer_in_context(info.context):
            if not is_reservation_enabled(site.settings):
                return None

            def get_oldest_stock_reservation_expiration_date(reservations):
                if not reservations:
                    return None

                return min(reservation.reserved_until for reservation in reservations)

            return (
                StocksReservationsByCheckoutTokenLoader(info.context)
                .load(root.node.token)
                .then(get_oldest_stock_reservation_expiration_date)
            )

    @staticmethod
    @one_of_permissions_required(
        [CheckoutPermissions.MANAGE_CHECKOUTS, PaymentPermissions.HANDLE_PAYMENTS]
    )
    def resolve_transactions(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        return TransactionItemsByCheckoutIDLoader(info.context).load(root.node.pk)

    @staticmethod
    def resolve_display_gross_prices(
        root: SyncWebhookControlContext[models.Checkout], info: ResolveInfo
    ):
        tax_config = TaxConfigurationByChannelId(info.context).load(
            root.node.channel_id
        )
        country_code = root.node.get_country()

        def load_tax_country_exceptions(tax_config):
            tax_configs_per_country = (
                TaxConfigurationPerCountryByTaxConfigurationIDLoader(info.context).load(
                    tax_config.id
                )
            )

            def calculate_display_gross_prices(tax_configs_per_country):
                tax_config_country = next(
                    (
                        tc
                        for tc in tax_configs_per_country
                        if tc.country.code == country_code
                    ),
                    None,
                )
                return get_display_gross_prices(tax_config, tax_config_country)

            return tax_configs_per_country.then(calculate_display_gross_prices)

        return tax_config.then(load_tax_country_exceptions)

    @staticmethod
    def resolve_metadata(root: SyncWebhookControlContext[models.Checkout], info):
        return (
            CheckoutMetadataByCheckoutIdLoader(info.context)
            .load(root.node.pk)
            .then(
                lambda metadata_storage: (
                    MetaResolvers.resolve_metadata(metadata_storage.metadata)
                    if metadata_storage
                    else {}
                )
            )
        )

    @staticmethod
    def resolve_metafield(
        root: SyncWebhookControlContext[models.Checkout], info, *, key: str
    ):
        return (
            CheckoutMetadataByCheckoutIdLoader(info.context)
            .load(root.node.pk)
            .then(
                lambda metadata_storage: (
                    metadata_storage.metadata.get(key) if metadata_storage else None
                )
            )
        )

    @staticmethod
    def resolve_metafields(
        root: SyncWebhookControlContext[models.Checkout], info, *, keys=None
    ):
        return (
            CheckoutMetadataByCheckoutIdLoader(info.context)
            .load(root.node.pk)
            .then(
                lambda metadata_storage: (
                    _filter_metadata(metadata_storage.metadata, keys)
                    if metadata_storage
                    else {}
                )
            )
        )

    @staticmethod
    def resolve_private_metadata(
        root: SyncWebhookControlContext[models.Checkout], info
    ):
        return (
            CheckoutMetadataByCheckoutIdLoader(info.context)
            .load(root.node.pk)
            .then(
                lambda metadata_storage: (
                    MetaResolvers.resolve_private_metadata(metadata_storage, info)
                    if metadata_storage
                    else {}
                )
            )
        )

    @staticmethod
    def resolve_private_metafield(
        root: SyncWebhookControlContext[models.Checkout], info, *, key: str
    ):
        def resolve_private_metafield_with_privilege_check(metadata_storage):
            MetaResolvers.check_private_metadata_privilege(metadata_storage, info)
            return metadata_storage.private_metadata.get(key)

        return (
            CheckoutMetadataByCheckoutIdLoader(info.context)
            .load(root.node.pk)
            .then(
                lambda metadata_storage: (
                    resolve_private_metafield_with_privilege_check(metadata_storage)
                    if metadata_storage
                    else None
                )
            )
        )

    @staticmethod
    def resolve_private_metafields(
        root: SyncWebhookControlContext[models.Checkout], info, *, keys=None
    ):
        def resolve_private_metafields_with_privilege(metadata_storage):
            MetaResolvers.check_private_metadata_privilege(metadata_storage, info)
            return _filter_metadata(metadata_storage.private_metadata, keys)

        return (
            CheckoutMetadataByCheckoutIdLoader(info.context)
            .load(root.node.pk)
            .then(
                lambda metadata_storage: (
                    resolve_private_metafields_with_privilege(metadata_storage)
                    if metadata_storage
                    else {}
                )
            )
        )

    @classmethod
    def resolve_updated_at(
        cls, root: SyncWebhookControlContext[models.Checkout], _info
    ):
        return root.node.last_change

    @staticmethod
    def resolve_authorize_status(
        root: SyncWebhookControlContext[models.Checkout], info
    ):
        @allow_writer_in_context(info.context)
        def _resolve_authorize_status(data):
            (
                address,
                lines,
                checkout_info,
                manager,
                tax_payloads,
                excluded_payloads,
                transactions,
            ) = data
            checkout_info.pregenerated_payloads_for_excluded_shipping_method = (
                excluded_payloads
            )
            database_connection_name = get_database_connection_name(info.context)
            fetch_checkout_data(
                checkout_info=checkout_info,
                manager=manager,
                lines=lines,
                checkout_transactions=transactions,
                force_status_update=True,
                database_connection_name=database_connection_name,
                pregenerated_subscription_payloads=tax_payloads,
                allow_sync_webhooks=root.allow_sync_webhooks,
            )
            return checkout_info.checkout.authorize_status

        dataloaders = list(get_dataloaders_for_fetching_checkout_data(root, info))
        dataloaders.append(
            TransactionItemsByCheckoutIDLoader(info.context).load(root.node.pk)
        )
        return Promise.all(dataloaders).then(_resolve_authorize_status)

    @staticmethod
    def resolve_charge_status(root: SyncWebhookControlContext[models.Checkout], info):
        @allow_writer_in_context(info.context)
        def _resolve_charge_status(data):
            (
                address,
                lines,
                checkout_info,
                manager,
                tax_payloads,
                excluded_payloads,
                transactions,
            ) = data
            database_connection_name = get_database_connection_name(info.context)
            checkout_info.allow_sync_webhooks = root.allow_sync_webhooks
            checkout_info.pregenerated_payloads_for_excluded_shipping_method = (
                excluded_payloads
            )

            fetch_checkout_data(
                checkout_info=checkout_info,
                manager=manager,
                lines=lines,
                checkout_transactions=transactions,
                force_status_update=True,
                database_connection_name=database_connection_name,
                pregenerated_subscription_payloads=tax_payloads,
                allow_sync_webhooks=root.allow_sync_webhooks,
            )
            return checkout_info.checkout.charge_status

        dataloaders = list(get_dataloaders_for_fetching_checkout_data(root, info))
        dataloaders.append(
            TransactionItemsByCheckoutIDLoader(info.context).load(root.node.pk)
        )
        return Promise.all(dataloaders).then(_resolve_charge_status)

    @staticmethod
    def resolve_total_balance(root: SyncWebhookControlContext[models.Checkout], info):
        database_connection_name = get_database_connection_name(info.context)

        def _calculate_total_balance_for_transactions(data):
            (
                address,
                lines,
                checkout_info,
                manager,
                tax_payloads,
                excluded_payloads,
                transactions,
            ) = data
            checkout_info.allow_sync_webhooks = root.allow_sync_webhooks
            checkout_info.pregenerated_payloads_for_excluded_shipping_method = (
                excluded_payloads
            )

            taxed_total = calculations.calculate_checkout_total_with_gift_cards(
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                address=address,
                database_connection_name=database_connection_name,
                pregenerated_subscription_payloads=tax_payloads,
                allow_sync_webhooks=root.allow_sync_webhooks,
            )
            currency = root.node.currency
            checkout_total = max(taxed_total, zero_taxed_money(currency))
            total_charged = zero_money(currency)
            for transaction in transactions:
                total_charged += transaction.amount_charged
                total_charged += transaction.amount_charge_pending
            return total_charged - checkout_total.gross

        dataloaders = list(get_dataloaders_for_fetching_checkout_data(root, info))
        dataloaders.append(
            TransactionItemsByCheckoutIDLoader(info.context).load(root.node.pk)
        )
        return Promise.all(dataloaders).then(_calculate_total_balance_for_transactions)

    @staticmethod
    @traced_resolver
    def resolve_problems(root: SyncWebhookControlContext[models.Checkout], info):
        checkout_problems_dataloader = CheckoutProblemsByCheckoutIdDataloader(
            info.context
        )

        def _wrapped_with_sync_webhook_control_context(problems):
            return [
                SyncWebhookControlContext(
                    node=problem, allow_sync_webhooks=root.allow_sync_webhooks
                )
                for problem in problems
            ]

        return checkout_problems_dataloader.load(root.node.pk).then(
            _wrapped_with_sync_webhook_control_context
        )

    @staticmethod
    def resolve_stored_payment_methods(
        root: SyncWebhookControlContext[models.Checkout],
        info: ResolveInfo,
        amount: Decimal | None = None,
    ):
        user_id = root.node.user_id
        if user_id is None:
            return []
        requestor = get_user_or_app_from_context(info.context)
        if not requestor or requestor.id != user_id:
            return []

        if not root.allow_sync_webhooks:
            return []

        def _resolve_stored_payment_methods(
            data: tuple["Channel", "User", "PluginsManager"],
        ):
            channel, user, manager = data
            request_data = ListStoredPaymentMethodsRequestData(
                user=user,
                channel=channel,
            )
            return manager.list_stored_payment_methods(request_data)

        manager = get_plugin_manager_promise(info.context)
        channel_loader = ChannelByIdLoader(info.context).load(root.node.channel_id)
        user_loader = UserByUserIdLoader(info.context).load(root.node.user_id)
        return Promise.all([channel_loader, user_loader, manager]).then(
            _resolve_stored_payment_methods
        )

    @staticmethod
    def resolve_voucher(root: SyncWebhookControlContext[models.Checkout], info):
        voucher_code = root.node.voucher_code
        if not voucher_code:
            return None

        def wrap_voucher_with_channel_context(data):
            voucher, channel = data
            return ChannelContext(node=voucher, channel_slug=channel.slug)

        voucher = VoucherByCodeLoader(info.context).load(voucher_code)
        channel = ChannelByIdLoader(info.context).load(root.node.channel_id)

        return Promise.all([voucher, channel]).then(wrap_voucher_with_channel_context)


class CheckoutCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT
        node = Checkout
