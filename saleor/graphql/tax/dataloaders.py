from collections import defaultdict
from decimal import Decimal

from django.db.models import Exists, OuterRef

from ...tax.models import (
    TaxClass,
    TaxClassCountryRate,
    TaxConfiguration,
    TaxConfigurationPerCountry,
)
from ..core.dataloaders import DataLoader


class TaxConfigurationPerCountryByTaxConfigurationIDLoader(DataLoader):
    context_key = "tax_configuration_per_country_by_tax_configuration_id"

    def batch_load(self, keys):
        tax_configs_per_country = TaxConfigurationPerCountry.objects.using(
            self.database_connection_name
        ).filter(tax_configuration_id__in=keys)

        one_to_many = defaultdict(list)
        for obj in tax_configs_per_country:
            one_to_many[obj.tax_configuration_id].append(obj)

        return [one_to_many[key] for key in keys]


class TaxConfigurationByChannelId(DataLoader):
    context_key = "tax_configuration_by_channel_id"

    def batch_load(self, keys):
        tax_configs = TaxConfiguration.objects.using(
            self.database_connection_name
        ).in_bulk(keys, field_name="channel_id")
        return [tax_configs[key] for key in keys]


class TaxClassCountryRateByTaxClassIDLoader(DataLoader):
    context_key = "tax_class_country_rate_by_tax_class_id"

    def batch_load(self, keys):
        tax_rates = TaxClassCountryRate.objects.using(
            self.database_connection_name
        ).filter(tax_class_id__in=keys)

        one_to_many = defaultdict(list)
        for obj in tax_rates:
            one_to_many[obj.tax_class_id].append(obj)

        return [one_to_many[key] for key in keys]


class TaxClassByIdLoader(DataLoader):
    context_key = "tax_class_by_id"

    def batch_load(self, keys):
        tax_class_map = TaxClass.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [tax_class_map.get(obj_id) for obj_id in keys]


class ProductChargeTaxesByTaxClassIdLoader(DataLoader):
    context_key = "product_charge_taxes_by_tax_class_id"

    def batch_load(self, keys):
        non_zero_rates = TaxClassCountryRate.objects.filter(
            tax_class=OuterRef("pk")
        ).exclude(rate=Decimal(0))
        tax_class_map = (
            TaxClass.objects.using(self.database_connection_name)
            .filter(pk__in=keys)
            .annotate(charge_taxes=Exists(non_zero_rates))
            .in_bulk(keys)
        )
        return [
            tax_class_map[tax_class_id].charge_taxes
            if tax_class_map.get(tax_class_id)
            else False
            for tax_class_id in keys
        ]
