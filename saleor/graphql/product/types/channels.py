from dataclasses import asdict
from decimal import Decimal
from typing import Optional

import graphene
from promise import Promise

from ....core.utils.country import get_active_country
from ....graphql.core.types import Money, MoneyRange
from ....permission.enums import ProductPermissions
from ....product import models
from ....product.utils.availability import get_product_availability
from ....product.utils.costs import (
    get_margin_for_variant_channel_listing,
    get_product_costs_data,
)
from ....tax.utils import (
    get_display_gross_prices,
    get_tax_calculation_strategy,
    get_tax_rate_for_tax_class,
)
from ...account import types as account_types
from ...channel.dataloaders import ChannelByIdLoader
from ...channel.types import Channel
from ...core.descriptions import ADDED_IN_31, ADDED_IN_33, DEPRECATED_IN_3X_FIELD
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.fields import PermissionsField
from ...core.scalars import Date, DateTime
from ...core.tracing import traced_resolver
from ...core.types import BaseObjectType, ModelObjectType
from ...tax.dataloaders import (
    TaxClassByProductIdLoader,
    TaxClassCountryRateByTaxClassIDLoader,
    TaxClassDefaultRateByCountryLoader,
    TaxConfigurationByChannelId,
    TaxConfigurationPerCountryByTaxConfigurationIDLoader,
)
from ..dataloaders import (
    ProductByIdLoader,
    ProductVariantsByProductIdLoader,
    VariantChannelListingByVariantIdAndChannelSlugLoader,
    VariantsChannelListingByProductIdAndChannelSlugLoader,
)


class Margin(BaseObjectType):
    start = graphene.Int(description="The starting value of the margin.")
    stop = graphene.Int(description="The ending value of the margin.")

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        description = "Metadata for the Margin class."


class ProductChannelListing(ModelObjectType[models.ProductChannelListing]):
    id = graphene.GlobalID(
        required=True, description="The ID of the product channel listing."
    )
    publication_date = Date(
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `publishedAt` field to fetch the publication date."
        ),
    )
    published_at = DateTime(
        description="The product publication date time." + ADDED_IN_33
    )
    is_published = graphene.Boolean(
        required=True,
        description="Indicates if the product is published in the channel.",
    )
    channel = graphene.Field(
        Channel,
        required=True,
        description="The channel in which the product is listed.",
    )
    visible_in_listings = graphene.Boolean(
        required=True,
        description="Indicates product visibility in the channel listings.",
    )
    available_for_purchase = Date(
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `availableForPurchaseAt` field to fetch "
            "the available for purchase date."
        ),
    )
    available_for_purchase_at = DateTime(
        description="The product available for purchase date time." + ADDED_IN_33
    )
    discounted_price = graphene.Field(
        Money, description="The price of the cheapest variant (including discounts)."
    )
    purchase_cost = PermissionsField(
        MoneyRange,
        description="Purchase cost of product.",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    margin = PermissionsField(
        Margin,
        description="Range of margin percentage value.",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    is_available_for_purchase = graphene.Boolean(
        description=(
            "Refers to a state that can be set by admins to control whether a product "
            "is available for purchase in storefronts in this channel. This does not "
            "guarantee the availability of stock. When set to `False`, this product is "
            "still visible to customers, but it cannot be purchased."
        )
    )
    pricing = graphene.Field(
        "saleor.graphql.product.types.products.ProductPricingInfo",
        address=graphene.Argument(
            account_types.AddressInput,
            description=(
                "Destination address used to find warehouses where stock availability "
                "for this product is checked. If address is empty, uses "
                "`Shop.companyAddress` or fallbacks to server's "
                "`settings.DEFAULT_COUNTRY` configuration."
            ),
        ),
        description=(
            "Lists the storefront product's pricing, the current price and discounts, "
            "only meant for displaying."
        ),
    )

    class Meta:
        description = "Represents product channel listing."
        model = models.ProductChannelListing
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_publication_date(root: models.ProductChannelListing, _info):
        return root.published_at

    @staticmethod
    def resolve_available_for_purchase(root: models.ProductChannelListing, _info):
        return root.available_for_purchase_at

    @staticmethod
    def resolve_channel(root: models.ProductChannelListing, info):
        return ChannelByIdLoader(info.context).load(root.channel_id)

    @staticmethod
    @traced_resolver
    def resolve_purchase_cost(root: models.ProductChannelListing, info):
        channel = ChannelByIdLoader(info.context).load(root.channel_id)

        def calculate_margin_with_variants(variants):
            def calculate_margin_with_channel(channel):
                def calculate_margin_with_channel_listings(
                    variant_channel_listings: list[
                        Optional[models.ProductVariantChannelListing]
                    ],
                ):
                    existing_listings = list(filter(None, variant_channel_listings))
                    if not existing_listings:
                        return None

                    has_variants = True if len(variant_ids_channel_slug) > 0 else False
                    purchase_cost, _margin = get_product_costs_data(
                        existing_listings, has_variants, root.currency
                    )
                    return purchase_cost

                variant_ids_channel_slug = [
                    (variant.id, channel.slug) for variant in variants
                ]
                return (
                    VariantChannelListingByVariantIdAndChannelSlugLoader(info.context)
                    .load_many(variant_ids_channel_slug)
                    .then(calculate_margin_with_channel_listings)
                )

            return channel.then(calculate_margin_with_channel)

        return (
            ProductVariantsByProductIdLoader(info.context)
            .load(root.product_id)
            .then(calculate_margin_with_variants)
        )

    @staticmethod
    @traced_resolver
    def resolve_margin(root: models.ProductChannelListing, info):
        channel = ChannelByIdLoader(info.context).load(root.channel_id)

        def calculate_margin_with_variants(variants):
            def calculate_margin_with_channel(channel):
                def calculate_margin_with_channel_listings(
                    variant_channel_listings: list[
                        Optional[models.ProductVariantChannelListing]
                    ],
                ):
                    existing_listings = list(filter(None, variant_channel_listings))
                    if not existing_listings:
                        return None

                    has_variants = True if len(variant_ids_channel_slug) > 0 else False
                    _purchase_cost, margin = get_product_costs_data(
                        existing_listings, has_variants, root.currency
                    )
                    return Margin(margin[0], margin[1])

                variant_ids_channel_slug = [
                    (variant.id, channel.slug) for variant in variants
                ]
                return (
                    VariantChannelListingByVariantIdAndChannelSlugLoader(info.context)
                    .load_many(variant_ids_channel_slug)
                    .then(calculate_margin_with_channel_listings)
                )

            return channel.then(calculate_margin_with_channel)

        return (
            ProductVariantsByProductIdLoader(info.context)
            .load(root.product_id)
            .then(calculate_margin_with_variants)
        )

    @staticmethod
    def resolve_is_available_for_purchase(root: models.ProductChannelListing, _info):
        return root.is_available_for_purchase()

    @staticmethod
    def resolve_pricing(root: models.ProductChannelListing, info, *, address=None):
        context = info.context

        channel = ChannelByIdLoader(context).load(root.channel_id)
        product = ProductByIdLoader(context).load(root.product_id)

        def load_tax_configuration(data):
            channel, product = data
            country_code = get_active_country(channel, address_data=address)

            def load_tax_country_exceptions(tax_config):
                tax_class = TaxClassByProductIdLoader(info.context).load(product.id)
                tax_configs_per_country = (
                    TaxConfigurationPerCountryByTaxConfigurationIDLoader(context).load(
                        tax_config.id
                    )
                )

                def load_variant_channel_listings(data):
                    tax_class, tax_configs_per_country = data

                    def load_default_tax_rate(variants_channel_listing):
                        if not variants_channel_listing:
                            return None

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
                            tax_rate = get_tax_rate_for_tax_class(
                                tax_class, country_rates, default_tax_rate, country_code
                            )
                            prices_entered_with_tax = tax_config.prices_entered_with_tax

                            availability = get_product_availability(
                                product_channel_listing=root,
                                variants_channel_listing=variants_channel_listing,
                                prices_entered_with_tax=prices_entered_with_tax,
                                tax_calculation_strategy=tax_calculation_strategy,
                                tax_rate=tax_rate,
                            )
                            from .products import ProductPricingInfo

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
                        default_country_rate = TaxClassDefaultRateByCountryLoader(
                            context
                        ).load(country_code)
                        return Promise.all([country_rates, default_country_rate]).then(
                            calculate_pricing_info
                        )

                    return (
                        VariantsChannelListingByProductIdAndChannelSlugLoader(context)
                        .load((root.product_id, channel.slug))
                        .then(load_default_tax_rate)
                    )

                return Promise.all([tax_class, tax_configs_per_country]).then(
                    load_variant_channel_listings
                )

            return (
                TaxConfigurationByChannelId(context)
                .load(channel.id)
                .then(load_tax_country_exceptions)
            )

        return Promise.all([channel, product]).then(load_tax_configuration)


class PreorderThreshold(BaseObjectType):
    quantity = graphene.Int(
        required=False,
        description="Preorder threshold for product variant in this channel.",
    )
    sold_units = graphene.Int(
        required=True,
        description="Number of sold product variant in this channel.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        description = "Represents preorder variant data for channel."


class ProductVariantChannelListing(
    ModelObjectType[models.ProductVariantChannelListing]
):
    id = graphene.GlobalID(
        required=True, description="The ID of the variant channel listing."
    )
    channel = graphene.Field(
        Channel,
        required=True,
        description="The channel to which the variant listing belongs.",
    )
    price = graphene.Field(Money, description="The price of the variant.")
    cost_price = graphene.Field(Money, description="Cost price of the variant.")
    margin = PermissionsField(
        graphene.Int,
        description="Gross margin percentage value.",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    preorder_threshold = graphene.Field(
        PreorderThreshold,
        required=False,
        description="Preorder variant data." + ADDED_IN_31,
    )

    class Meta:
        description = "Represents product variant channel listing."
        model = models.ProductVariantChannelListing
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_channel(root: models.ProductVariantChannelListing, info):
        return ChannelByIdLoader(info.context).load(root.channel_id)

    @staticmethod
    def resolve_margin(root: models.ProductVariantChannelListing, _info):
        return get_margin_for_variant_channel_listing(root)

    @staticmethod
    def resolve_preorder_threshold(root: models.ProductVariantChannelListing, _info):
        # The preorder_quantity_allocated field is added through annotation
        # when using the `resolve_channel_listings` resolver.
        return PreorderThreshold(
            quantity=root.preorder_quantity_threshold,
            sold_units=getattr(root, "preorder_quantity_allocated", 0),
        )


class CollectionChannelListing(ModelObjectType[models.CollectionChannelListing]):
    id = graphene.GlobalID(
        required=True, description="The ID of the collection channel listing."
    )
    publication_date = Date(
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `publishedAt` field to fetch the publication date."
        ),
    )
    published_at = DateTime(
        description="The collection publication date." + ADDED_IN_33
    )
    is_published = graphene.Boolean(
        required=True,
        description="Indicates if the collection is published in the channel.",
    )
    channel = graphene.Field(
        Channel,
        required=True,
        description="The channel to which the collection belongs.",
    )

    class Meta:
        description = "Represents collection channel listing."
        model = models.CollectionChannelListing
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_publication_date(root: models.ProductChannelListing, _info):
        return root.published_at

    @staticmethod
    def resolve_channel(root: models.ProductChannelListing, info):
        return ChannelByIdLoader(info.context).load(root.channel_id)
