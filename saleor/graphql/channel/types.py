import collections
import itertools
from typing import TYPE_CHECKING, TypeVar, cast

import graphene
from django.db.models import Model
from django_countries.fields import Country
from graphene.types.objecttype import ObjectType
from graphene.types.resolver import get_default_resolver
from promise import Promise

from ...channel import models
from ...core.models import ModelWithMetadata
from ...permission.auth_filters import AuthorizationFilters
from ...permission.enums import (
    ChannelPermissions,
    CheckoutPermissions,
    OrderPermissions,
    PaymentPermissions,
)
from ..account.enums import CountryCodeEnum
from ..core import ResolveInfo
from ..core.descriptions import (
    ADDED_IN_318,
    ADDED_IN_320,
    DEPRECATED_IN_3X_FIELD,
    PREVIEW_FEATURE,
)
from ..core.doc_category import (
    DOC_CATEGORY_CHECKOUT,
    DOC_CATEGORY_ORDERS,
    DOC_CATEGORY_PAYMENTS,
    DOC_CATEGORY_PRODUCTS,
    DOC_CATEGORY_TAXES,
)
from ..core.fields import PermissionsField
from ..core.scalars import Day, Minute
from ..core.types import BaseObjectType, CountryDisplay, ModelObjectType, NonNullList
from ..meta.types import ObjectWithMetadata
from ..tax.dataloaders import TaxConfigurationByChannelId
from ..translations.resolvers import resolve_translation
from ..warehouse.dataloaders import WarehousesByChannelIdLoader
from ..warehouse.types import Warehouse
from . import ChannelContext
from .dataloaders import ChannelWithHasOrdersByIdLoader
from .enums import (
    AllocationStrategyEnum,
    MarkAsPaidStrategyEnum,
    TransactionFlowStrategyEnum,
)

if TYPE_CHECKING:
    from ...shipping.models import ShippingZone

T = TypeVar("T", bound=Model)


class ChannelContextTypeForObjectType(ModelObjectType[T]):
    """A Graphene type that supports resolvers' root as ChannelContext objects."""

    class Meta:
        abstract = True

    @staticmethod
    def resolver_with_context(
        attname, default_value, root: ChannelContext, info: ResolveInfo, **args
    ):
        resolver = get_default_resolver()
        return resolver(attname, default_value, root.node, info, **args)

    @staticmethod
    def resolve_id(root: ChannelContext[T], _info: ResolveInfo):
        return root.node.pk

    @staticmethod
    def resolve_translation(
        root: ChannelContext[T], info: ResolveInfo, *, language_code
    ):
        # Resolver for TranslationField; needs to be manually specified.
        return resolve_translation(root.node, info, language_code=language_code)


class ChannelContextType(ChannelContextTypeForObjectType[T]):
    """A Graphene type that supports resolvers' root as ChannelContext objects."""

    class Meta:
        abstract = True

    @classmethod
    def is_type_of(cls, root: ChannelContext[T] | T, _info: ResolveInfo) -> bool:
        # Unwrap node from ChannelContext if it didn't happen already
        if isinstance(root, ChannelContext):
            root = root.node

        if isinstance(root, cls):
            return True

        if cls._meta.model._meta.proxy:
            model = root._meta.model
        else:
            model = cast(type[Model], root._meta.model._meta.concrete_model)

        return model == cls._meta.model


TM = TypeVar("TM", bound=ModelWithMetadata)


class ChannelContextTypeWithMetadataForObjectType(ChannelContextTypeForObjectType[TM]):
    """A Graphene type for that uses ChannelContext as root in resolvers.

    Same as ChannelContextType, but for types that implement ObjectWithMetadata
    interface.
    """

    class Meta:
        abstract = True

    @staticmethod
    def resolve_metadata(root: ChannelContext[TM], info: ResolveInfo):
        # Used in metadata API to resolve metadata fields from an instance.
        return ObjectWithMetadata.resolve_metadata(root.node, info)

    @staticmethod
    def resolve_metafield(root: ChannelContext[TM], info: ResolveInfo, *, key: str):
        # Used in metadata API to resolve metadata fields from an instance.
        return ObjectWithMetadata.resolve_metafield(root.node, info, key=key)

    @staticmethod
    def resolve_metafields(root: ChannelContext[TM], info: ResolveInfo, *, keys=None):
        # Used in metadata API to resolve metadata fields from an instance.
        return ObjectWithMetadata.resolve_metafields(root.node, info, keys=keys)

    @staticmethod
    def resolve_private_metadata(root: ChannelContext[TM], info: ResolveInfo):
        # Used in metadata API to resolve private metadata fields from an instance.
        return ObjectWithMetadata.resolve_private_metadata(root.node, info)

    @staticmethod
    def resolve_private_metafield(
        root: ChannelContext[TM], info: ResolveInfo, *, key: str
    ):
        # Used in metadata API to resolve private metadata fields from an instance.
        return ObjectWithMetadata.resolve_private_metafield(root.node, info, key=key)

    @staticmethod
    def resolve_private_metafields(
        root: ChannelContext[TM], info: ResolveInfo, *, keys=None
    ):
        # Used in metadata API to resolve private metadata fields from an instance.
        return ObjectWithMetadata.resolve_private_metafields(root.node, info, keys=keys)


class ChannelContextTypeWithMetadata(ChannelContextTypeWithMetadataForObjectType[TM]):
    """A Graphene type for that uses ChannelContext as root in resolvers.

    Same as ChannelContextType, but for types that implement ObjectWithMetadata
    interface.
    """

    class Meta:
        abstract = True


class StockSettings(BaseObjectType):
    allocation_strategy = AllocationStrategyEnum(
        description=(
            "Allocation strategy defines the preference of warehouses "
            "for allocations and reservations."
        ),
        required=True,
    )

    class Meta:
        description = "Represents the channel stock settings."
        doc_category = DOC_CATEGORY_PRODUCTS


class CheckoutSettings(ObjectType):
    use_legacy_error_flow = graphene.Boolean(
        required=True,
        description=(
            "Default `true`. Determines if the checkout mutations should use legacy "
            "error flow. In legacy flow, all mutations can raise an exception "
            "unrelated to the requested action - (e.g. out-of-stock exception when "
            "updating checkoutShippingAddress.) "
            "If `false`, the errors will be aggregated in `checkout.problems` field. "
            "Some of the `problems` can block the finalizing checkout process. "
            "The legacy flow will be removed in Saleor 4.0. "
            "The flow with `checkout.problems` will be the default one."
            + DEPRECATED_IN_3X_FIELD
        ),
    )
    automatically_complete_fully_paid_checkouts = graphene.Boolean(
        required=True,
        description=(
            "Default `false`. Determines if the paid checkouts should be automatically "
            "completed. This setting applies only to checkouts where payment "
            "was processed through transactions."
            "When enabled, the checkout will be automatically completed once the "
            "checkout `charge_status` reaches `FULL`. This occurs when the total sum "
            "of charged and authorized transaction amounts equals or exceeds the "
            "checkout's total amount."
        )
        + ADDED_IN_320,
    )

    class Meta:
        description = "Represents the channel-specific checkout settings."
        doc_category = DOC_CATEGORY_CHECKOUT


class OrderSettings(ObjectType):
    automatically_confirm_all_new_orders = graphene.Boolean(
        required=True,
        description=(
            "When disabled, all new orders from checkout "
            "will be marked as unconfirmed. When enabled orders from checkout will "
            "become unfulfilled immediately."
        ),
    )
    automatically_fulfill_non_shippable_gift_card = graphene.Boolean(
        required=True,
        description=(
            "When enabled, all non-shippable gift card orders "
            "will be fulfilled automatically."
        ),
    )
    expire_orders_after = Minute(
        required=False,
        description=(
            "Expiration time in minutes. Default null - means do not expire any orders."
        ),
    )

    mark_as_paid_strategy = MarkAsPaidStrategyEnum(
        required=True,
        description=(
            "Determine what strategy will be used to mark the order as paid. "
            "Based on the chosen option, the proper object will be created "
            "and attached to the order when it's manually marked as paid."
            "\n`PAYMENT_FLOW` - [default option] creates the `Payment` object."
            "\n`TRANSACTION_FLOW` - creates the `TransactionItem` object."
        ),
    )
    delete_expired_orders_after = Day(
        required=True,
        description=("The time in days after expired orders will be deleted."),
    )
    allow_unpaid_orders = graphene.Boolean(
        required=True,
        description=(
            "Determine if it is possible to place unpaid order by calling "
            "`checkoutComplete` mutation."
        ),
    )
    include_draft_order_in_voucher_usage = graphene.Boolean(
        required=True,
        description=(
            "Determine if voucher applied on draft order should be count toward "
            "voucher usage." + ADDED_IN_318 + PREVIEW_FEATURE
        ),
    )

    class Meta:
        description = "Represents the channel-specific order settings."
        doc_category = DOC_CATEGORY_ORDERS


class PaymentSettings(ObjectType):
    default_transaction_flow_strategy = TransactionFlowStrategyEnum(
        required=True,
        description=(
            "Determine the transaction flow strategy to be used. "
            "Include the selected option in the payload sent to the payment app, as a "
            "requested action for the transaction."
        ),
    )

    class Meta:
        description = "Represents the channel-specific payment settings."
        doc_category = DOC_CATEGORY_PAYMENTS


class Channel(ModelObjectType):
    id = graphene.GlobalID(required=True, description="The ID of the channel.")
    slug = graphene.String(
        required=True,
        description="Slug of the channel.",
    )

    name = PermissionsField(
        graphene.String,
        description="Name of the channel.",
        required=True,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
        ],
    )
    is_active = PermissionsField(
        graphene.Boolean,
        description="Whether the channel is active.",
        required=True,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
        ],
    )
    currency_code = PermissionsField(
        graphene.String,
        description="A currency that is assigned to the channel.",
        required=True,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
        ],
    )
    has_orders = PermissionsField(
        graphene.Boolean,
        description="Whether a channel has associated orders.",
        permissions=[
            ChannelPermissions.MANAGE_CHANNELS,
        ],
        required=True,
    )
    default_country = PermissionsField(
        CountryDisplay,
        description=(
            "Default country for the channel. Default country can be "
            "used in checkout to determine the stock quantities or calculate taxes "
            "when the country was not explicitly provided."
        ),
        required=True,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
        ],
    )
    warehouses = PermissionsField(
        NonNullList(Warehouse),
        description="List of warehouses assigned to this channel.",
        required=True,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
        ],
    )
    countries = NonNullList(
        CountryDisplay,
        description="List of shippable countries for the channel.",
    )

    available_shipping_methods_per_country = graphene.Field(
        NonNullList("saleor.graphql.shipping.types.ShippingMethodsPerCountry"),
        countries=graphene.Argument(NonNullList(CountryCodeEnum)),
        description="Shipping methods that are available for the channel.",
    )
    stock_settings = PermissionsField(
        StockSettings,
        description=("Define the stock setting for this channel."),
        required=True,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
        ],
    )
    order_settings = PermissionsField(
        OrderSettings,
        description="Channel-specific order settings.",
        required=True,
        permissions=[
            ChannelPermissions.MANAGE_CHANNELS,
            OrderPermissions.MANAGE_ORDERS,
        ],
    )

    checkout_settings = PermissionsField(
        CheckoutSettings,
        description="Channel-specific checkout settings.",
        required=True,
        permissions=[
            ChannelPermissions.MANAGE_CHANNELS,
            CheckoutPermissions.MANAGE_CHECKOUTS,
        ],
    )
    payment_settings = PermissionsField(
        PaymentSettings,
        description="Channel-specific payment settings.",
        required=True,
        permissions=[
            ChannelPermissions.MANAGE_CHANNELS,
            PaymentPermissions.HANDLE_PAYMENTS,
        ],
    )

    tax_configuration = PermissionsField(
        "saleor.graphql.tax.types.TaxConfiguration",
        description="Channel specific tax configuration." + ADDED_IN_320,
        required=True,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
        doc_category=DOC_CATEGORY_TAXES,
    )

    class Meta:
        description = "Represents channel."
        model = models.Channel
        interfaces = [graphene.relay.Node, ObjectWithMetadata]

    @staticmethod
    def resolve_tax_configuration(root: models.Channel, info: ResolveInfo):
        return TaxConfigurationByChannelId(info.context).load(root.id)

    @staticmethod
    def resolve_has_orders(root: models.Channel, info: ResolveInfo):
        return (
            ChannelWithHasOrdersByIdLoader(info.context)
            .load(root.id)
            .then(lambda channel: channel.has_orders)
        )

    @staticmethod
    def resolve_default_country(root: models.Channel, _info: ResolveInfo):
        return CountryDisplay(
            code=root.default_country.code, country=root.default_country.name
        )

    @staticmethod
    def resolve_warehouses(root: models.Channel, info: ResolveInfo):
        return WarehousesByChannelIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_countries(root: models.Channel, info: ResolveInfo):
        from ..shipping.dataloaders import ShippingZonesByChannelIdLoader

        def get_countries(shipping_zones):
            countries = []
            for s_zone in shipping_zones:
                countries.extend(s_zone.countries)
            sorted_countries = list(set(countries))
            sorted_countries.sort(key=lambda country: country.name)
            return [
                CountryDisplay(code=country.code, country=country.name)
                for country in sorted_countries
            ]

        return (
            ShippingZonesByChannelIdLoader(info.context)
            .load(root.id)
            .then(get_countries)
        )

    @staticmethod
    def resolve_available_shipping_methods_per_country(
        root: models.Channel, info, **data
    ):
        from ...shipping.utils import convert_to_shipping_method_data
        from ..shipping.dataloaders import (
            ShippingMethodChannelListingByChannelSlugLoader,
            ShippingMethodsByShippingZoneIdLoader,
            ShippingZonesByChannelIdLoader,
        )

        shipping_zones_loader = ShippingZonesByChannelIdLoader(info.context).load(
            root.id
        )
        shipping_zone_countries: dict[int, list[Country]] = collections.defaultdict(
            list
        )
        requested_countries = data.get("countries", [])

        def _group_shipping_methods_by_country(data):
            shipping_methods, shipping_channel_listings = data
            shipping_listing_map = {
                listing.shipping_method_id: listing
                for listing in shipping_channel_listings
            }

            shipping_methods_per_country = collections.defaultdict(list)
            for shipping_method in shipping_methods:
                countries = shipping_zone_countries.get(
                    shipping_method.shipping_zone_id, []
                )
                for country in countries:
                    listing = shipping_listing_map.get(shipping_method.id)
                    if not listing:
                        continue
                    shipping_method_dataclass = convert_to_shipping_method_data(
                        shipping_method, listing
                    )
                    shipping_methods_per_country[country.code].append(
                        shipping_method_dataclass
                    )

            if requested_countries:
                results = [
                    {
                        "country_code": code,
                        "shipping_methods": shipping_methods_per_country.get(code, []),
                    }
                    for code in requested_countries
                    if code in shipping_methods_per_country
                ]
            else:
                results = [
                    {
                        "country_code": code,
                        "shipping_methods": shipping_methods_per_country[code],
                    }
                    for code in shipping_methods_per_country.keys()
                ]
            results.sort(key=lambda item: item["country_code"])

            return results

        def filter_shipping_methods(shipping_methods):
            shipping_methods = list(itertools.chain.from_iterable(shipping_methods))
            shipping_listings = ShippingMethodChannelListingByChannelSlugLoader(
                info.context
            ).load(root.slug)
            return Promise.all([shipping_methods, shipping_listings]).then(
                _group_shipping_methods_by_country
            )

        def get_shipping_methods(shipping_zones: list["ShippingZone"]):
            shipping_zones_keys = [shipping_zone.id for shipping_zone in shipping_zones]
            for shipping_zone in shipping_zones:
                shipping_zone_countries[shipping_zone.id] = shipping_zone.countries

            return (
                ShippingMethodsByShippingZoneIdLoader(info.context)
                .load_many(shipping_zones_keys)
                .then(filter_shipping_methods)
            )

        return shipping_zones_loader.then(get_shipping_methods)

    @staticmethod
    def resolve_stock_settings(root: models.Channel, _info: ResolveInfo):
        return StockSettings(allocation_strategy=root.allocation_strategy)

    @staticmethod
    def resolve_order_settings(root: models.Channel, _info):
        return OrderSettings(
            automatically_confirm_all_new_orders=(
                root.automatically_confirm_all_new_orders
            ),
            automatically_fulfill_non_shippable_gift_card=(
                root.automatically_fulfill_non_shippable_gift_card
            ),
            expire_orders_after=root.expire_orders_after,
            mark_as_paid_strategy=root.order_mark_as_paid_strategy,
            delete_expired_orders_after=root.delete_expired_orders_after.days,
            include_draft_order_in_voucher_usage=(
                root.include_draft_order_in_voucher_usage
            ),
            allow_unpaid_orders=(root.allow_unpaid_orders),
        )

    @staticmethod
    def resolve_checkout_settings(root: models.Channel, _info):
        complete_paid_checkouts = root.automatically_complete_fully_paid_checkouts
        return CheckoutSettings(
            use_legacy_error_flow=root.use_legacy_error_flow_for_checkout,
            automatically_complete_fully_paid_checkouts=complete_paid_checkouts,
        )

    @staticmethod
    def resolve_payment_settings(root: models.Channel, _info):
        return PaymentSettings(
            default_transaction_flow_strategy=root.default_transaction_flow_strategy,
        )
