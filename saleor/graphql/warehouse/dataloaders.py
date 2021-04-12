from collections import defaultdict
from typing import DefaultDict, Iterable, List, Optional, Tuple
from uuid import UUID

from django.conf import settings

from ...warehouse.models import Stock, Warehouse
from ..core.dataloaders import DataLoader

CountryCode = Optional[str]
VariantIdAndCountryCode = Tuple[int, CountryCode]


class AvailableQuantityByProductVariantIdCountryCodeAndChannelSlugLoader(
    DataLoader[VariantIdAndCountryCode, int]
):
    """Calculates available variant quantity based on variant ID and country code.

    For each country code, for each shipping zone supporting that country,
    calculate the maximum available quantity, then return either that number
    or the maximum allowed checkout quantity, whichever is lower.
    """

    context_key = "available_quantity_by_productvariant_and_country"

    def batch_load(self, keys):
        # Split the list of keys by country first. A typical query will only touch
        # a handful of unique countries but may access thousands of product variants
        # so it's cheaper to execute one query per country.
        variants_by_country_and_channel: DefaultDict[
            CountryCode, List[int]
        ] = defaultdict(list)
        for variant_id, country_code, channel_slug in keys:
            variants_by_country_and_channel[(country_code, channel_slug)].append(
                variant_id
            )

        # For each country code execute a single query for all product variants.
        quantity_by_variant_and_country: DefaultDict[
            VariantIdAndCountryCode, int
        ] = defaultdict(int)
        for key, variant_ids in variants_by_country_and_channel.items():
            country_code, channel_slug = key
            quantities = self.batch_load_country(
                country_code, channel_slug, variant_ids
            )
            for variant_id, quantity in quantities:
                quantity_by_variant_and_country[
                    (variant_id, country_code, channel_slug)
                ] = quantity

        return [quantity_by_variant_and_country[key] for key in keys]

    def batch_load_country(
        self,
        country_code: CountryCode,
        channel_slug: Optional[str],
        variant_ids: Iterable[int],
    ) -> Iterable[Tuple[int, int]]:
        # get stocks only for warehouses assigned to the shipping zones
        # that are available in the given channel
        results = Stock.objects.filter(product_variant_id__in=variant_ids)
        if country_code:
            results = results.filter(
                warehouse__shipping_zones__countries__contains=country_code
            )
        if channel_slug:
            results = results.filter(
                warehouse__shipping_zones__channels__slug=channel_slug
            )
        results = results.annotate_available_quantity()
        results = results.values_list(
            "product_variant_id", "warehouse__shipping_zones", "available_quantity"
        )

        # A single country code (or a missing country code) can return results from
        # multiple shipping zones. We want to combine all quantities within a single
        # zone and then find out which zone contains the highest total.
        quantity_by_shipping_zone_by_product_variant: DefaultDict[
            int, DefaultDict[int, int]
        ] = defaultdict(lambda: defaultdict(int))
        for variant_id, shipping_zone_id, quantity in results:
            quantity_by_shipping_zone_by_product_variant[variant_id][
                shipping_zone_id
            ] += quantity
        quantity_map: DefaultDict[int, int] = defaultdict(int)
        for (
            variant_id,
            quantity_by_shipping_zone,
        ) in quantity_by_shipping_zone_by_product_variant.items():
            quantity_values = quantity_by_shipping_zone.values()
            if country_code:
                # When country code is known, return the sum of quantities from all
                # shipping zones supporting given country.
                quantity_map[variant_id] = sum(quantity_values)
            else:
                # When country code is unknown, return the highest known quantity.
                quantity_map[variant_id] = max(quantity_values)

        # Return the quantities after capping them at the maximum quantity allowed in
        # checkout. This prevent users from tracking the store's precise stock levels.
        return [
            (
                variant_id,
                min(quantity_map[variant_id], settings.MAX_CHECKOUT_LINE_QUANTITY),
            )
            for variant_id in variant_ids
        ]


class StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChanneLoader(
    DataLoader[VariantIdAndCountryCode, Iterable[Stock]]
):
    """Return stocks with available quantity based on variant ID, country code, channel.

    For each country code, for each shipping zone supporting that country and channel,
    return stocks with maximum available quantity.
    """

    context_key = "stocks_with_available_quantity_by_productvariant_country_and_channel"

    def batch_load(self, keys):
        # Split the list of keys by country first. A typical query will only touch
        # a handful of unique countries but may access thousands of product variants
        # so it's cheaper to execute one query per country.
        variants_by_country: DefaultDict[CountryCode, List[int]] = defaultdict(list)
        for variant_id, country_code, channel_slug in keys:
            variants_by_country[(country_code, channel_slug)].append(variant_id)

        # For each country code execute a single query for all product variants.
        stocks_by_variant_and_country: DefaultDict[
            VariantIdAndCountryCode, Iterable[Stock]
        ] = defaultdict(list)
        for key, variant_ids in variants_by_country.items():
            country_code, channel_slug = key
            variant_ids_stocks = self.batch_load_country(
                country_code, channel_slug, variant_ids
            )
            for variant_id, stocks in variant_ids_stocks:
                stocks_by_variant_and_country[
                    (variant_id, country_code, channel_slug)
                ].extend(stocks)

        return [stocks_by_variant_and_country[key] for key in keys]

    def batch_load_country(
        self,
        country_code: CountryCode,
        channel_slug: Optional[str],
        variant_ids: Iterable[int],
    ) -> Iterable[Tuple[int, List[Stock]]]:
        stocks = Stock.objects.filter(product_variant_id__in=variant_ids)
        if country_code:
            stocks = stocks.filter(
                warehouse__shipping_zones__countries__contains=country_code
            )
        if channel_slug:
            stocks = stocks.filter(
                warehouse__shipping_zones__channels__slug=channel_slug
            )
        stocks = stocks.annotate_available_quantity()

        stocks_by_variant_id_map: DefaultDict[int, List[Stock]] = defaultdict(list)
        for stock in stocks:
            stocks_by_variant_id_map[stock.product_variant_id].append(stock)

        return [
            (
                variant_id,
                stocks_by_variant_id_map[variant_id],
            )
            for variant_id in variant_ids
        ]


class WarehouseByIdLoader(DataLoader):
    context_key = "warehouse_by_id"

    def batch_load(self, keys):
        warehouses = Warehouse.objects.in_bulk(keys)
        return [warehouses.get(UUID(warehouse_uuid)) for warehouse_uuid in keys]
