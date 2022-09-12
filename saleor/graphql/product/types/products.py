import sys
from collections import defaultdict
from dataclasses import asdict
from typing import List, Optional

import graphene
from django_countries.fields import Country
from graphene import relay

from ....attribute import models as attribute_models
from ....core.permissions import (
    AuthorizationFilters,
    OrderPermissions,
    ProductPermissions,
    has_one_of_permissions,
)
from ....core.tracing import traced_resolver
from ....core.utils import get_currency_for_country
from ....core.weight import convert_weight_to_default_weight_unit
from ....product import models
from ....product.models import ALL_PRODUCTS_PERMISSIONS
from ....product.utils import calculate_revenue_for_variant
from ....product.utils.availability import (
    get_product_availability,
    get_variant_availability,
)
from ....product.utils.variants import get_variant_selection_attributes
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
from ...discount.dataloaders import DiscountsByDateTimeLoader
from ...meta.types import ObjectWithMetadata
from ...order.dataloaders import (
    OrderByIdLoader,
    OrderLinesByVariantIdAndChannelIdLoader,
)
from ...product.dataloaders.products import (
    AvailableProductVariantsByProductIdAndChannel,
    ProductVariantsByProductIdAndChannel,
)
from ...site.dataloaders import load_site
from ...translations.fields import TranslationField
from ...translations.types import (
    CategoryTranslation,
    CollectionTranslation,
    ProductTranslation,
    ProductVariantTranslation,
)
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
    CategoryChildrenByCategoryIdLoader,
    CollectionChannelListingByCollectionIdAndChannelSlugLoader,
    CollectionChannelListingByCollectionIdLoader,
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
    ThumbnailByCategoryIdSizeAndFormatLoader,
    ThumbnailByCollectionIdSizeAndFormatLoader,
    ThumbnailByProductMediaIdSizeAndFormatLoader,
    VariantAttributesByProductTypeIdLoader,
    VariantChannelListingByVariantIdAndChannelSlugLoader,
    VariantChannelListingByVariantIdLoader,
    VariantsChannelListingByProductIdAndChannelSlugLoader,
)
from ..enums import ProductMediaType, ProductTypeKindEnum, VariantAttributeScope
from ..filters import ProductFilterInput
from ..resolvers import resolve_product_variants, resolve_products
from ..sorters import ProductOrder
from .channels import (
    CollectionChannelListing,
    ProductChannelListing,
    ProductVariantChannelListing,
)
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
class ProductVariant(ChannelContextTypeWithMetadata, ModelObjectType):
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
    def resolve_quantity_available(
        root: ChannelContext[models.ProductVariant],
        info,
        address=None,
        country_code=None,
    ):
        if address is not None:
            country_code = address.country
        site = load_site(info.context)
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

        address_country = address.country if address is not None else None

        def calculate_pricing_info(discounts):
            def calculate_pricing_with_channel(channel):
                def calculate_pricing_with_product_variant_channel_listings(
                    variant_channel_listing,
                ):
                    def calculate_pricing_with_product(product):
                        def calculate_pricing_with_product_channel_listings(
                            product_channel_listing,
                        ):
                            def calculate_pricing_with_collections(collections):
                                if (
                                    not variant_channel_listing
                                    or not product_channel_listing
                                ):
                                    return None

                                country_code = (
                                    address_country or channel.default_country.code
                                )

                                local_currency = None
                                local_currency = get_currency_for_country(country_code)

                                availability = get_variant_availability(
                                    variant=root.node,
                                    variant_channel_listing=variant_channel_listing,
                                    product=product,
                                    product_channel_listing=product_channel_listing,
                                    collections=collections,
                                    discounts=discounts,
                                    channel=channel,
                                    country=Country(country_code),
                                    local_currency=local_currency,
                                    plugins=context.plugins,
                                )
                                return VariantPricingInfo(**asdict(availability))

                            return collections.then(calculate_pricing_with_collections)

                        return product_channel_listing.then(
                            calculate_pricing_with_product_channel_listings
                        )

                    return product.then(calculate_pricing_with_product)

                return variant_channel_listing.then(
                    calculate_pricing_with_product_variant_channel_listings
                )

            return channel.then(calculate_pricing_with_channel)

        return (
            DiscountsByDateTimeLoader(context)
            .load(info.context.request_time)
            .then(calculate_pricing_info)
        )

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
class Product(ChannelContextTypeWithMetadata, ModelObjectType):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    name = graphene.String(required=True)
    description = JSONString(description="Description of the product." + RICH_CONTENT)
    product_type = graphene.Field(lambda: ProductType, required=True)
    slug = graphene.String(required=True)
    category = graphene.Field(lambda: Category)
    created = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    charge_taxes = graphene.Boolean(required=True)
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
        TaxType, description="A type of tax. Assigned by enabled tax gateway"
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
        description="List of media for the product.",
    )
    images = NonNullList(
        lambda: ProductImage,
        description="List of images for the product.",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use the `media` field instead.",
    )
    collections = NonNullList(
        lambda: Collection,
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
    available_for_purchase = graphene.Date(
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
        tax_data = info.context.plugins.get_tax_code_from_object_meta(root.node)
        return TaxType(tax_code=tax_data.code, description=tax_data.description)

    @staticmethod
    @traced_resolver
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
                return Image(alt=image.alt, url=info.context.build_absolute_uri(url))

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
        channel = ChannelBySlugLoader(context).load(channel_slug)

        address_country = address.country if address is not None else None

        def calculate_pricing_info(discounts):
            def calculate_pricing_with_channel(channel):
                def calculate_pricing_with_product_channel_listings(
                    product_channel_listing,
                ):
                    def calculate_pricing_with_variants(variants):
                        def calculate_pricing_with_variants_channel_listings(
                            variants_channel_listing,
                        ):
                            def calculate_pricing_with_collections(collections):
                                if not variants_channel_listing:
                                    return None

                                local_currency = None
                                country_code = (
                                    address_country or channel.default_country.code
                                )
                                local_currency = get_currency_for_country(country_code)

                                availability = get_product_availability(
                                    product=root.node,
                                    product_channel_listing=product_channel_listing,
                                    variants=variants,
                                    variants_channel_listing=variants_channel_listing,
                                    collections=collections,
                                    discounts=discounts,
                                    channel=channel,
                                    manager=context.plugins,
                                    country=Country(country_code),
                                    local_currency=local_currency,
                                )
                                return ProductPricingInfo(**asdict(availability))

                            return collections.then(calculate_pricing_with_collections)

                        return variants_channel_listing.then(
                            calculate_pricing_with_variants_channel_listings
                        )

                    return variants.then(calculate_pricing_with_variants)

                return product_channel_listing.then(
                    calculate_pricing_with_product_channel_listings
                )

            return channel.then(calculate_pricing_with_channel)

        return (
            DiscountsByDateTimeLoader(context)
            .load(info.context.request_time)
            .then(calculate_pricing_info)
        )

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
    def resolve_media(root: ChannelContext[models.Product], info):
        return MediaByProductIdLoader(info.context).load(root.node.id)

    @staticmethod
    def resolve_images(root: ChannelContext[models.Product], info):
        return ImagesByProductIdLoader(info.context).load(root.node.id)

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
    @traced_resolver
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
    @traced_resolver
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
    @traced_resolver
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
class ProductType(ModelObjectType):
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
        TaxType, description="A type of tax. Assigned by enabled tax gateway"
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
        tax_data = info.context.plugins.get_tax_code_from_object_meta(root)
        return TaxType(tax_code=tax_data.code, description=tax_data.description)

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
        qs = root.products.visible_to_user(requestor, channel)  # type: ignore
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
    def __resolve_references(roots: List["ProductType"], _info):
        return resolve_federation_references(
            ProductType, roots, models.ProductType.objects
        )


class ProductTypeCountableConnection(CountableConnection):
    class Meta:
        node = ProductType


@federated_entity("id channel")
class Collection(ChannelContextTypeWithMetadata, ModelObjectType):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    name = graphene.String(required=True)
    description = JSONString(
        description="Description of the collection." + RICH_CONTENT
    )
    slug = graphene.String(required=True)
    channel = graphene.String(
        description=(
            "Channel given to retrieve this collection. Also used by federation "
            "gateway to resolve this object in a federated query."
        ),
    )
    description_json = JSONString(
        description="Description of the collection." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    products = FilterConnectionField(
        ProductCountableConnection,
        filter=ProductFilterInput(description="Filtering options for products."),
        sort_by=ProductOrder(description="Sort products."),
        description="List of products in this collection.",
    )
    background_image = ThumbnailField()
    translation = TranslationField(
        CollectionTranslation,
        type_name="collection",
        resolver=ChannelContextType.resolve_translation,
    )
    channel_listings = PermissionsField(
        NonNullList(CollectionChannelListing),
        description="List of channels in which the collection is available.",
        permissions=[
            ProductPermissions.MANAGE_PRODUCTS,
        ],
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = "Represents a collection of products."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Collection

    @staticmethod
    def resolve_channel(root: ChannelContext[models.Product], _info):
        return root.channel_slug

    @staticmethod
    def resolve_background_image(
        root: ChannelContext[models.Collection], info, size=None, format=None
    ):
        node = root.node
        if not node.background_image:
            return

        alt = node.background_image_alt
        if not size:
            return Image(url=node.background_image.url, alt=alt)

        format = format.lower() if format else None
        size = get_thumbnail_size(size)

        def _resolve_background_image(thumbnail):
            url = get_image_or_proxy_url(thumbnail, node.id, "Collection", size, format)
            return Image(url=url, alt=alt)

        return (
            ThumbnailByCollectionIdSizeAndFormatLoader(info.context)
            .load((node.id, size, format))
            .then(_resolve_background_image)
        )

    @staticmethod
    def resolve_products(root: ChannelContext[models.Collection], info, **kwargs):
        requestor = get_user_or_app_from_context(info.context)
        qs = root.node.products.visible_to_user(  # type: ignore
            requestor, root.channel_slug
        )
        qs = ChannelQsContext(qs=qs, channel_slug=root.channel_slug)

        kwargs["channel"] = root.channel_slug
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, ProductCountableConnection)

    @staticmethod
    def resolve_channel_listings(root: ChannelContext[models.Collection], info):
        return CollectionChannelListingByCollectionIdLoader(info.context).load(
            root.node.id
        )

    @staticmethod
    def resolve_description_json(root: ChannelContext[models.Collection], _info):
        description = root.node.description
        return description if description is not None else {}

    @staticmethod
    def __resolve_references(roots: List["Collection"], info):
        from ..resolvers import resolve_collections

        channels = defaultdict(set)
        roots_ids = []
        for root in roots:
            _, root_id = from_global_id_or_error(root.id, Collection, raise_error=True)
            roots_ids.append(f"{root.channel}_{root_id}")
            channels[root.channel].add(root_id)

        collections = {}
        for channel, ids in channels.items():
            queryset = resolve_collections(info, channel).qs.filter(id__in=ids)

            for collection in queryset:
                collections[f"{channel}_{collection.id}"] = ChannelContext(
                    channel_slug=channel, node=collection
                )

        return [collections.get(root_id) for root_id in roots_ids]


class CollectionCountableConnection(CountableConnection):
    class Meta:
        node = Collection


@federated_entity("id")
class Category(ModelObjectType):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    name = graphene.String(required=True)
    description = JSONString(description="Description of the category." + RICH_CONTENT)
    slug = graphene.String(required=True)
    parent = graphene.Field(lambda: Category)
    level = graphene.Int(required=True)
    description_json = JSONString(
        description="Description of the category." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    ancestors = ConnectionField(
        lambda: CategoryCountableConnection,
        description="List of ancestors of the category.",
    )
    products = ConnectionField(
        ProductCountableConnection,
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description=(
            "List of products in the category. Requires the following permissions to "
            "include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
    )
    children = ConnectionField(
        lambda: CategoryCountableConnection,
        description="List of children of the category.",
    )
    background_image = ThumbnailField()
    translation = TranslationField(CategoryTranslation, type_name="category")

    class Meta:
        description = (
            "Represents a single category of products. Categories allow to organize "
            "products in a tree-hierarchies which can be used for navigation in the "
            "storefront."
        )
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Category

    @staticmethod
    def resolve_ancestors(root: models.Category, info, **kwargs):
        return create_connection_slice(
            root.get_ancestors(), info, kwargs, CategoryCountableConnection
        )

    @staticmethod
    def resolve_description_json(root: models.Category, _info):
        description = root.description
        return description if description is not None else {}

    @staticmethod
    def resolve_background_image(root: models.Category, info, size=None, format=None):
        if not root.background_image:
            return

        alt = root.background_image_alt
        if not size:
            return Image(url=root.background_image.url, alt=alt)

        format = format.lower() if format else None
        size = get_thumbnail_size(size)

        def _resolve_background_image(thumbnail):
            url = get_image_or_proxy_url(thumbnail, root.id, "Category", size, format)
            return Image(url=url, alt=alt)

        return (
            ThumbnailByCategoryIdSizeAndFormatLoader(info.context)
            .load((root.id, size, format))
            .then(_resolve_background_image)
        )

    @staticmethod
    def resolve_children(root: models.Category, info, **kwargs):
        def slice_children_categories(children):
            return create_connection_slice(
                children, info, kwargs, CategoryCountableConnection
            )

        return (
            CategoryChildrenByCategoryIdLoader(info.context)
            .load(root.pk)
            .then(slice_children_categories)
        )

    @staticmethod
    def resolve_url(root: models.Category, _info):
        return ""

    @staticmethod
    @traced_resolver
    def resolve_products(root: models.Category, info, *, channel=None, **kwargs):
        requestor = get_user_or_app_from_context(info.context)
        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )
        tree = root.get_descendants(include_self=True)
        if channel is None and not has_required_permissions:
            channel = get_default_channel_slug_or_graphql_error()
        qs = models.Product.objects.all()
        if not has_required_permissions:
            qs = (
                qs.visible_to_user(requestor, channel)
                .annotate_visible_in_listings(channel)
                .exclude(
                    visible_in_listings=False,
                )
            )
        if channel and has_required_permissions:
            qs = qs.filter(channel_listings__channel__slug=channel)
        qs = qs.filter(category__in=tree)
        qs = ChannelQsContext(qs=qs, channel_slug=channel)
        return create_connection_slice(qs, info, kwargs, ProductCountableConnection)

    @staticmethod
    def __resolve_references(roots: List["Category"], _info):
        return resolve_federation_references(Category, roots, models.Category.objects)


class CategoryCountableConnection(CountableConnection):
    class Meta:
        node = Category


@federated_entity("id")
class ProductMedia(ModelObjectType):
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
            return info.context.build_absolute_uri(root.image.url)

        format = format.lower() if format else None
        size = get_thumbnail_size(size)

        def _resolve_url(thumbnail):
            url = get_image_or_proxy_url(
                thumbnail, root.id, "ProductMedia", size, format
            )
            return info.context.build_absolute_uri(url)

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
            return info.context.build_absolute_uri(root.image.url)

        format = format.lower() if format else None
        size = get_thumbnail_size(size)

        def _resolve_url(thumbnail):
            url = get_image_or_proxy_url(
                thumbnail, root.id, "ProductMedia", size, format
            )
            return info.context.build_absolute_uri(url)

        return (
            ThumbnailByProductMediaIdSizeAndFormatLoader(info.context)
            .load((root.id, size, format))
            .then(_resolve_url)
        )
