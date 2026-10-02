import sys
from dataclasses import asdict
from decimal import Decimal

import graphene
from promise import Promise

from ....core.db.connection import allow_writer_in_context
from ....core.utils.country import get_active_country
from ....product import models
from ....product.utils.availability import get_variant_availability
from ....tax.utils import (
    get_tax_calculation_strategy,
    get_tax_rate_for_country,
)
from ....warehouse.reservations import is_reservation_enabled
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.types import BaseObjectType, TaxedMoney, TaxedMoneyRange
from ...tax.dataloaders import (
    TaxClassCountryRateByTaxClassIDLoader,
    TaxClassDefaultRateByCountryLoader,
    TaxConfigurationByChannelId,
    TaxConfigurationPerCountryByTaxConfigurationIDLoader,
)
from ...warehouse.dataloaders import (
    AvailableQuantityByProductVariantIdAndChannelSlugLoader,
    AvailableQuantityByProductVariantIdCountryCodeAndChannelSlugLoader,
    PreorderQuantityReservedByVariantChannelListingIdLoader,
)
from ..dataloaders import (
    VariantChannelListingByVariantIdAndChannelSlugLoader,
    VariantChannelListingByVariantIdLoader,
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
    price_prior = graphene.Field(TaxedMoney, description="The price prior to discount.")

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
        description="The prior price range of the product variants.",
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


def get_variant_quantity_available(
    info,
    variant: models.ProductVariant,
    channel_slug: str | None,
    site,
    country_code=None,
):
    """Resolve the quantity of a variant available for sale in one checkout."""
    with allow_writer_in_context(info.context):
        global_quantity_limit_per_checkout = site.settings.limit_quantity_per_checkout

    if variant.is_preorder_active():
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
                                    global_quantity_limit_per_checkout or sys.maxsize,
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

    if not variant.track_inventory:
        return global_quantity_limit_per_checkout

    include_shipping_zones = site.settings.use_legacy_shipping_zone_stock_availability
    if include_shipping_zones:
        return AvailableQuantityByProductVariantIdCountryCodeAndChannelSlugLoader(
            info.context
        ).load((variant.id, country_code, channel_slug))
    return AvailableQuantityByProductVariantIdAndChannelSlugLoader(info.context).load(
        (variant.id, channel_slug)
    )


def get_variant_pricing_info(context, data, address):
    """Build `VariantPricingInfo` from loaded listings, channel and tax class."""
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
                    VariantPricingInfo(**asdict(availability)) if availability else None
                )

            country_rates = (
                TaxClassCountryRateByTaxClassIDLoader(context).load(tax_class_id)
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
