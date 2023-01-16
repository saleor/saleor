import sys
from collections import defaultdict
from dataclasses import asdict
from decimal import Decimal
from typing import List, Optional

import graphene
from graphene import relay
from promise import Promise

from ....attribute import models as attribute_models
from ....core.permissions import (
    AuthorizationFilters,
    OrderPermissions,
    ProductPermissions,
    has_one_of_permissions,
)
from ....core.utils import build_absolute_uri, get_currency_for_country
from ....core.weight import convert_weight_to_default_weight_unit
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
    get_tax_rate_for_tax_class,
)
from ....thumbnail.utils import get_image_or_proxy_url, get_thumbnail_size
from ....warehouse.reservations import is_reservation_enabled
from ...account import types as account_types
from ...account.enums import CountryCodeEnum
from ...attribute.filters import AttributeFilterInput
from ...attribute.resolvers import resolve_attributes
from ...attribute.types import (
    AssignedVariantAttribute,
    Attribute,
    AttributeCountableConnection,
    SelectedAttribute,
)
from ...channel import ChannelContext, ChannelQsContext
from ...channel.dataloaders import ChannelBySlugLoader
from ...channel.types import ChannelContextType, ChannelContextTypeWithMetadata
from ...channel.utils import get_default_channel_slug_or_graphql_error
from ...core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ...core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_39,
    ADDED_IN_310,
    DEPRECATED_IN_3X_FIELD,
    DEPRECATED_IN_3X_INPUT,
    PREVIEW_FEATURE,
    RICH_CONTENT,
)
from ...core.enums import ReportingPeriod
from ...core.federation import federated_entity, resolve_federation_references
from ...core.fields import (
    ConnectionField,
    FilterConnectionField,
    JSONString,
    PermissionsField,
)
from ...core.scalars import Date
from ...core.tracing import traced_resolver
from ...core.types import (
    Image,
    ModelObjectType,
    NonNullList,
    TaxedMoney,
    TaxedMoneyRange,
    TaxType,
    ThumbnailField,
    Weight,
)
from ...core.utils import from_global_id_or_error
from ...core.validators import validate_one_of_args_is_in_query
from ...discount.dataloaders import DiscountsByDateTimeLoader
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
    TaxClassByProductIdLoader,
    TaxClassByVariantIdLoader,
    TaxClassCountryRateByTaxClassIDLoader,
    TaxClassDefaultRateByCountryLoader,
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
    ProductAttributesByProductTypeIdLoader,
    ProductByIdLoader,
    ProductChannelListingByProductIdAndChannelSlugLoader,
    ProductChannelListingByProductIdLoader,
    ProductTypeByIdLoader,
    ProductVariantByIdLoader,
    ProductVariantsByProductIdLoader,
    SelectedAttributesByProductIdLoader,
    SelectedAttributesByProductVariantIdLoader,
    ThumbnailByProductMediaIdSizeAndFormatLoader,
    VariantAttributesByProductTypeIdLoader,
    VariantChannelListingByVariantIdAndChannelSlugLoader,
    VariantChannelListingByVariantIdLoader,
    VariantsChannelListingByProductIdAndChannelSlugLoader,
)
from ..enums import ProductMediaType, ProductTypeKindEnum, VariantAttributeScope
from ..resolvers import resolve_product_variants, resolve_products
from ..sorters import MediaSortingInput
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


class Margin(graphene.ObjectType):
    start = graphene.Int()
    stop = graphene.Int()


class BasePricingInfo(graphene.ObjectType):
    on_sale = graphene.Boolean(description="Whether it is in sale or not.")
    discount = graphene.Field(
        TaxedMoney, description="The discount amount if in sale (null otherwise)."
    )
    discount_local_currency = graphene.Field(
        TaxedMoney, description="The discount amount in the local currency."
    )


class VariantPricingInfo(BasePricingInfo):
    discount_local_currency = graphene.Field(
        TaxedMoney, description="The discount amount in the local currency."
    )
    price = graphene.Field(
        TaxedMoney, description="The price, with any discount subtracted."
    )
    price_undiscounted = graphene.Field(
        TaxedMoney, description="The price without any discount."
    )
    price_local_currency = graphene.Field(
        TaxedMoney, description="The discounted price in the local currency."
    )

    class Meta:
        description = "Represents availability of a variant in the storefront."


class ProductPricingInfo(BasePricingInfo):
    price_range = graphene.Field(
        TaxedMoneyRange,
        description="The discounted price range of the product variants.",
    )
    price_range_undiscounted = graphene.Field(
        TaxedMoneyRange,
        description="The undiscounted price range of the product variants.",
    )
    price_range_local_currency = graphene.Field(
        TaxedMoneyRange,
        description=(
            "The discounted price range of the product variants "
            "in the local currency."
        ),
    )
    display_gross_prices = graphene.Boolean(
        description=(
            "Determines whether this product's price displayed in a storefront "
            "should include taxes." + ADDED_IN_39 + PREVIEW_FEATURE
        ),
        required=True,
    )

    class Meta:
        description = "Represents availability of a product in the storefront."


class PreorderData(graphene.ObjectType):
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
    end_date = graphene.DateTime(required=False, description="Preorder end date.")

    class Meta:
        description = "Represents preorder settings for product variant."

    @staticmethod
    def resolve_global_threshold(root, _info):
        return root.global_threshold

    @staticmethod
    def resolve_global_sold_units(root, _info):
        return root.global_sold_units


@federated_entity("id channel")
class ProductVariant(ChannelContextTypeWithMetadata[models.ProductVariant]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    sku = graphene.String()
    product = graphene.Field(lambda: Product, required=True)
    track_inventory = graphene.Boolean(required=True)
    quantity_limit_per_customer = graphene.Int()
    weight = graphene.Field(Weight)
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
    attributes = NonNullList(
        SelectedAttribute,
        required=True,
        description="List of attributes assigned to this variant.",
        variant_selection=graphene.Argument(
            VariantAttributeScope,
            description="Define scope of returned attributes.",
        ),
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
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use the `media` field instead.",
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
        description=(
            "Preorder data for product variant." + ADDED_IN_31 + PREVIEW_FEATURE
        ),
    )
    created = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    external_reference = graphene.String(
        description=f"External ID of this product. {ADDED_IN_310}",
        required=False,
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Represents a version of a product such as different size or color."
        )
        interfaces = [relay.Node, ObjectWithMetadata]
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
        return StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader(
            info.context
        ).load((root.node.id, country_code, root.channel_slug))

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
        global_quantity_limit_per_checkout = site.settings.limit_quantity_per_checkout

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

    @staticmethod
    def resolve_attributes(
        root: ChannelContext[models.ProductVariant],
        info,
        variant_selection: Optional[str] = None,
    ):
        def apply_variant_selection_filter(selected_attributes):
            if not variant_selection or variant_selection == VariantAttributeScope.ALL:
                return selected_attributes
            attributes = [
                (selected_att["attribute"], selected_att["variant_selection"])
                for selected_att in selected_attributes
            ]
            variant_selection_attrs = [
                attr for attr, _ in get_variant_selection_attributes(attributes)
            ]

            if variant_selection == VariantAttributeScope.VARIANT_SELECTION:
                return [
                    selected_attribute
                    for selected_attribute in selected_attributes
                    if selected_attribute["attribute"] in variant_selection_attrs
                ]
            return [
                selected_attribute
                for selected_attribute in selected_attributes
                if selected_attribute["attribute"] not in variant_selection_attrs
            ]

        return (
            SelectedAttributesByProductVariantIdLoader(info.context)
            .load(root.node.id)
            .then(apply_variant_selection_filter)
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

        product = ProductByIdLoader(context).load(root.node.product_id)
        product_channel_listing = ProductChannelListingByProductIdAndChannelSlugLoader(
            context
        ).load((root.node.product_id, channel_slug))
        variant_channel_listing = VariantChannelListingByVariantIdAndChannelSlugLoader(
            context
        ).load((root.node.id, channel_slug))
        collections = CollectionsByProductIdLoader(context).load(root.node.product_id)
        channel = ChannelBySlugLoader(context).load(channel_slug)
        discounts = DiscountsByDateTimeLoader(context).load(info.context.request_time)
        tax_class = TaxClassByVariantIdLoader(context).load(root.node.id)
        manager = get_plugin_manager_promise(info.context)

        address_country = address.country if address is not None else None

        def load_tax_configuration(data):
            (
                product,
                product_channel_listing,
                variant_channel_listing,
                collections,
                channel,
                tax_class,
                discounts,
                manager,
            ) = data

            if not variant_channel_listing or not product_channel_listing:
                return None

            country_code = address_country or channel.default_country.code

            def load_tax_country_exceptions(tax_config):
                def load_default_tax_rate(tax_configs_per_country):
                    def calculate_pricing_info(data):
                        country_rates, default_country_rate_obj = data
                        local_currency = get_currency_for_country(country_code)

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
                        tax_rate = get_tax_rate_for_tax_class(
                            tax_class, country_rates, default_tax_rate, country_code
                        )

                        availability = get_variant_availability(
                            variant=root.node,
                            variant_channel_listing=variant_channel_listing,
                            product=product,
                            product_channel_listing=product_channel_listing,
                            collections=collections,
                            discounts=discounts,
                            channel=channel,
                            local_currency=local_currency,
                            prices_entered_with_tax=tax_config.prices_entered_with_tax,
                            tax_calculation_strategy=tax_calculation_strategy,
                            tax_rate=tax_rate,
                        )
                        return VariantPricingInfo(**asdict(availability))

                    country_rates = (
                        TaxClassCountryRateByTaxClassIDLoader(context).load(
                            tax_class.pk
                        )
                        if tax_class
                        else []
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
                product,
                product_channel_listing,
                variant_channel_listing,
                collections,
                channel,
                tax_class,
                discounts,
                manager,
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
    def __resolve_references(roots: List["ProductVariant"], info):
        requestor = get_user_or_app_from_context(info.context)
        requestor_has_access_to_all = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )

        channels = defaultdict(set)
        roots_ids = []
        for root in roots:
            roots_ids.append(f"{root.channel}_{root.id}")
            channels[root.channel].add(root.id)

        variants = {}
        for channel, ids in channels.items():
            qs = resolve_product_variants(
                info,
                requestor_has_access_to_all,
                requestor,
                ids=ids,
                channel_slug=channel,
            ).qs
            for variant in qs:
                global_id = graphene.Node.to_global_id("ProductVariant", variant.id)
                variants[f"{channel}_{global_id}"] = ChannelContext(
                    channel_slug=channel, node=variant
                )

        return [variants.get(root_id) for root_id in roots_ids]


class ProductVariantCountableConnection(CountableConnection):
    class Meta:
        node = ProductVariant


@federated_entity("id channel")
class Product(ChannelContextTypeWithMetadata[models.Product]):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    name = graphene.String(required=True)
    description = JSONString(description="Description of the product." + RICH_CONTENT)
    product_type = graphene.Field(lambda: ProductType, required=True)
    slug = graphene.String(required=True)
    category = graphene.Field("saleor.graphql.product.types.categories.Category")
    created = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    charge_taxes = graphene.Boolean(
        required=True,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `Channel.taxConfiguration` field to "
            "determine whether tax collection is enabled."
        ),
    )
    weight = graphene.Field(Weight)
    default_variant = graphene.Field(ProductVariant)
    rating = graphene.Float()
    channel = graphene.String(
        description=(
            "Channel given to retrieve this product. Also used by federation "
            "gateway to resolve this object in a federated query."
        ),
    )
    description_json = JSONString(
        description="Description of the product." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    thumbnail = ThumbnailField()
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
        description="Whether the product is in stock and visible or not.",
    )
    tax_type = graphene.Field(
        TaxType,
        description="A type of tax. Assigned by enabled tax gateway",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use `taxClass` field instead.",
    )
    attribute = graphene.Field(
        SelectedAttribute,
        slug=graphene.Argument(
            graphene.String,
            description="Slug of the attribute",
            required=True,
        ),
        description=(
            f"Get a single attribute attached to product by attribute slug."
            f"{ADDED_IN_39}"
        ),
    )
    attributes = NonNullList(
        SelectedAttribute,
        required=True,
        description="List of attributes assigned to this product.",
    )
    channel_listings = PermissionsField(
        NonNullList(ProductChannelListing),
        description="List of availability in channels for the product.",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    media_by_id = graphene.Field(
        lambda: ProductMedia,
        id=graphene.Argument(graphene.ID, description="ID of a product media."),
        description="Get a single product media by ID.",
    )
    image_by_id = graphene.Field(
        lambda: ProductImage,
        id=graphene.Argument(graphene.ID, description="ID of a product image."),
        description="Get a single product image by ID.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `mediaById` field instead."
        ),
    )
    variant = graphene.Field(
        ProductVariant,
        id=graphene.Argument(graphene.ID, description="ID of the variant."),
        sku=graphene.Argument(graphene.String, description="SKU of the variant."),
        description=f"Get a single variant by SKU or ID. {ADDED_IN_39}",
    )
    variants = NonNullList(
        ProductVariant,
        description=(
            "List of variants for the product. Requires the following permissions to "
            "include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
    )
    media = NonNullList(
        lambda: ProductMedia,
        sort_by=graphene.Argument(
            MediaSortingInput, description=f"Sort media. {ADDED_IN_39}"
        ),
        description="List of media for the product.",
    )
    images = NonNullList(
        lambda: ProductImage,
        description="List of images for the product.",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use the `media` field instead.",
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
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `availableForPurchaseAt` field to fetch "
            "the available for purchase date."
        ),
    )
    available_for_purchase_at = graphene.DateTime(
        description="Date when product is available for purchase."
    )
    is_available_for_purchase = graphene.Boolean(
        description="Whether the product is available for purchase."
    )
    tax_class = PermissionsField(
        TaxClass,
        description=(
            "Tax class assigned to this product type. All products of this product "
            "type use this tax class, unless it's overridden in the `Product` type."
        ),
        required=False,
        permissions=[AuthorizationFilters.AUTHENTICATED_STAFF_USER],
    )
    external_reference = graphene.String(
        description=f"External ID of this product. {ADDED_IN_310}",
        required=False,
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = "Represents an individual item for sale in the storefront."
        interfaces = [relay.Node, ObjectWithMetadata]
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
        def with_tax_class(data):
            tax_class, manager = data
            tax_data = manager.get_tax_code_from_object_meta(tax_class)
            return TaxType(tax_code=tax_data.code, description=tax_data.description)

        if root.node.tax_class_id:
            tax_class = TaxClassByIdLoader(info.context).load(root.node.tax_class_id)
            manager = get_plugin_manager_promise(info.context)
            return Promise.all([tax_class, manager]).then(with_tax_class)

        return None

    @staticmethod
    def resolve_thumbnail(
        root: ChannelContext[models.Product], info, *, size=256, format=None
    ):
        format = format.lower() if format else None
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
        address_country = address.country if address is not None else None

        channel = ChannelBySlugLoader(context).load(channel_slug)
        product_channel_listing = ProductChannelListingByProductIdAndChannelSlugLoader(
            context
        ).load((root.node.id, channel_slug))
        variants = ProductVariantsByProductIdLoader(context).load(root.node.id)
        variants_channel_listing = (
            VariantsChannelListingByProductIdAndChannelSlugLoader(context).load(
                (root.node.id, channel_slug)
            )
        )
        collections = CollectionsByProductIdLoader(context).load(root.node.id)
        discounts = DiscountsByDateTimeLoader(context).load(context.request_time)
        tax_class = TaxClassByProductIdLoader(context).load(root.node.id)

        def load_tax_configuration(data):
            (
                channel,
                product_channel_listing,
                variants,
                variants_channel_listing,
                collections,
                discounts,
                tax_class,
            ) = data

            if not variants_channel_listing:
                return None

            country_code = address_country or channel.default_country.code

            def load_tax_country_exceptions(tax_config):
                def load_default_tax_rate(tax_configs_per_country):
                    def calculate_pricing_info(data):
                        country_rates, default_country_rate_obj = data
                        local_currency = get_currency_for_country(country_code)
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
                        tax_rate = get_tax_rate_for_tax_class(
                            tax_class, country_rates, default_tax_rate, country_code
                        )

                        availability = get_product_availability(
                            product=root.node,
                            product_channel_listing=product_channel_listing,
                            variants=variants,
                            variants_channel_listing=variants_channel_listing,
                            collections=collections,
                            discounts=discounts,
                            channel=channel,
                            local_currency=local_currency,
                            prices_entered_with_tax=tax_config.prices_entered_with_tax,
                            tax_calculation_strategy=tax_calculation_strategy,
                            tax_rate=tax_rate,
                        )

                        pricing_info = asdict(availability)
                        pricing_info["display_gross_prices"] = display_gross_prices
                        return ProductPricingInfo(**pricing_info)

                    country_rates = (
                        TaxClassCountryRateByTaxClassIDLoader(context).load(
                            tax_class.pk
                        )
                        if tax_class
                        else []
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
                variants,
                variants_channel_listing,
                collections,
                discounts,
                tax_class,
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

    @staticmethod
    def resolve_attribute(root: ChannelContext[models.Product], info, slug):
        def get_selected_attribute_by_slug(
            attributes: List[SelectedAttribute],
        ) -> Optional[SelectedAttribute]:
            return next(
                (atr for atr in attributes if atr["attribute"].slug == slug),
                None,
            )

        return (
            SelectedAttributesByProductIdLoader(info.context)
            .load(root.node.id)
            .then(get_selected_attribute_by_slug)
        )

    @staticmethod
    def resolve_attributes(root: ChannelContext[models.Product], info):
        return SelectedAttributesByProductIdLoader(info.context).load(root.node.id)

    @staticmethod
    def resolve_media_by_id(root: ChannelContext[models.Product], _info, *, id):
        _type, pk = from_global_id_or_error(id, ProductMedia)
        return root.node.media.filter(pk=pk).first()

    @staticmethod
    def resolve_image_by_id(root: ChannelContext[models.Product], _info, *, id):
        _type, pk = from_global_id_or_error(id, ProductImage)
        return root.node.media.filter(pk=pk).first()

    @staticmethod
    def resolve_media(root: ChannelContext[models.Product], info, sort_by=None):
        if sort_by is None:
            sort_by = {
                "field": ["sort_order"],
                "direction": "",
            }

        def sort_media(media) -> list[ProductMedia]:
            reversed = sort_by["direction"] == "-"
            media_sorted = sorted(
                media,
                key=lambda x: tuple(getattr(x, field) for field in sort_by["field"]),
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
        ) -> Optional[ProductVariant]:
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
    def __resolve_references(roots: List["Product"], info):
        requestor = get_user_or_app_from_context(info.context)
        channels = defaultdict(set)
        roots_ids = []
        for root in roots:
            _, root_id = from_global_id_or_error(root.id, Product, raise_error=True)
            if root_id:
                roots_ids.append(f"{root.channel}_{root_id}")
                channels[root.channel].add(root_id)

        products = {}
        for channel, ids in channels.items():
            queryset = resolve_products(
                info, requestor, channel_slug=channel
            ).qs.filter(id__in=ids)

            for product in queryset:
                products[f"{channel}_{product.id}"] = ChannelContext(
                    channel_slug=channel, node=product
                )

        return [products.get(root_id) for root_id in roots_ids]


class ProductCountableConnection(CountableConnection):
    class Meta:
        node = Product


@federated_entity("id")
class ProductType(ModelObjectType[models.ProductType]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    slug = graphene.String(required=True)
    has_variants = graphene.Boolean(required=True)
    is_shipping_required = graphene.Boolean(required=True)
    is_digital = graphene.Boolean(required=True)
    weight = graphene.Field(Weight)
    kind = ProductTypeKindEnum(description="The product type kind.", required=True)
    products = ConnectionField(
        ProductCountableConnection,
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of products of this type.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the top-level `products` query with the `productTypes` filter."
        ),
    )
    tax_type = graphene.Field(
        TaxType,
        description="A type of tax. Assigned by enabled tax gateway",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use `taxClass` field instead.",
    )
    tax_class = PermissionsField(
        TaxClass,
        description=(
            "Tax class assigned to this product type. All products of this product "
            "type use this tax class, unless it's overridden in the `Product` type."
        ),
        required=False,
        permissions=[AuthorizationFilters.AUTHENTICATED_STAFF_USER],
    )
    variant_attributes = NonNullList(
        Attribute,
        description="Variant attributes of that product type.",
        variant_selection=graphene.Argument(
            VariantAttributeScope,
            description="Define scope of returned attributes.",
        ),
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `assignedVariantAttributes` instead."
        ),
    )
    assigned_variant_attributes = NonNullList(
        AssignedVariantAttribute,
        description=(
            "Variant attributes of that product type with attached variant selection."
            + ADDED_IN_31
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
        filter=AttributeFilterInput(),
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
        def with_tax_class(data):
            tax_class, manager = data
            tax_data = manager.get_tax_code_from_object_meta(tax_class)
            return TaxType(tax_code=tax_data.code, description=tax_data.description)

        if root.tax_class_id:
            tax_class = TaxClassByIdLoader(info.context).load(root.tax_class_id)
            manager = get_plugin_manager_promise(info.context)
            return Promise.all([tax_class, manager]).then(with_tax_class)

        return None

    @staticmethod
    def resolve_product_attributes(root: models.ProductType, info):
        def unpack_attributes(attributes):
            return [attr for attr, *_ in attributes]

        return (
            ProductAttributesByProductTypeIdLoader(info.context)
            .load(root.pk)
            .then(unpack_attributes)
        )

    @staticmethod
    @traced_resolver
    def resolve_variant_attributes(
        root: models.ProductType,
        info,
        variant_selection: Optional[str] = None,
    ):
        def apply_variant_selection_filter(attributes):
            if not variant_selection or variant_selection == VariantAttributeScope.ALL:
                return [attr for attr, *_ in attributes]
            variant_selection_attrs = get_variant_selection_attributes(attributes)
            if variant_selection == VariantAttributeScope.VARIANT_SELECTION:
                return [attr for attr, *_ in variant_selection_attrs]
            return [
                attr
                for attr, variant_selection in attributes
                if (attr, variant_selection) not in variant_selection_attrs
            ]

        return (
            VariantAttributesByProductTypeIdLoader(info.context)
            .load(root.pk)
            .then(apply_variant_selection_filter)
        )

    @staticmethod
    @traced_resolver
    def resolve_assigned_variant_attributes(
        root: models.ProductType,
        info,
        variant_selection: Optional[str] = None,
    ):
        def apply_variant_selection_filter(attributes):
            if not variant_selection or variant_selection == VariantAttributeScope.ALL:
                return [
                    {"attribute": attr, "variant_selection": variant_selection}
                    for attr, variant_selection in attributes
                ]
            variant_selection_attrs = get_variant_selection_attributes(attributes)
            if variant_selection == VariantAttributeScope.VARIANT_SELECTION:
                return [
                    {"attribute": attr, "variant_selection": variant_selection}
                    for attr, variant_selection in variant_selection_attrs
                ]
            return [
                {"attribute": attr, "variant_selection": variant_selection}
                for attr, variant_selection in attributes
                if (attr, variant_selection) not in variant_selection_attrs
            ]

        return (
            VariantAttributesByProductTypeIdLoader(info.context)
            .load(root.pk)
            .then(apply_variant_selection_filter)
        )

    @staticmethod
    def resolve_products(root: models.ProductType, info, *, channel=None, **kwargs):
        requestor = get_user_or_app_from_context(info.context)
        if channel is None:
            channel = get_default_channel_slug_or_graphql_error()
        qs = root.products.visible_to_user(requestor, channel)
        qs = ChannelQsContext(qs=qs, channel_slug=channel)
        kwargs["channel"] = channel
        return create_connection_slice(qs, info, kwargs, ProductCountableConnection)

    @staticmethod
    def resolve_available_attributes(root: models.ProductType, info, **kwargs):
        qs = attribute_models.Attribute.objects.get_unassigned_product_type_attributes(
            root.pk
        )
        qs = resolve_attributes(info, qs=qs)
        qs = filter_connection_queryset(qs, kwargs, info.context)
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
    def __resolve_references(roots: List["ProductType"], _info):
        return resolve_federation_references(
            ProductType, roots, models.ProductType.objects
        )


class ProductTypeCountableConnection(CountableConnection):
    class Meta:
        node = ProductType


@federated_entity("id")
class ProductMedia(ModelObjectType[models.ProductMedia]):
    id = graphene.GlobalID(required=True)
    sort_order = graphene.Int()
    alt = graphene.String(required=True)
    type = ProductMediaType(required=True)
    oembed_data = JSONString(required=True)
    url = ThumbnailField(graphene.String, required=True)

    class Meta:
        description = "Represents a product media."
        interfaces = [relay.Node]
        model = models.ProductMedia

    @staticmethod
    def resolve_url(root: models.ProductMedia, info, *, size=None, format=None):
        if root.external_url:
            return root.external_url

        if not root.image:
            return

        if not size:
            return build_absolute_uri(root.image.url)

        format = format.lower() if format else None
        size = get_thumbnail_size(size)

        def _resolve_url(thumbnail):
            url = get_image_or_proxy_url(
                thumbnail, str(root.id), "ProductMedia", size, format
            )
            return build_absolute_uri(url)

        return (
            ThumbnailByProductMediaIdSizeAndFormatLoader(info.context)
            .load((root.id, size, format))
            .then(_resolve_url)
        )

    @staticmethod
    def __resolve_references(roots: List["ProductMedia"], _info):
        return resolve_federation_references(
            ProductMedia, roots, models.ProductMedia.objects
        )


class ProductImage(graphene.ObjectType):
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
    url = ThumbnailField(graphene.String, required=True)

    class Meta:
        description = "Represents a product image."

    @staticmethod
    def resolve_id(root: models.ProductMedia, info):
        return graphene.Node.to_global_id("ProductImage", root.id)

    @staticmethod
    def resolve_url(root: models.ProductMedia, info, *, size=None, format=None):
        if not root.image:
            return

        if not size:
            return build_absolute_uri(root.image.url)

        format = format.lower() if format else None
        size = get_thumbnail_size(size)

        def _resolve_url(thumbnail):
            url = get_image_or_proxy_url(
                thumbnail, str(root.id), "ProductMedia", size, format
            )
            return build_absolute_uri(url)

        return (
            ThumbnailByProductMediaIdSizeAndFormatLoader(info.context)
            .load((root.id, size, format))
            .then(_resolve_url)
        )
