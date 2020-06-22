from collections import defaultdict
from typing import DefaultDict, Iterable, List, Optional, Tuple

from django.conf import settings

from ...warehouse.models import Stock
from ..core.dataloaders import DataLoader

CountryCode = Optional[str]
VariantIdAndCountryCode = Tuple[int, CountryCode]


class AvailableQuantityByProductVariantIdAndCountryCodeLoader(
    DataLoader[VariantIdAndCountryCode, int]
):
    """Calculates available variant quantity based on variant ID and country code.

    For each country code, for each shipping zone supporting that country,
    calculate the maximum available quantity, then return either that number
    or the maximum allowed checkout quantity, whichever is lower.
    """

    context_key = "stock_by_productvariant_and_country"

    def batch_load(self, keys):
        # Split the list of keys by country first. A typical query will only touch
        # a handful of unique countries but may access thousands of product variants
        # so it's cheaper to execute one query per country.
        variants_by_country: DefaultDict[CountryCode, List[int]] = defaultdict(list)
        for variant_id, country_code in keys:
            variants_by_country[country_code].append(variant_id)

        # For each country code execute a single query for all product variants.
        quantity_by_variant_and_country: DefaultDict[
            VariantIdAndCountryCode, int
        ] = defaultdict(int)
        for country_code, variant_ids in variants_by_country.items():
            quantities = self.batch_load_country(country_code, variant_ids)
            for variant_id, quantity in quantities:
                quantity_by_variant_and_country[(variant_id, country_code)] = quantity

        return [quantity_by_variant_and_country[key] for key in keys]

    def batch_load_country(
        self, country_code: CountryCode, variant_ids: Iterable[int]
    ) -> Iterable[Tuple[int, int]]:
        results = Stock.objects.filter(product_variant_id__in=variant_ids)
        if country_code:
            results.filter(warehouse__shipping_zones__countries__contains=country_code)
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
            quantity_map[variant_id] = max(quantity_by_shipping_zone.values())

        # Return the quantities after capping them at the maximum quantity allowed in
        # checkout. This prevent users from tracking the store's precise stock levels.
        return [
            (
                variant_id,
                min(quantity_map[variant_id], settings.MAX_CHECKOUT_LINE_QUANTITY),
            )
            for variant_id in variant_ids
        ]
