from ....tax import TaxCalculationStrategy
from ....tax.models import TaxConfiguration


def create_channel_tax_configuration(channel):
    # Use TAX_APP strategy, to enable calculations with plugins by default.
    tax_configuration = TaxConfiguration.objects.create(
        channel=channel,
        metadata={"key": "value"},
        private_metadata={"key": "value"},
        tax_calculation_strategy=TaxCalculationStrategy.TAX_APP,
    )
    tax_configuration.country_exceptions.create(
        country="PL",
        tax_calculation_strategy=TaxCalculationStrategy.TAX_APP,
    )
    tax_configuration.country_exceptions.create(
        country="DE",
        tax_calculation_strategy=TaxCalculationStrategy.TAX_APP,
    )
