from collections import defaultdict
from typing import DefaultDict, Iterable, List, Optional, Tuple

from django.conf import settings
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce

from ...warehouse.models import Stock
from ..core.dataloaders import DataLoader

CountryCode = Optional[str]
VariantIdAndCountryCode = Tuple[int, CountryCode]


class AvailableQuantityByProductVariantIdAndCountryCodeLoader(DataLoader):
    context_key = "stock_by_productvariant_and_country"

    def batch_load(self, keys: Iterable[VariantIdAndCountryCode]) -> List[int]:
        country_map: DefaultDict[CountryCode, List[int]] = defaultdict(list)
        for variant_id, country_code in keys:
            country_map[country_code].append(variant_id)
        quantity_map: DefaultDict[VariantIdAndCountryCode, int] = defaultdict(int)
        for country_code, variant_ids in country_map.items():
            quantities = self.batch_load_country(country_code, variant_ids)
            for variant_id, quantity in quantities:
                quantity_map[(variant_id, country_code)] = quantity
        return [quantity_map[key] for key in keys]

    def batch_load_country(
        self, country_code: CountryCode, variant_ids: Iterable[int]
    ) -> Iterable[Tuple[int, int]]:
        query = Q(product_variant_id__in=variant_ids)
        if country_code:
            query &= Q(warehouse__shipping_zones__countries__contains=country_code)
        stocks = (
            Stock.objects.filter(query)
            .annotate(
                available_quantity=Sum("quantity", distinct=True)
                - Coalesce(Sum("allocations__quantity_allocated"), 0),
            )
            .values_list(
                "product_variant_id", "warehouse__shipping_zones", "available_quantity"
            )
        )
        variant_map: DefaultDict[int, DefaultDict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for variant_id, shipping_zone_id, quantity in stocks:
            variant_map[variant_id][shipping_zone_id] += quantity
        quantity_map: DefaultDict[int, int] = defaultdict(int)
        for variant_id, shipping_zone_quantities in variant_map.items():
            quantity_map[variant_id] = max(shipping_zone_quantities.values())
        return [
            (
                variant_id,
                min(quantity_map[variant_id], settings.MAX_CHECKOUT_LINE_QUANTITY),
            )
            for variant_id in variant_ids
        ]
