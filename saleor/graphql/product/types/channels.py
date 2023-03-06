from dataclasses import asdict
from decimal import Decimal
from typing import List, Optional

import graphene
from promise import Promise

from ....core.utils import get_currency_for_country
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
from ...core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_33,
    DEPRECATED_IN_3X_FIELD,
    PREVIEW_FEATURE,
)
from ...core.fields import PermissionsField
from ...core.scalars import Date
from ...core.tracing import traced_resolver
from ...core.types import ModelObjectType
from ...discount.dataloaders import DiscountsByDateTimeLoader
from ...tax.dataloaders import (
    TaxClassByProductIdLoader,
    TaxClassCountryRateByTaxClassIDLoader,
    TaxClassDefaultRateByCountryLoader,
    TaxConfigurationByChannelId,
    TaxConfigurationPerCountryByTaxConfigurationIDLoader,
)
from ..dataloaders import (
    CollectionsByProductIdLoader,
    ProductByIdLoader,
    ProductVariantsByProductIdLoader,
    VariantChannelListingByVariantIdAndChannelSlugLoader,
    VariantsChannelListingByProductIdAndChannelSlugLoader,
)


class Margin(graphene.ObjectType):
    start = graphene.Int()
    stop = graphene.Int()


class ProductChannelListing(ModelObjectType[models.ProductChannelListing]):
    id = graphene.GlobalID(required=True)
    publication_date = Date(
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `publishedAt` field to fetch the publication date."
        ),
    )
    published_at = graphene.DateTime(
        description="The product publication date time." + ADDED_IN_33
    )
    is_published = graphene.Boolean(required=True)
    channel = graphene.Field(Channel, required=True)
    visible_in_listings = graphene.Boolean(required=True)
    available_for_purchase = Date(
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `availableForPurchaseAt` field to fetch "
            "the available for purchase date."
        ),
    )
    available_for_purchase_at = graphene.DateTime(
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
        description="Whether the product is available for purchase."
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
                    variant_channel_listings: List[
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
                    variant_channel_listings: List[
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
        address_country = address.country if address is not None else None

        channel = ChannelByIdLoader(context).load(root.channel_id)
        product = ProductByIdLoader(context).load(root.product_id)
        variants = ProductVariantsByProductIdLoader(context).load(root.product_id)
        collections = CollectionsByProductIdLoader(context).load(root.product_id)
        discounts = DiscountsByDateTimeLoader(context).load(info.context.request_time)

        def load_tax_configuration(data):
            channel, product, variants, collections, discounts = data
            country_code = address_country or channel.default_country.code

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
                            prices_entered_with_tax = tax_config.prices_entered_with_tax

                            availability = get_product_availability(
                                product=product,
                                product_channel_listing=root,
                                variants=variants,
                                variants_channel_listing=variants_channel_listing,
                                collections=collections,
                                discounts=discounts,
                                channel=channel,
                                local_currency=local_currency,
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

        return Promise.all([channel, product, variants, collections, discounts]).then(
            load_tax_configuration
        )


class PreorderThreshold(graphene.ObjectType):
    quantity = graphene.Int(
        required=False,
        description="Preorder threshold for product variant in this channel.",
    )
    sold_units = graphene.Int(
        required=True,
        description="Number of sold product variant in this channel.",
    )

    class Meta:
        description = "Represents preorder variant data for channel."


class ProductVariantChannelListing(
    ModelObjectType[models.ProductVariantChannelListing]
):
    id = graphene.GlobalID(required=True)
    channel = graphene.Field(Channel, required=True)
    price = graphene.Field(Money)
    cost_price = graphene.Field(Money, description="Cost price of the variant.")
    margin = PermissionsField(
        graphene.Int,
        description="Gross margin percentage value.",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )
    preorder_threshold = graphene.Field(
        PreorderThreshold,
        required=False,
        description="Preorder variant data." + ADDED_IN_31 + PREVIEW_FEATURE,
    )

    class Meta:
        description = "Represents product varaint channel listing."
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
    id = graphene.GlobalID(required=True)
    publication_date = Date(
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `publishedAt` field to fetch the publication date."
        ),
    )
    published_at = graphene.DateTime(
        description="The collection publication date." + ADDED_IN_33
    )
    is_published = graphene.Boolean(required=True)
    channel = graphene.Field(Channel, required=True)

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
