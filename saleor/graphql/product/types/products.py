import sys
from collections import defaultdict
from dataclasses import asdict
from decimal import Decimal

import graphene
from graphene import relay
from promise import Promise

from ....attribute import models as attribute_models
from ....channel.models import Channel
from ....core.db.connection import allow_writer_in_context
from ....core.utils import build_absolute_uri
from ....core.utils.country import get_active_country
from ....core.weight import convert_weight_to_default_weight_unit
from ....permission.auth_filters import AuthorizationFilters
from ....permission.enums import OrderPermissions, ProductPermissions
from ....permission.utils import has_one_of_permissions
from ....product import models
from ....product.models import ALL_PRODUCTS_PERMISSIONS
from ....product.utils import calculate_revenue_for_variant
from ....product.utils.availability import (
    get_product_availability,
    get_variant_availability,
)
from ....product.utils.variants import get_variant_selection_attributes
from ....tax.utils import (
    get_display_gross_prices,
    get_tax_calculation_strategy,
    get_tax_rate_for_country,
)
from ....thumbnail.utils import (
    get_image_or_proxy_url,
    get_thumbnail_format,
    get_thumbnail_size,
)
from ....warehouse.reservations import is_reservation_enabled
from ...account import types as account_types
from ...account.enums import CountryCodeEnum
from ...attribute.filters import (
    AttributeFilterInput,
    AttributeWhereInput,
    filter_attribute_search,
)
from ...attribute.resolvers import resolve_attributes
from ...attribute.types import (
    AssignedAttribute,
    AssignedVariantAttribute,
    Attribute,
    AttributeCountableConnection,
    ObjectWithAttributes,
    SelectedAttribute,
)
from ...channel.dataloaders.by_self import ChannelBySlugLoader
from ...channel.utils import get_default_channel_slug_or_graphql_error
from ...core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ...core.const import DEFAULT_NESTED_LIST_LIMIT
from ...core.context import (
    ChannelContext,
    ChannelQsContext,
    get_database_connection_name,
)
from ...core.descriptions import (
    ADDED_IN_321,
    ADDED_IN_322,
    DEPRECATED_IN_3X_INPUT,
    RICH_CONTENT,
)
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.enums import ReportingPeriod
from ...core.federation import federated_entity, resolve_federation_references
from ...core.fields import (
    ConnectionField,
    FilterConnectionField,
    JSONString,
    PermissionsField,
)
from ...core.scalars import Date, DateTime, PositiveInt
from ...core.tracing import traced_resolver
from ...core.types import (
    BaseObjectType,
    Image,
    ModelObjectType,
    NonNullList,
    TaxedMoney,
    TaxedMoneyRange,
    TaxType,
    ThumbnailField,
    Weight,
)
from ...core.types.context import ChannelContextType
from ...core.utils import from_global_id_or_error
from ...core.validators import (
    validate_one_of_args_is_in_query,
)
from ...meta.types import ObjectWithMetadata
from ...order.dataloaders import (
    OrderByIdLoader,
    OrderLinesByVariantIdAndChannelIdLoader,
)
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product.dataloaders.products import (
    AvailableProductVariantsByProductIdAndChannel,
    ProductVariantsByProductIdAndChannel,
)
from ...site.dataloaders import load_site_callback
from ...tax.dataloaders import (
    ProductChargeTaxesByTaxClassIdLoader,
    TaxClassByIdLoader,
    TaxClassCountryRateByTaxClassIDLoader,
    TaxClassDefaultRateByCountryLoader,
    TaxClassIdByProductIdLoader,
    TaxConfigurationByChannelId,
    TaxConfigurationPerCountryByTaxConfigurationIDLoader,
)
from ...tax.types import TaxClass
from ...translations.fields import TranslationField
from ...translations.types import ProductTranslation, ProductVariantTranslation
from ...utils import get_user_or_app_from_context
from ...utils.filters import reporting_period_to_date
from ...warehouse.dataloaders import (
    AvailableQuantityByProductVariantIdCountryCodeAndChannelSlugLoader,
    PreorderQuantityReservedByVariantChannelListingIdLoader,
    StocksByProductVariantIdLoader,
    StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader,
)
from ...warehouse.types import Stock
from ..dataloaders import (
    CategoryByIdLoader,
    CollectionChannelListingByCollectionIdAndChannelSlugLoader,
    CollectionsByProductIdLoader,
    ImagesByProductIdLoader,
    ImagesByProductVariantIdLoader,
    MediaByProductIdLoader,
    MediaByProductVariantIdLoader,
    ProductAttributesAllByProductTypeIdLoader,
    ProductAttributesVisibleInStorefrontByProductTypeIdLoader,
    ProductByIdLoader,
    ProductChannelListingByProductIdAndChannelSlugLoader,
    ProductChannelListingByProductIdLoader,
    ProductTypeByIdLoader,
    ProductVariantByIdLoader,
    ProductVariantsByProductIdLoader,
    ThumbnailByProductMediaIdSizeAndFormatLoader,
    VariantAttributesAllByProductTypeIdLoader,
    VariantAttributesVisibleInStorefrontByProductTypeIdLoader,
    VariantChannelListingByVariantIdAndChannelSlugLoader,
    VariantChannelListingByVariantIdLoader,
    VariantsChannelListingByProductIdAndChannelSlugLoader,
)
from ..enums import ProductMediaType, ProductTypeKindEnum, VariantAttributeScope
from ..filters.product_variant import (
    ProductVariantFilterInput,
    ProductVariantWhereInput,
)
from ..resolvers import (
    resolve_product_attribute,
    resolve_product_attributes,
    resolve_product_variants,
    resolve_products,
    resolve_variant_attribute,
    resolve_variant_attributes,
)
from ..sorters import MediaSortingInput, ProductVariantSortingInput
from .channels import ProductChannelListing, ProductVariantChannelListing
from .digital_contents import DigitalContent

destination_address_argument = graphene.Argument(
    account_types.AddressInput,
    description=(
        "Destination address used to find warehouses where stock availability "
        "for this product is checked. If address is empty, uses "
        "`Shop.companyAddress` or fallbacks to server's "
        "`settings.DEFAULT_COUNTRY` configuration."
    ),
)


class BasePricingInfo(BaseObjectType):
    on_sale = graphene.Boolean(description="Whether it is in sale or not.")
    discount = graphene.Field(
        TaxedMoney, description="The discount amount if in sale (null otherwise)."
    )
    discount_prior = graphene.Field(
        TaxedMoney,
        description=(
            "The discount amount compared to prior price. Null if product "
            "is not on sale or prior price was not provided in VariantChannelListing"
            + ADDED_IN_321
        ),
    )

    # deprecated
    discount_local_currency = graphene.Field(
        TaxedMoney,
        description="The discount amount in the local currency.",
        deprecation_reason="Always returns `null`.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        description = "Represents base type for pricing information of a product."


class VariantPricingInfo(BasePricingInfo):
    price = graphene.Field(
        TaxedMoney, description="The price, with any discount subtracted."
    )
    price_undiscounted = graphene.Field(
        TaxedMoney, description="The price without any discount."
    )
    price_prior = graphene.Field(
        TaxedMoney, description="The price prior to discount." + ADDED_IN_321
    )

    # deprecated
    discount_local_currency = graphene.Field(
        TaxedMoney,
        description="The discount amount in the local currency.",
        deprecation_reason="Always returns `null`.",
    )
    price_local_currency = graphene.Field(
        TaxedMoney,
        description="The discounted price in the local currency.",
        deprecation_reason="Always returns `null`.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        description = "Represents availability of a variant in the storefront."


class ProductPricingInfo(BasePricingInfo):
    display_gross_prices = graphene.Boolean(
        description="Determines whether displayed prices should include taxes.",
        required=True,
    )
    price_range = graphene.Field(
        TaxedMoneyRange,
        description="The discounted price range of the product variants.",
    )
    price_range_undiscounted = graphene.Field(
        TaxedMoneyRange,
        description="The undiscounted price range of the product variants.",
    )
    price_range_prior = graphene.Field(
        TaxedMoneyRange,
        description="The prior price range of the product variants." + ADDED_IN_321,
    )

    # deprecated
    price_range_local_currency = graphene.Field(
        TaxedMoneyRange,
        description=(
            "The discounted price range of the product variants in the local currency."
        ),
        deprecation_reason="Always returns `null`.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        description = "Represents availability of a product in the storefront."


class PreorderData(BaseObjectType):
    global_threshold = PermissionsField(
        graphene.Int,
        required=False,
        description="The global preorder threshold for product variant.",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    global_sold_units = PermissionsField(
        graphene.Int,
        required=True,
        description="Total number of sold product variant during preorder.",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    end_date = DateTime(required=False, description="Preorder end date.")

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        description = "Represents preorder settings for product variant."

    @staticmethod
    def resolve_global_threshold(root, _info):
        return root.global_threshold

    @staticmethod
    def resolve_global_sold_units(root, _info):
        return root.global_sold_units


@federated_entity("id channel")
class ProductVariant(ChannelContextType[models.ProductVariant]):
    id = graphene.GlobalID(required=True, description="The ID of the product variant.")
    name = graphene.String(
        required=True, description="The name of the product variant."
    )
    sku = graphene.String(
        description="The SKU (stock keeping unit) of the product variant."
    )
    product = graphene.Field(
        lambda: Product,
        required=True,
        description="The product to which the variant belongs.",
    )
    track_inventory = graphene.Boolean(
        required=True,
        description=(
            "Determines if the inventory of this variant should be tracked. If false, "
            "the quantity won't change when customers buy this item. "
            "If the field is not provided, `Shop.trackInventoryByDefault` will be used."
        ),
    )
    quantity_limit_per_customer = graphene.Int(
        description="The maximum quantity of this variant that a customer can purchase."
    )
    weight = graphene.Field(Weight, description="The weight of the product variant.")
    channel = graphene.String(
        description=(
            "Channel given to retrieve this product variant. Also used by federation "
            "gateway to resolve this object in a federated query."
        ),
    )
    channel_listings = PermissionsField(
        NonNullList(ProductVariantChannelListing),
        description="List of price information in channels for the product.",
        permissions=[
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
        ],
    )
    pricing = graphene.Field(
        VariantPricingInfo,
        address=destination_address_argument,
        description=(
            "Lists the storefront variant's pricing, the current price and discounts, "
            "only meant for displaying."
        ),
    )
    assigned_attribute = graphene.Field(
        AssignedAttribute,
        slug=graphene.Argument(
            graphene.String,
            description="Slug of the attribute",
            required=True,
        ),
        description="Get a single attribute attached to product by attribute slug."
        + ADDED_IN_322,
    )

    assigned_attributes = NonNullList(
        AssignedAttribute,
        required=True,
        description="List of attributes assigned to this variant." + ADDED_IN_322,
        limit=PositiveInt(
            description=(
                "Maximum number of attributes to return. "
                f"Default is {DEFAULT_NESTED_LIST_LIMIT}."
            ),
            default_value=DEFAULT_NESTED_LIST_LIMIT,
        ),
    )
    attributes = NonNullList(
        SelectedAttribute,
        required=True,
        description="List of attributes assigned to this variant.",
        variant_selection=graphene.Argument(
            VariantAttributeScope,
            description="Define scope of returned attributes.",
        ),
        deprecation_reason="Use the `assignedAttributes` field instead.",
    )
    margin = graphene.Int(description="Gross margin percentage value.")
    quantity_ordered = PermissionsField(
        graphene.Int,
        description="Total quantity ordered.",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    revenue = PermissionsField(
        TaxedMoney,
        period=graphene.Argument(ReportingPeriod),
        description=(
            "Total revenue generated by a variant in given period of time. Note: this "
            "field should be queried using `reportProductSales` query as it uses "
            "optimizations suitable for such calculations."
        ),
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    images = NonNullList(
        lambda: ProductImage,
        description="List of images for the product variant.",
        deprecation_reason="Use the `media` field instead.",
    )
    media = NonNullList(
        lambda: ProductMedia,
        description="List of media for the product variant.",
    )
    translation = TranslationField(
        ProductVariantTranslation,
        type_name="product variant",
        resolver=ChannelContextType.resolve_translation,
    )
    digital_content = PermissionsField(
        DigitalContent,
        description="Digital content for the product variant.",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    stocks = PermissionsField(
        NonNullList(Stock),
        description="Stocks for the product variant.",
        address=destination_address_argument,
        country_code=graphene.Argument(
            CountryCodeEnum,
            description=(
                "Two-letter ISO 3166-1 country code. "
                f"{DEPRECATED_IN_3X_INPUT} Use `address` argument instead."
            ),
        ),
        permissions=[
            ProductPermissions.MANAGE_PRODUCTS,
            OrderPermissions.MANAGE_ORDERS,
        ],
    )
    quantity_available = graphene.Int(
        required=False,
        description=(
            "Quantity of a product available for sale in one checkout. "
            "Field value will be `null` when "
            "no `limitQuantityPerCheckout` in global settings has been set, and "
            "`productVariant` stocks are not tracked."
        ),
        address=destination_address_argument,
        country_code=graphene.Argument(
            CountryCodeEnum,
            description=(
                "Two-letter ISO 3166-1 country code. When provided, the exact quantity "
                "from a warehouse operating in shipping zones that contain this "
                "country will be returned. Otherwise, it will return the maximum "
                "quantity from all shipping zones. "
                f"{DEPRECATED_IN_3X_INPUT} Use `address` argument instead."
            ),
        ),
    )
    preorder = graphene.Field(
        PreorderData,
        required=False,
        description="Preorder data for product variant.",
    )
    created = DateTime(
        required=True,
        description="The date and time when the product variant was created.",
    )
    updated_at = DateTime(
        required=True,
        description="The date and time when the product variant was last updated.",
    )
    external_reference = graphene.String(
        description="External ID of this product.",
        required=False,
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Represents a version of a product such as different size or color."
        )
        interfaces = [relay.Node, ObjectWithMetadata, ObjectWithAttributes]
        model = models.ProductVariant

    @staticmethod
    def resolve_created(root: ChannelContext[models.ProductVariant], _info):
        return root.node.created_at

    @staticmethod
    def resolve_channel(root: ChannelContext[models.Product], _info):
        return root.channel_slug

    @staticmethod
    def resolve_stocks(
        root: ChannelContext[models.ProductVariant],
        info,
        address=None,
        country_code=None,
    ):
        if address is not None:
            country_code = address.country
        channle_slug = root.channel_slug
        if channle_slug or country_code:
            return StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader(  # noqa: E501
                info.context
            ).load((root.node.id, country_code, root.channel_slug))
        return StocksByProductVariantIdLoader(info.context).load(root.node.id)

    @staticmethod
    @load_site_callback
    def resolve_quantity_available(
        root: ChannelContext[models.ProductVariant],
        info,
        site,
        address=None,
        country_code=None,
    ):
        if address is not None:
            country_code = address.country
        channel_slug = str(root.channel_slug) if root.channel_slug else None

        with allow_writer_in_context(info.context):
            global_quantity_limit_per_checkout = (
                site.settings.limit_quantity_per_checkout
            )

        if root.node.is_preorder_active():
            variant = root.node
            channel_listing = VariantChannelListingByVariantIdAndChannelSlugLoader(
                info.context
            ).load((variant.id, channel_slug))

            def calculate_available_per_channel(channel_listing):
                if (
                    channel_listing
                    and channel_listing.preorder_quantity_threshold is not None
                ):
                    if is_reservation_enabled(site.settings):
                        quantity_reserved = (
                            PreorderQuantityReservedByVariantChannelListingIdLoader(
                                info.context
                            ).load(channel_listing.id)
                        )

                        def calculate_available_channel_quantity_with_reservations(
                            reserved_quantity,
                        ):
                            return max(
                                min(
                                    channel_listing.preorder_quantity_threshold
                                    - channel_listing.preorder_quantity_allocated
                                    - reserved_quantity,
                                    global_quantity_limit_per_checkout or sys.maxsize,
                                ),
                                0,
                            )

                        return quantity_reserved.then(
                            calculate_available_channel_quantity_with_reservations
                        )

                    return min(
                        channel_listing.preorder_quantity_threshold
                        - channel_listing.preorder_quantity_allocated,
                        global_quantity_limit_per_checkout or sys.maxsize,
                    )
                if variant.preorder_global_threshold is not None:
                    variant_channel_listings = VariantChannelListingByVariantIdLoader(
                        info.context
                    ).load(variant.id)

                    def calculate_available_global(variant_channel_listings):
                        if not variant_channel_listings:
                            return global_quantity_limit_per_checkout
                        global_sold_units = sum(
                            channel_listing.preorder_quantity_allocated
                            for channel_listing in variant_channel_listings
                        )

                        available_quantity = variant.preorder_global_threshold
                        available_quantity -= global_sold_units

                        if is_reservation_enabled(site.settings):
                            quantity_reserved = (
                                PreorderQuantityReservedByVariantChannelListingIdLoader(
                                    info.context
                                ).load_many(
                                    [listing.id for listing in variant_channel_listings]
                                )
                            )

                            def calculate_available_global_quantity_with_reservations(
                                reserved_quantities,
                            ):
                                return max(
                                    min(
                                        variant.preorder_global_threshold
                                        - global_sold_units
                                        - sum(reserved_quantities),
                                        global_quantity_limit_per_checkout
                                        or sys.maxsize,
                                    ),
                                    0,
                                )

                            return quantity_reserved.then(
                                calculate_available_global_quantity_with_reservations
                            )

                        return min(
                            variant.preorder_global_threshold - global_sold_units,
                            global_quantity_limit_per_checkout or sys.maxsize,
                        )

                    return variant_channel_listings.then(calculate_available_global)

                return global_quantity_limit_per_checkout

            return channel_listing.then(calculate_available_per_channel)

        if not root.node.track_inventory:
            return global_quantity_limit_per_checkout

        return AvailableQuantityByProductVariantIdCountryCodeAndChannelSlugLoader(
            info.context
        ).load((root.node.id, country_code, channel_slug))

    @staticmethod
    def resolve_digital_content(root: ChannelContext[models.ProductVariant], _info):
        return getattr(root.node, "digital_content", None)

    @classmethod
    def resolve_assigned_attribute(
        cls, root: ChannelContext[models.ProductVariant], info, slug
    ):
        return resolve_variant_attribute(root, info, slug)

    @classmethod
    def resolve_attributes(
        cls,
        root: ChannelContext[models.ProductVariant],
        info,
        variant_selection: VariantAttributeScope | None = None,
    ):
        if variant_selection == VariantAttributeScope.VARIANT_SELECTION:
            selection_bool = True
        elif variant_selection == VariantAttributeScope.NOT_VARIANT_SELECTION:
            selection_bool = False
        else:
            selection_bool = None
        return resolve_variant_attributes(
            root, info, variant_selection=selection_bool, limit=None
        )

    @classmethod
    def resolve_assigned_attributes(
        cls,
        root: ChannelContext[models.ProductVariant],
        info,
        limit: int = DEFAULT_NESTED_LIST_LIMIT,
    ):
        return resolve_variant_attributes(
            root, info, variant_selection=None, limit=limit
        )

    @staticmethod
    def resolve_channel_listings(root: ChannelContext[models.ProductVariant], info):
        return VariantChannelListingByVariantIdLoader(info.context).load(root.node.id)

    @staticmethod
    def resolve_pricing(
        root: ChannelContext[models.ProductVariant], info, *, address=None
    ):
        if not root.channel_slug:
            return None

        channel_slug = str(root.channel_slug)
        context = info.context

        product_channel_listing = ProductChannelListingByProductIdAndChannelSlugLoader(
            context
        ).load((root.node.product_id, channel_slug))
        variant_channel_listing = VariantChannelListingByVariantIdAndChannelSlugLoader(
            context
        ).load((root.node.id, channel_slug))
        channel = ChannelBySlugLoader(context).load(channel_slug)
        tax_class_id_loader = TaxClassIdByProductIdLoader(context).load(
            root.node.product_id
        )

        def load_tax_configuration(data):
            (
                product_channel_listing,
                variant_channel_listing,
                channel,
                tax_class_id,
            ) = data

            if not variant_channel_listing or not product_channel_listing:
                return None
            country_code = get_active_country(channel, address_data=address)

            def load_tax_country_exceptions(tax_config):
                def load_default_tax_rate(tax_configs_per_country):
                    def calculate_pricing_info(data):
                        country_rates, default_country_rate_obj = data

                        tax_config_country = next(
                            (
                                tc
                                for tc in tax_configs_per_country
                                if tc.country.code == country_code
                            ),
                            None,
                        )
                        tax_calculation_strategy = get_tax_calculation_strategy(
                            tax_config, tax_config_country
                        )

                        default_tax_rate = (
                            default_country_rate_obj.rate
                            if default_country_rate_obj
                            else Decimal(0)
                        )
                        tax_rate = get_tax_rate_for_country(
                            country_rates, default_tax_rate, country_code
                        )

                        availability = get_variant_availability(
                            variant_channel_listing=variant_channel_listing,
                            product_channel_listing=product_channel_listing,
                            prices_entered_with_tax=tax_config.prices_entered_with_tax,
                            tax_calculation_strategy=tax_calculation_strategy,
                            tax_rate=tax_rate,
                        )
                        return (
                            VariantPricingInfo(**asdict(availability))
                            if availability
                            else None
                        )

                    country_rates = (
                        TaxClassCountryRateByTaxClassIDLoader(context).load(
                            tax_class_id
                        )
                        if tax_class_id
                        else Promise.resolve([])
                    )
                    default_rate = TaxClassDefaultRateByCountryLoader(context).load(
                        country_code
                    )
                    return Promise.all([country_rates, default_rate]).then(
                        calculate_pricing_info
                    )

                return (
                    TaxConfigurationPerCountryByTaxConfigurationIDLoader(context)
                    .load(tax_config.id)
                    .then(load_default_tax_rate)
                )

            return (
                TaxConfigurationByChannelId(context)
                .load(channel.id)
                .then(load_tax_country_exceptions)
            )

        return Promise.all(
            [
                product_channel_listing,
                variant_channel_listing,
                channel,
                tax_class_id_loader,
            ]
        ).then(load_tax_configuration)

    @staticmethod
    def resolve_product(root: ChannelContext[models.ProductVariant], info):
        product = ProductByIdLoader(info.context).load(root.node.product_id)
        return product.then(
            lambda product: ChannelContext(node=product, channel_slug=root.channel_slug)
        )

    @staticmethod
    def resolve_quantity_ordered(root: ChannelContext[models.ProductVariant], _info):
        # This field is added through annotation when using the
        # `resolve_report_product_sales` resolver.
        return getattr(root.node, "quantity_ordered", None)

    @staticmethod
    @traced_resolver
    def resolve_revenue(root: ChannelContext[models.ProductVariant], info, *, period):
        start_date = reporting_period_to_date(period)
        variant = root.node
        channel_slug = root.channel_slug

        def calculate_revenue_with_channel(channel):
            if not channel:
                return None

            def calculate_revenue_with_order_lines(order_lines):
                def calculate_revenue_with_orders(orders):
                    orders_dict = {order.id: order for order in orders}
                    return calculate_revenue_for_variant(
                        variant,
                        start_date,
                        order_lines,
                        orders_dict,
                        channel.currency_code,
                    )

                order_ids = [order_line.order_id for order_line in order_lines]
                return (
                    OrderByIdLoader(info.context)
                    .load_many(order_ids)
                    .then(calculate_revenue_with_orders)
                )

            return (
                OrderLinesByVariantIdAndChannelIdLoader(info.context)
                .load((variant.id, channel.id))
                .then(calculate_revenue_with_order_lines)
            )

        return (
            ChannelBySlugLoader(info.context)
            .load(channel_slug)
            .then(calculate_revenue_with_channel)
        )

    @staticmethod
    def resolve_media(root: ChannelContext[models.ProductVariant], info):
        return MediaByProductVariantIdLoader(info.context).load(root.node.id)

    @staticmethod
    def resolve_images(root: ChannelContext[models.ProductVariant], info):
        return ImagesByProductVariantIdLoader(info.context).load(root.node.id)

    @staticmethod
    def resolve_weight(root: ChannelContext[models.ProductVariant], _info):
        return convert_weight_to_default_weight_unit(root.node.weight)

    @staticmethod
    @traced_resolver
    def resolve_preorder(root: ChannelContext[models.ProductVariant], info):
        variant = root.node

        variant_channel_listings = VariantChannelListingByVariantIdLoader(
            info.context
        ).load(variant.id)

        def calculate_global_sold_units(variant_channel_listings):
            global_sold_units = sum(
                channel_listing.preorder_quantity_allocated
                for channel_listing in variant_channel_listings
            )
            return (
                PreorderData(
                    global_threshold=variant.preorder_global_threshold,
                    global_sold_units=global_sold_units,
                    end_date=variant.preorder_end_date,
                )
                if variant.is_preorder_active()
                else None
            )

        return variant_channel_listings.then(calculate_global_sold_units)

    @staticmethod
    def __resolve_references(roots: list["ProductVariant"], info):
        requestor = get_user_or_app_from_context(info.context)

        channels = defaultdict(set)
        roots_ids = []
        for root in roots:
            roots_ids.append(f"{root.channel}_{root.id}")
            channels[root.channel].add(root.id)

        variants = {}
        database_connection_name = get_database_connection_name(info.context)
        channels_map = Channel.objects.using(database_connection_name).in_bulk(
            set(channels.keys()), field_name="slug"
        )
        for channel_slug, ids in channels.items():
            limited_channel_access = False if channel_slug is None else True
            qs = resolve_product_variants(
                info,
                requestor,
                ids=ids,
                channel=channels_map.get(channel_slug),
                limited_channel_access=limited_channel_access,
            ).qs
            for variant in qs:
                global_id = graphene.Node.to_global_id("ProductVariant", variant.id)
                variants[f"{channel_slug}_{global_id}"] = ChannelContext(
                    channel_slug=channel_slug, node=variant
                )

        return [variants.get(root_id) for root_id in roots_ids]


class ProductVariantCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        node = ProductVariant


@federated_entity("id channel")
class Product(ChannelContextType[models.Product]):
    id = graphene.GlobalID(required=True, description="The ID of the product.")
    seo_title = graphene.String(description="SEO title of the product.")
    seo_description = graphene.String(description="SEO description of the product.")
    name = graphene.String(required=True, description="SEO description of the product.")
    description = JSONString(description="Description of the product." + RICH_CONTENT)
    product_type = graphene.Field(
        lambda: ProductType, required=True, description="Type of the product."
    )
    slug = graphene.String(required=True, description="Slug of the product.")
    category = graphene.Field("saleor.graphql.product.types.categories.Category")
    created = DateTime(
        required=True, description="The date and time when the product was created."
    )
    updated_at = DateTime(
        required=True,
        description="The date and time when the product was last updated.",
    )
    charge_taxes = graphene.Boolean(
        required=True,
        deprecation_reason="Use `Channel.taxConfiguration` field to determine whether tax collection is enabled.",
    )
    weight = graphene.Field(Weight, description="Weight of the product.")
    default_variant = graphene.Field(
        ProductVariant, description="Default variant of the product."
    )
    rating = graphene.Float(description="Rating of the product.")
    channel = graphene.String(
        description=(
            "Channel given to retrieve this product. Also used by federation "
            "gateway to resolve this object in a federated query."
        ),
    )
    description_json = JSONString(
        description="Description of the product." + RICH_CONTENT,
        deprecation_reason="Use the `description` field instead.",
    )
    thumbnail = ThumbnailField(description="Thumbnail of the product.")
    pricing = graphene.Field(
        ProductPricingInfo,
        address=destination_address_argument,
        description=(
            "Lists the storefront product's pricing, the current price and discounts, "
            "only meant for displaying."
        ),
    )
    is_available = graphene.Boolean(
        address=destination_address_argument,
        description=(
            "Whether the product is in stock, set as available for purchase in the "
            "given channel, and published."
        ),
    )
    tax_type = graphene.Field(
        TaxType,
        description="A type of tax. Assigned by enabled tax gateway",
        deprecation_reason="Use `taxClass` field instead.",
    )
    assigned_attribute = graphene.Field(
        AssignedAttribute,
        slug=graphene.Argument(
            graphene.String,
            description="Slug of the attribute",
            required=True,
        ),
        description="Get a single attribute attached to product by attribute slug."
        + ADDED_IN_322,
    )
    assigned_attributes = NonNullList(
        AssignedAttribute,
        required=True,
        description="List of attributes assigned to this product." + ADDED_IN_322,
        limit=PositiveInt(
            description=(
                "Maximum number of attributes to return. "
                f"Default is {DEFAULT_NESTED_LIST_LIMIT}."
            ),
            default_value=DEFAULT_NESTED_LIST_LIMIT,
        ),
    )

    attribute = graphene.Field(
        SelectedAttribute,
        slug=graphene.Argument(
            graphene.String,
            description="Slug of the attribute",
            required=True,
        ),
        description="Get a single attribute attached to product by attribute slug.",
        deprecation_reason="Use the `assignedAttribute` field instead.",
    )
    attributes = NonNullList(
        SelectedAttribute,
        required=True,
        description="List of attributes assigned to this product.",
        deprecation_reason="Use the `assignedAttributes` field instead.",
    )
    channel_listings = PermissionsField(
        NonNullList(ProductChannelListing),
        description="List of availability in channels for the product.",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    media_by_id = graphene.Field(
        lambda: ProductMedia,
        id=graphene.Argument(
            graphene.ID, description="ID of a product media.", required=True
        ),
        description="Get a single product media by ID.",
    )
    image_by_id = graphene.Field(
        lambda: ProductImage,
        id=graphene.Argument(
            graphene.ID, description="ID of a product image.", required=True
        ),
        description="Get a single product image by ID.",
        deprecation_reason="Use the `mediaById` field instead.",
    )
    variant = graphene.Field(
        ProductVariant,
        id=graphene.Argument(graphene.ID, description="ID of the variant."),
        sku=graphene.Argument(graphene.String, description="SKU of the variant."),
        description="Get a single variant by SKU or ID.",
        deprecation_reason="Use top-level `variant` query.",
    )
    variants = NonNullList(
        ProductVariant,
        description=(
            "List of variants for the product. Requires the following permissions to "
            "include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
        deprecation_reason="Use `productVariants` field instead.",
    )
    product_variants = FilterConnectionField(
        ProductVariantCountableConnection,
        filter=ProductVariantFilterInput(
            description=(
                f"Filtering options for product variant. {DEPRECATED_IN_3X_INPUT} "
                "Use `where` filter instead."
            )
        ),
        where=ProductVariantWhereInput(
            description="Where filtering options for product variants."
        ),
        sort_by=ProductVariantSortingInput(description="Sort products variants."),
        description=(
            "List of variants for the product. Requires the following permissions to "
            "include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}." + ADDED_IN_321
        ),
    )
    media = NonNullList(
        lambda: ProductMedia,
        sort_by=graphene.Argument(MediaSortingInput, description="Sort media."),
        description="List of media for the product.",
    )
    images = NonNullList(
        lambda: ProductImage,
        description="List of images for the product.",
        deprecation_reason="Use the `media` field instead.",
    )
    collections = NonNullList(
        "saleor.graphql.product.types.collections.Collection",
        description=(
            "List of collections for the product. Requires the following permissions "
            "to include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
    )
    translation = TranslationField(
        ProductTranslation,
        type_name="product",
        resolver=ChannelContextType.resolve_translation,
    )
    available_for_purchase = Date(
        description="Date when product is available for purchase.",
        deprecation_reason="Use the `availableForPurchaseAt` field to fetch the available for purchase date.",
    )
    available_for_purchase_at = DateTime(
        description="Date when product is available for purchase."
    )
    is_available_for_purchase = graphene.Boolean(
        description=(
            "Refers to a state that can be set by admins to control whether a product "
            "is available for purchase in storefronts. This does not guarantee the "
            "availability of stock. When set to `False`, this product is still visible "
            "to customers, but it cannot be purchased."
        )
    )
    tax_class = PermissionsField(
        TaxClass,
        description=(
            "Tax class assigned to this product type. All products of this product "
            "type use this tax class, unless it's overridden in the `Product` type."
        ),
        required=False,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
    )
    external_reference = graphene.String(
        description="External ID of this product.",
        required=False,
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = "Represents an individual item for sale in the storefront."
        interfaces = [relay.Node, ObjectWithMetadata, ObjectWithAttributes]
        model = models.Product

    @staticmethod
    def resolve_created(root: ChannelContext[models.Product], _info):
        created_at = root.node.created_at
        return created_at

    @staticmethod
    def resolve_channel(root: ChannelContext[models.Product], _info):
        return root.channel_slug

    @staticmethod
    def resolve_default_variant(root: ChannelContext[models.Product], info):
        default_variant_id = root.node.default_variant_id
        if default_variant_id is None:
            return None

        def return_default_variant_with_channel_context(variant):
            return ChannelContext(node=variant, channel_slug=root.channel_slug)

        return (
            ProductVariantByIdLoader(info.context)
            .load(default_variant_id)
            .then(return_default_variant_with_channel_context)
        )

    @staticmethod
    def resolve_category(root: ChannelContext[models.Product], info):
        category_id = root.node.category_id
        if category_id is None:
            return None
        return CategoryByIdLoader(info.context).load(category_id)

    @staticmethod
    def resolve_description_json(root: ChannelContext[models.Product], _info):
        description = root.node.description
        return description if description is not None else {}

    @staticmethod
    def resolve_tax_type(root: ChannelContext[models.Product], info):
        @allow_writer_in_context(info.context)
        def with_tax_class(data):
            tax_class, manager = data
            tax_data = manager.get_tax_code_from_object_meta(
                tax_class, channel_slug=root.channel_slug
            )
            return TaxType(tax_code=tax_data.code, description=tax_data.description)

        if root.node.tax_class_id:
            tax_class = TaxClassByIdLoader(info.context).load(root.node.tax_class_id)
            manager = get_plugin_manager_promise(info.context)
            return Promise.all([tax_class, manager]).then(with_tax_class)

        return None

    @staticmethod
    def resolve_thumbnail(
        root: ChannelContext[models.Product],
        info,
        *,
        size: int = 256,
        format: str | None = None,
    ):
        format = get_thumbnail_format(format)
        size = get_thumbnail_size(size)

        def return_first_thumbnail(product_media):
            if not product_media:
                return None

            image = product_media[0]
            oembed_data = image.oembed_data

            if oembed_data.get("thumbnail_url"):
                return Image(alt=oembed_data["title"], url=oembed_data["thumbnail_url"])

            def _resolve_url(thumbnail):
                url = get_image_or_proxy_url(
                    thumbnail, image.id, "ProductMedia", size, format
                )
                return Image(alt=image.alt, url=build_absolute_uri(url))

            return (
                ThumbnailByProductMediaIdSizeAndFormatLoader(info.context)
                .load((image.id, size, format))
                .then(_resolve_url)
            )

        return (
            MediaByProductIdLoader(info.context)
            .load(root.node.id)
            .then(return_first_thumbnail)
        )

    @staticmethod
    def resolve_url(_root, _info):
        return ""

    @staticmethod
    def resolve_pricing(root: ChannelContext[models.Product], info, *, address=None):
        if not root.channel_slug:
            return None

        channel_slug = str(root.channel_slug)
        context = info.context

        channel = ChannelBySlugLoader(context).load(channel_slug)
        product_channel_listing = ProductChannelListingByProductIdAndChannelSlugLoader(
            context
        ).load((root.node.id, channel_slug))
        variants_channel_listing = (
            VariantsChannelListingByProductIdAndChannelSlugLoader(context).load(
                (root.node.id, channel_slug)
            )
        )
        tax_class_id_loader = TaxClassIdByProductIdLoader(context).load(root.node.id)

        def load_tax_configuration(data):
            (
                channel,
                product_channel_listing,
                variants_channel_listing,
                tax_class_id,
            ) = data

            if not variants_channel_listing:
                return None
            country_code = get_active_country(channel, address_data=address)

            def load_tax_country_exceptions(tax_config):
                def load_default_tax_rate(tax_configs_per_country):
                    def calculate_pricing_info(data):
                        country_rates, default_country_rate_obj = data
                        tax_config_country = next(
                            (
                                tc
                                for tc in tax_configs_per_country
                                if tc.country.code == country_code
                            ),
                            None,
                        )
                        display_gross_prices = get_display_gross_prices(
                            tax_config,
                            tax_config_country,
                        )
                        tax_calculation_strategy = get_tax_calculation_strategy(
                            tax_config, tax_config_country
                        )

                        default_tax_rate = (
                            default_country_rate_obj.rate
                            if default_country_rate_obj
                            else Decimal(0)
                        )
                        tax_rate = get_tax_rate_for_country(
                            country_rates, default_tax_rate, country_code
                        )

                        availability = get_product_availability(
                            product_channel_listing=product_channel_listing,
                            variants_channel_listing=variants_channel_listing,
                            prices_entered_with_tax=tax_config.prices_entered_with_tax,
                            tax_calculation_strategy=tax_calculation_strategy,
                            tax_rate=tax_rate,
                        )

                        pricing_info = asdict(availability)
                        pricing_info["display_gross_prices"] = display_gross_prices
                        return ProductPricingInfo(**pricing_info)

                    country_rates = (
                        TaxClassCountryRateByTaxClassIDLoader(context).load(
                            tax_class_id
                        )
                        if tax_class_id
                        else Promise.resolve([])
                    )
                    default_rate = TaxClassDefaultRateByCountryLoader(context).load(
                        country_code
                    )
                    return Promise.all([country_rates, default_rate]).then(
                        calculate_pricing_info
                    )

                return (
                    TaxConfigurationPerCountryByTaxConfigurationIDLoader(context)
                    .load(tax_config.id)
                    .then(load_default_tax_rate)
                )

            return (
                TaxConfigurationByChannelId(context)
                .load(channel.id)
                .then(load_tax_country_exceptions)
            )

        return Promise.all(
            [
                channel,
                product_channel_listing,
                variants_channel_listing,
                tax_class_id_loader,
            ]
        ).then(load_tax_configuration)

    @staticmethod
    @traced_resolver
    def resolve_is_available(
        root: ChannelContext[models.Product], info, *, address=None
    ):
        if not root.channel_slug:
            return None

        channel_slug = str(root.channel_slug)
        country_code = address.country if address is not None else None

        requestor = get_user_or_app_from_context(info.context)

        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )

        def calculate_is_available(quantities):
            for qty in quantities:
                if qty > 0:
                    return True
            return False

        def load_variants_availability(variants):
            keys = [(variant.id, country_code, channel_slug) for variant in variants]
            return AvailableQuantityByProductVariantIdCountryCodeAndChannelSlugLoader(
                info.context
            ).load_many(keys)

        def check_variant_availability():
            if has_required_permissions and not channel_slug:
                variants = ProductVariantsByProductIdLoader(info.context).load(
                    root.node.id
                )
            elif has_required_permissions and channel_slug:
                variants = ProductVariantsByProductIdAndChannel(info.context).load(
                    (root.node.id, channel_slug)
                )
            else:
                variants = AvailableProductVariantsByProductIdAndChannel(
                    info.context
                ).load((root.node.id, channel_slug))
            return variants.then(load_variants_availability).then(
                calculate_is_available
            )

        def check_is_available_for_purchase(product_channel_listing):
            if product_channel_listing:
                if product_channel_listing.is_available_for_purchase():
                    return check_variant_availability()
            return False

        return (
            ProductChannelListingByProductIdAndChannelSlugLoader(info.context)
            .load((root.node.id, channel_slug))
            .then(check_is_available_for_purchase)
        )

    @classmethod
    def resolve_assigned_attribute(
        cls, root: ChannelContext[models.Product], info, slug
    ):
        return resolve_product_attribute(root, info, slug)

    @classmethod
    def resolve_attribute(cls, root: ChannelContext[models.Product], info, slug):
        return resolve_product_attribute(root, info, slug)

    @classmethod
    def resolve_assigned_attributes(
        cls,
        root: ChannelContext[models.Product],
        info,
        limit: int = DEFAULT_NESTED_LIST_LIMIT,
    ):
        return resolve_product_attributes(root, info, limit=limit)

    @classmethod
    def resolve_attributes(cls, root: ChannelContext[models.Product], info):
        return resolve_product_attributes(root, info, limit=None)

    @staticmethod
    def resolve_media_by_id(root: ChannelContext[models.Product], info, *, id):
        _type, pk = from_global_id_or_error(id, ProductMedia)
        return (
            root.node.media.using(get_database_connection_name(info.context))
            .filter(pk=pk)
            .first()
        )

    @staticmethod
    def resolve_image_by_id(root: ChannelContext[models.Product], info, *, id):
        _type, pk = from_global_id_or_error(id, ProductImage)
        return (
            root.node.media.using(get_database_connection_name(info.context))
            .filter(pk=pk)
            .first()
        )

    @staticmethod
    def resolve_media(root: ChannelContext[models.Product], info, sort_by=None):
        if sort_by is None:
            sort_by = {
                "field": ["sort_order"],
                "direction": "",
            }

        def sort_media(media) -> list[ProductMedia]:
            reversed = sort_by["direction"] == "-"

            # Nullable first,
            # achieved by adding the number of nonnull fields as firt element of tuple
            def key(x):
                values_tuple = tuple(
                    getattr(x, field)
                    for field in sort_by["field"]
                    if getattr(x, field) is not None
                )
                values_tuple = (len(values_tuple),) + values_tuple
                return values_tuple

            media_sorted = sorted(
                media,
                key=key,
                reverse=reversed,
            )
            return media_sorted

        return MediaByProductIdLoader(info.context).load(root.node.id).then(sort_media)

    @staticmethod
    def resolve_images(root: ChannelContext[models.Product], info):
        return ImagesByProductIdLoader(info.context).load(root.node.id)

    @staticmethod
    def resolve_variant(root: ChannelContext[models.Product], info, id=None, sku=None):
        validate_one_of_args_is_in_query("id", id, "sku", sku)

        def get_product_variant(
            product_variants,
        ) -> ProductVariant | None:
            if id:
                id_type, variant_id = graphene.Node.from_global_id(id)
                if id_type != "ProductVariant":
                    return None

                return next(
                    (
                        variant
                        for variant in product_variants
                        if variant.node.id == int(variant_id)
                    ),
                    None,
                )
            if sku:
                return next(
                    (
                        variant
                        for variant in product_variants
                        if variant.node.sku == sku
                    ),
                    None,
                )
            return None

        variants = Product.resolve_variants(root, info)
        return variants.then(get_product_variant)

    @staticmethod
    def resolve_variants(root: ChannelContext[models.Product], info):
        requestor = get_user_or_app_from_context(info.context)
        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )
        if has_required_permissions and not root.channel_slug:
            variants = ProductVariantsByProductIdLoader(info.context).load(root.node.id)
        elif has_required_permissions and root.channel_slug:
            variants = ProductVariantsByProductIdAndChannel(info.context).load(
                (root.node.id, root.channel_slug)
            )
        else:
            variants = AvailableProductVariantsByProductIdAndChannel(info.context).load(
                (root.node.id, root.channel_slug)
            )

        def map_channel_context(variants):
            return [
                ChannelContext(node=variant, channel_slug=root.channel_slug)
                for variant in variants
            ]

        return variants.then(map_channel_context)

    @staticmethod
    def resolve_product_variants(root: ChannelContext[models.Product], info, **kwargs):
        requestor = get_user_or_app_from_context(info.context)

        def _resolve_product_variants(channel_obj):
            limited_channel_access = False if channel_slug is None else True
            qs = resolve_product_variants(
                info,
                channel=channel_obj,
                product_id=root.node.pk,
                limited_channel_access=limited_channel_access,
                requestor=requestor,
            )
            kwargs["channel"] = qs.channel_slug
            qs = filter_connection_queryset(
                qs, kwargs, allow_replica=info.context.allow_replica
            )
            return create_connection_slice(
                qs, info, kwargs, ProductVariantCountableConnection
            )

        if channel_slug := root.channel_slug:
            return (
                ChannelBySlugLoader(info.context)
                .load(channel_slug)
                .then(_resolve_product_variants)
            )
        return _resolve_product_variants(None)

    @staticmethod
    def resolve_channel_listings(root: ChannelContext[models.Product], info):
        return ProductChannelListingByProductIdLoader(info.context).load(root.node.id)

    @staticmethod
    @traced_resolver
    def resolve_collections(root: ChannelContext[models.Product], info):
        requestor = get_user_or_app_from_context(info.context)

        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )

        def return_collections(collections):
            if has_required_permissions:
                return [
                    ChannelContext(node=collection, channel_slug=root.channel_slug)
                    for collection in collections
                ]

            dataloader_keys = [
                (collection.id, str(root.channel_slug)) for collection in collections
            ]
            CollectionChannelListingLoader = (
                CollectionChannelListingByCollectionIdAndChannelSlugLoader
            )
            channel_listings = CollectionChannelListingLoader(info.context).load_many(
                dataloader_keys
            )

            def return_visible_collections(channel_listings):
                visible_collections = []
                channel_listings_dict = {
                    channel_listing.collection_id: channel_listing
                    for channel_listing in channel_listings
                    if channel_listing
                }

                for collection in collections:
                    channel_listing = channel_listings_dict.get(collection.id)
                    if channel_listing and channel_listing.is_visible:
                        visible_collections.append(collection)

                return [
                    ChannelContext(node=collection, channel_slug=root.channel_slug)
                    for collection in visible_collections
                ]

            return channel_listings.then(return_visible_collections)

        return (
            CollectionsByProductIdLoader(info.context)
            .load(root.node.id)
            .then(return_collections)
        )

    @staticmethod
    def resolve_weight(root: ChannelContext[models.Product], _info):
        return convert_weight_to_default_weight_unit(root.node.weight)

    @staticmethod
    def resolve_is_available_for_purchase(root: ChannelContext[models.Product], info):
        if not root.channel_slug:
            return None
        channel_slug = str(root.channel_slug)

        def calculate_is_available_for_purchase(product_channel_listing):
            if not product_channel_listing:
                return None
            return product_channel_listing.is_available_for_purchase()

        return (
            ProductChannelListingByProductIdAndChannelSlugLoader(info.context)
            .load((root.node.id, channel_slug))
            .then(calculate_is_available_for_purchase)
        )

    @staticmethod
    def resolve_available_for_purchase(root: ChannelContext[models.Product], info):
        if not root.channel_slug:
            return None
        channel_slug = str(root.channel_slug)

        def calculate_available_for_purchase(product_channel_listing):
            if not product_channel_listing:
                return None
            return product_channel_listing.available_for_purchase_at

        return (
            ProductChannelListingByProductIdAndChannelSlugLoader(info.context)
            .load((root.node.id, channel_slug))
            .then(calculate_available_for_purchase)
        )

    @staticmethod
    def resolve_available_for_purchase_at(root: ChannelContext[models.Product], info):
        if not root.channel_slug:
            return None
        channel_slug = str(root.channel_slug)

        def calculate_available_for_purchase(product_channel_listing):
            if not product_channel_listing:
                return None
            return product_channel_listing.available_for_purchase_at

        return (
            ProductChannelListingByProductIdAndChannelSlugLoader(info.context)
            .load((root.node.id, channel_slug))
            .then(calculate_available_for_purchase)
        )

    @staticmethod
    def resolve_product_type(root: ChannelContext[models.Product], info):
        return ProductTypeByIdLoader(info.context).load(root.node.product_type_id)

    @staticmethod
    def resolve_tax_class(root: ChannelContext[models.Product], info):
        product_type = (
            ProductTypeByIdLoader(info.context).load(root.node.product_type_id)
            if not root.node.tax_class_id
            else None
        )

        def resolve_tax_class(product_type):
            tax_class_id = (
                product_type.tax_class_id if product_type else root.node.tax_class_id
            )
            return (
                TaxClassByIdLoader(info.context).load(tax_class_id)
                if tax_class_id
                else None
            )

        return Promise.resolve(product_type).then(resolve_tax_class)

    def resolve_charge_taxes(root: ChannelContext[models.Product], info):
        # Deprecated: this field is deprecated as it only checks whether there are any
        # non-zero flat rates set for a product. Instead channel tax configuration
        # should be used to check whether taxes are charged.

        tax_class_id = root.node.tax_class_id
        if not tax_class_id:
            product_type = ProductTypeByIdLoader(info.context).load(
                root.node.product_type_id
            )

            def with_product_type(product_type):
                tax_class_id = product_type.tax_class_id
                return (
                    ProductChargeTaxesByTaxClassIdLoader(info.context).load(
                        tax_class_id
                    )
                    if tax_class_id
                    else False
                )

            return product_type.then(with_product_type)

        return ProductChargeTaxesByTaxClassIdLoader(info.context).load(tax_class_id)

    @staticmethod
    def __resolve_references(roots: list["Product"], info):
        requestor = get_user_or_app_from_context(info.context)
        channels = defaultdict(set)
        roots_ids = []
        for root in roots:
            _, root_id = from_global_id_or_error(root.id, Product, raise_error=True)
            if root_id:
                roots_ids.append(f"{root.channel}_{root_id}")
                channels[root.channel].add(root_id)

        products = {}

        database_connection_name = get_database_connection_name(info.context)
        channels_map = Channel.objects.using(database_connection_name).in_bulk(
            set(channels.keys()), field_name="slug"
        )
        for channel_slug, ids in channels.items():
            limited_channel_access = False if channel_slug is None else True
            queryset = resolve_products(
                info, requestor, channels_map.get(channel_slug), limited_channel_access
            ).qs.filter(id__in=ids)

            for product in queryset:
                products[f"{channel_slug}_{product.id}"] = ChannelContext(
                    channel_slug=channel_slug, node=product
                )

        return [products.get(root_id) for root_id in roots_ids]


class ProductCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        node = Product


@federated_entity("id")
class ProductType(ModelObjectType[models.ProductType]):
    id = graphene.GlobalID(required=True, description="The ID of the product type.")
    name = graphene.String(required=True, description="Name of the product type.")
    slug = graphene.String(required=True, description="Slug of the product type.")
    has_variants = graphene.Boolean(
        required=True, description="Whether the product type has variants."
    )
    is_shipping_required = graphene.Boolean(
        required=True, description="Whether shipping is required for this product type."
    )
    is_digital = graphene.Boolean(
        required=True, description="Whether the product type is digital."
    )
    weight = graphene.Field(Weight, description="Weight of the product type.")
    kind = ProductTypeKindEnum(description="The product type kind.", required=True)
    products = ConnectionField(
        ProductCountableConnection,
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of products of this type.",
        deprecation_reason="Use the top-level `products` query with the `productTypes` filter.",
    )
    tax_type = graphene.Field(
        TaxType,
        description="A type of tax. Assigned by enabled tax gateway",
        deprecation_reason="Use `taxClass` field instead.",
    )
    tax_class = PermissionsField(
        TaxClass,
        description=(
            "Tax class assigned to this product type. All products of this product "
            "type use this tax class, unless it's overridden in the `Product` type."
        ),
        required=False,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
    )
    variant_attributes = NonNullList(
        Attribute,
        description="Variant attributes of that product type.",
        variant_selection=graphene.Argument(
            VariantAttributeScope,
            description="Define scope of returned attributes.",
        ),
        deprecation_reason="Use `assignedVariantAttributes` instead.",
    )
    assigned_variant_attributes = NonNullList(
        AssignedVariantAttribute,
        description=(
            "Variant attributes of that product type with attached variant selection."
        ),
        variant_selection=graphene.Argument(
            VariantAttributeScope,
            description="Define scope of returned attributes.",
        ),
    )
    product_attributes = NonNullList(
        Attribute, description="Product attributes of that product type."
    )
    available_attributes = FilterConnectionField(
        AttributeCountableConnection,
        filter=AttributeFilterInput(
            description=(
                "Filtering options for attributes of this product type. "
                f"{DEPRECATED_IN_3X_INPUT} Use `where` filter instead."
            )
        ),
        where=AttributeWhereInput(
            description="Where filtering options for attributes of this product type."
        ),
        search=graphene.String(description="Search attributes."),
        description="List of attributes which can be assigned to this product type.",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )

    class Meta:
        description = (
            "Represents a type of product. It defines what attributes are available to "
            "products of this type."
        )
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.ProductType

    @staticmethod
    def resolve_tax_type(root: models.ProductType, info):
        @allow_writer_in_context(info.context)
        def with_tax_class(data):
            tax_class, manager = data
            tax_data = manager.get_tax_code_from_object_meta(
                tax_class, channel_slug=None
            )
            return TaxType(tax_code=tax_data.code, description=tax_data.description)

        if root.tax_class_id:
            tax_class = TaxClassByIdLoader(info.context).load(root.tax_class_id)
            manager = get_plugin_manager_promise(info.context)
            return Promise.all([tax_class, manager]).then(with_tax_class)

        return None

    @staticmethod
    def resolve_product_attributes(root: models.ProductType, info):
        def unpack_attributes(attributes):
            return [ChannelContext(attr, None) for attr, *_ in attributes]

        requestor = get_user_or_app_from_context(info.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(ProductPermissions.MANAGE_PRODUCTS)
        ):
            return (
                ProductAttributesAllByProductTypeIdLoader(info.context)
                .load(root.pk)
                .then(unpack_attributes)
            )
        return (
            ProductAttributesVisibleInStorefrontByProductTypeIdLoader(info.context)
            .load(root.pk)
            .then(unpack_attributes)
        )

    @staticmethod
    @traced_resolver
    def resolve_variant_attributes(
        root: models.ProductType,
        info,
        variant_selection: str | None = None,
    ):
        def apply_variant_selection_filter(attributes):
            if not variant_selection or variant_selection == VariantAttributeScope.ALL:
                return [ChannelContext(attr, None) for attr, *_ in attributes]
            variant_selection_attrs = get_variant_selection_attributes(attributes)
            if variant_selection == VariantAttributeScope.VARIANT_SELECTION:
                return [
                    ChannelContext(attr, None) for attr, *_ in variant_selection_attrs
                ]
            return [
                ChannelContext(attr, None)
                for attr, variant_selection in attributes
                if (attr, variant_selection) not in variant_selection_attrs
            ]

        requestor = get_user_or_app_from_context(info.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(ProductPermissions.MANAGE_PRODUCTS)
        ):
            return (
                VariantAttributesAllByProductTypeIdLoader(info.context)
                .load(root.pk)
                .then(apply_variant_selection_filter)
            )
        return (
            VariantAttributesVisibleInStorefrontByProductTypeIdLoader(info.context)
            .load(root.pk)
            .then(apply_variant_selection_filter)
        )

    @staticmethod
    @traced_resolver
    def resolve_assigned_variant_attributes(
        root: models.ProductType,
        info,
        variant_selection: str | None = None,
    ):
        def apply_variant_selection_filter(attributes):
            if not variant_selection or variant_selection == VariantAttributeScope.ALL:
                return [
                    {
                        "attribute": ChannelContext(attr, None),
                        "variant_selection": variant_selection,
                    }
                    for attr, variant_selection in attributes
                ]
            variant_selection_attrs = get_variant_selection_attributes(attributes)
            if variant_selection == VariantAttributeScope.VARIANT_SELECTION:
                return [
                    {
                        "attribute": ChannelContext(attr, None),
                        "variant_selection": variant_selection,
                    }
                    for attr, variant_selection in variant_selection_attrs
                ]
            return [
                {
                    "attribute": ChannelContext(attr, None),
                    "variant_selection": variant_selection,
                }
                for attr, variant_selection in attributes
                if (attr, variant_selection) not in variant_selection_attrs
            ]

        requestor = get_user_or_app_from_context(info.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(ProductPermissions.MANAGE_PRODUCTS)
        ):
            return (
                VariantAttributesAllByProductTypeIdLoader(info.context)
                .load(root.pk)
                .then(apply_variant_selection_filter)
            )
        return (
            VariantAttributesVisibleInStorefrontByProductTypeIdLoader(info.context)
            .load(root.pk)
            .then(apply_variant_selection_filter)
        )

    @staticmethod
    def resolve_products(root: models.ProductType, info, *, channel=None, **kwargs):
        requestor = get_user_or_app_from_context(info.context)
        limited_channel_access = False if channel is None else True
        if channel is None:
            channel = get_default_channel_slug_or_graphql_error(
                allow_replica=info.context.allow_replica
            )

        def _resolve_products(channel_obj):
            qs = root.products.using(
                get_database_connection_name(info.context)
            ).visible_to_user(requestor, channel_obj, limited_channel_access)
            qs = ChannelQsContext(qs=qs, channel_slug=channel)
            kwargs["channel"] = channel
            return create_connection_slice(qs, info, kwargs, ProductCountableConnection)

        if channel:
            return (
                ChannelBySlugLoader(info.context)
                .load(str(channel))
                .then(_resolve_products)
            )
        return _resolve_products(None)

    @staticmethod
    def resolve_available_attributes(
        root: models.ProductType, info, search=None, **kwargs
    ):
        qs = attribute_models.Attribute.objects.using(
            get_database_connection_name(info.context)
        ).get_unassigned_product_type_attributes(root.pk)
        qs = resolve_attributes(info, qs=qs)
        qs = filter_connection_queryset(
            qs, kwargs, info.context, allow_replica=info.context.allow_replica
        )
        if search:
            qs = filter_attribute_search(qs, None, search)
        qs = ChannelQsContext(qs=qs, channel_slug=None)
        return create_connection_slice(qs, info, kwargs, AttributeCountableConnection)

    @staticmethod
    def resolve_weight(root: models.ProductType, _info):
        return convert_weight_to_default_weight_unit(root.weight)

    @staticmethod
    def resolve_tax_class(root: models.ProductType, info):
        return (
            TaxClassByIdLoader(info.context).load(root.tax_class_id)
            if root.tax_class_id
            else None
        )

    @staticmethod
    def __resolve_references(roots: list[models.ProductType], info):
        database_connection_name = get_database_connection_name(info.context)
        return resolve_federation_references(
            ProductType,
            roots,
            models.ProductType.objects.using(database_connection_name),
        )


class ProductTypeCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        node = ProductType


@federated_entity("id")
class ProductMedia(ModelObjectType[models.ProductMedia]):
    id = graphene.GlobalID(
        required=True, description="The unique ID of the product media."
    )
    sort_order = graphene.Int(description="The sort order of the media.")
    alt = graphene.String(required=True, description="The alt text of the media.")
    type = ProductMediaType(required=True, description="The type of the media.")
    oembed_data = JSONString(required=True, description="The oEmbed data of the media.")
    url = ThumbnailField(
        graphene.String, required=True, description="The URL of the media."
    )
    product_id = graphene.ID(description="Product id the media refers to.")

    class Meta:
        description = "Represents a product media."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.ProductMedia

    @staticmethod
    def resolve_url(
        root: models.ProductMedia,
        info,
        *,
        size: int | None = None,
        format: str | None = None,
    ) -> str | None | Promise[str]:
        if root.external_url:
            return root.external_url

        if not root.image:
            return None

        if size == 0:
            return build_absolute_uri(root.image.url)

        format = get_thumbnail_format(format)
        selected_size = get_thumbnail_size(size)

        def _resolve_url(thumbnail) -> str:
            url = get_image_or_proxy_url(
                thumbnail, str(root.id), "ProductMedia", selected_size, format
            )
            return build_absolute_uri(url)

        return (
            ThumbnailByProductMediaIdSizeAndFormatLoader(info.context)
            .load((root.id, selected_size, format))
            .then(_resolve_url)
        )

    @staticmethod
    def __resolve_references(roots: list["ProductMedia"], info):
        database_connection_name = get_database_connection_name(info.context)
        return resolve_federation_references(
            ProductMedia,
            roots,
            models.ProductMedia.objects.using(database_connection_name),
        )

    @staticmethod
    def resolve_product_id(root: models.ProductMedia, info) -> str:
        return graphene.Node.to_global_id("Product", root.product_id)


class ProductImage(BaseObjectType):
    id = graphene.ID(required=True, description="The ID of the image.")
    alt = graphene.String(description="The alt text of the image.")
    sort_order = graphene.Int(
        required=False,
        description=(
            "The new relative sorting position of the item (from -inf to +inf). "
            "1 moves the item one position forward, -1 moves the item one position "
            "backward, 0 leaves the item unchanged."
        ),
    )
    url = ThumbnailField(
        graphene.String, required=True, description="The URL of the image."
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        description = "Represents a product image."

    @staticmethod
    def resolve_id(root: models.ProductMedia, info) -> str:
        return graphene.Node.to_global_id("ProductImage", root.id)

    @staticmethod
    def resolve_url(
        root: models.ProductMedia,
        info,
        *,
        size: int | None = None,
        format: str | None = None,
    ) -> None | str | Promise[str]:
        if not root.image:
            return None

        if size == 0:
            return build_absolute_uri(root.image.url)

        format = get_thumbnail_format(format)
        selected_size = get_thumbnail_size(size)

        def _resolve_url(thumbnail):
            url = get_image_or_proxy_url(
                thumbnail, str(root.id), "ProductMedia", selected_size, format
            )
            return build_absolute_uri(url)

        return (
            ThumbnailByProductMediaIdSizeAndFormatLoader(info.context)
            .load((root.id, selected_size, format))
            .then(_resolve_url)
        )
