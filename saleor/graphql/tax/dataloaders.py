from collections import defaultdict
from decimal import Decimal

from django.db.models import Exists, OuterRef
from promise import Promise

from ...tax.models import (
    TaxClass,
    TaxClassCountryRate,
    TaxConfiguration,
    TaxConfigurationPerCountry,
)
from ..core.dataloaders import DataLoader
from ..product.dataloaders import (
    ProductByIdLoader,
    ProductByVariantIdLoader,
    ProductTypeByProductIdLoader,
    ProductTypeByVariantIdLoader,
)


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


class TaxClassDefaultRateByCountryLoader(DataLoader):
    context_key = "tax_class_default_rate_by_country"

    def batch_load(self, keys):
        tax_rates = TaxClassCountryRate.objects.using(
            self.database_connection_name
        ).filter(tax_class=None, country__in=keys)
        tax_rates_map = {rate.country: rate for rate in tax_rates}
        return [tax_rates_map.get(key) for key in keys]


class TaxClassByIdLoader(DataLoader):
    context_key = "tax_class_by_id"

    def batch_load(self, keys):
        tax_class_map = TaxClass.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [tax_class_map.get(obj_id) for obj_id in keys]


class TaxClassByProductIdLoader(DataLoader):
    context_key = "tax_class_by_product_id"

    def batch_load(self, keys):
        products = ProductByIdLoader(self.context).load_many(keys)
        product_types = ProductTypeByProductIdLoader(self.context).load_many(keys)

        def load_tax_classes(results):
            (products, product_types) = results
            products_map = dict(zip(keys, products))
            product_types_map = dict(zip(keys, product_types))

            tax_class_ids_map = {}
            for product_id in keys:
                product = products_map[product_id]
                product_type = product_types_map[product_id]
                tax_class_id = product.tax_class_id or product_type.tax_class_id
                tax_class_ids_map[product_id] = tax_class_id

            return [
                TaxClassByIdLoader(self.context).load(tax_class_ids_map[product_id])
                if tax_class_ids_map[product_id]
                else None
                for product_id in keys
            ]

        return Promise.all([products, product_types]).then(load_tax_classes)


class TaxClassByVariantIdLoader(DataLoader):
    context_key = "tax_class_by_variant_id"

    def batch_load(self, keys):
        products = ProductByVariantIdLoader(self.context).load_many(keys)
        product_types = ProductTypeByVariantIdLoader(self.context).load_many(keys)

        def load_tax_classes(results):
            (products, product_types) = results
            products_map = dict(zip(keys, products))
            product_types_map = dict(zip(keys, product_types))

            tax_class_ids_map = {}
            for variant_pk in keys:
                product = products_map[variant_pk]
                product_type = product_types_map[variant_pk]
                tax_class_id = product.tax_class_id or product_type.tax_class_id
                tax_class_ids_map[variant_pk] = tax_class_id

            return [
                TaxClassByIdLoader(self.context).load(tax_class_ids_map[variant_id])
                if tax_class_ids_map[variant_id]
                else None
                for variant_id in keys
            ]

        return Promise.all([products, product_types]).then(load_tax_classes)


class ProductChargeTaxesByTaxClassIdLoader(DataLoader):
    # Deprecated: this dataloader is used only for deprecated `Product.chargeTaxes`
    # and `ProductType.chargeTaxes` fields and it only reflects flat tax rates, while it
    # ignores any tax apps. To determine whether to charge taxes, one should look into
    # TaxConfiguration of a channel.

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
