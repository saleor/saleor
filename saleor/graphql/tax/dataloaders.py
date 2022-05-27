from collections import defaultdict

from ...tax.models import TaxConfigurationPerCountry
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
