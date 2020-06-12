import pytest
from django_prices_vatlayer.models import VAT
from django_prices_vatlayer.utils import get_tax_for_rate

from ..base_plugin import ConfigurationTypeField
from ..models import PluginConfiguration
from .sample_plugins import PluginInactive, PluginSample


@pytest.fixture
def plugin_configuration(db):
    configuration, _ = PluginConfiguration.objects.get_or_create(
        identifier=PluginSample.PLUGIN_ID,
        name=PluginSample.PLUGIN_NAME,
        defaults={
            "active": PluginSample.DEFAULT_ACTIVE,
            "configuration": PluginSample.DEFAULT_CONFIGURATION,
            "name": PluginSample.PLUGIN_NAME,
        },
    )
    configuration.refresh_from_db()
    return configuration


@pytest.fixture
def inactive_plugin_configuration(db):
    return PluginConfiguration.objects.get_or_create(
        identifier=PluginSample.PLUGIN_ID,
        name=PluginInactive.PLUGIN_NAME,
        defaults={
            "active": PluginInactive.DEFAULT_ACTIVE,
            "configuration": PluginInactive.DEFAULT_CONFIGURATION,
            "name": PluginInactive.PLUGIN_NAME,
        },
    )[0]


@pytest.fixture
def new_config():
    return {"name": "Foo", "value": "bar"}


@pytest.fixture
def new_config_structure():
    return {"type": ConfigurationTypeField.STRING, "help_text": "foo", "label": "foo"}


@pytest.fixture
def tax_rates():
    return {
        "standard_rate": 23,
        "reduced_rates": {
            "pharmaceuticals": 8,
            "medical": 8,
            "passenger transport": 8,
            "newspapers": 8,
            "hotels": 8,
            "restaurants": 8,
            "admission to cultural events": 8,
            "admission to sporting events": 8,
            "admission to entertainment events": 8,
            "foodstuffs": 5,
        },
    }


@pytest.fixture
def taxes(tax_rates):
    taxes = {
        "standard": {
            "value": tax_rates["standard_rate"],
            "tax": get_tax_for_rate(tax_rates),
        }
    }
    if tax_rates["reduced_rates"]:
        taxes.update(
            {
                rate: {
                    "value": tax_rates["reduced_rates"][rate],
                    "tax": get_tax_for_rate(tax_rates, rate),
                }
                for rate in tax_rates["reduced_rates"]
            }
        )
    return taxes


@pytest.fixture
def vatlayer(db, tax_rates, taxes, setup_vatlayer):
    VAT.objects.create(country_code="PL", data=tax_rates)

    tax_rates_2 = {
        "standard_rate": 19,
        "reduced_rates": {
            "admission to cultural events": 7,
            "admission to entertainment events": 7,
            "books": 7,
            "foodstuffs": 7,
            "hotels": 7,
            "medical": 7,
            "newspapers": 7,
            "passenger transport": 7,
        },
    }
    VAT.objects.create(country_code="DE", data=tax_rates_2)
    return taxes
