import pytest
from django_countries import countries

from ...plugins.avatax import (
    DEFAULT_TAX_CODE,
    META_CODE_KEY,
    META_DESCRIPTION_KEY,
    TAX_CODE_NON_TAXABLE_PRODUCT,
)
from ..models import TaxClass, TaxClassCountryRate


@pytest.fixture(autouse=True)
def default_tax_class(db):
    tax_class, _ = TaxClass.objects.get_or_create(
        name="Default",
        defaults={
            "metadata": {
                META_CODE_KEY: DEFAULT_TAX_CODE,
                META_DESCRIPTION_KEY: "Default tax code",
            },
            "private_metadata": {
                META_CODE_KEY: DEFAULT_TAX_CODE,
                META_DESCRIPTION_KEY: "Default tax code",
            },
        },
    )
    TaxClassCountryRate.objects.bulk_create(
        [
            TaxClassCountryRate(country="PL", rate=23, tax_class=tax_class),
            TaxClassCountryRate(country="DE", rate=19, tax_class=tax_class),
        ]
    )
    return tax_class


@pytest.fixture
def tax_classes(db):
    objects = []
    for name in ["Books", "Groceries"]:
        tax_class, _ = TaxClass.objects.get_or_create(
            name=name,
            defaults={
                "metadata": {"key": "value"},
                "private_metadata": {"key": "value"},
            },
        )
        TaxClassCountryRate.objects.bulk_create(
            [
                TaxClassCountryRate(country="PL", rate=23, tax_class=tax_class),
                TaxClassCountryRate(country="DE", rate=19, tax_class=tax_class),
            ]
        )
        objects.append(tax_class)
    return objects


@pytest.fixture
def tax_class_zero_rates(db):
    zero_rate_tax_class = TaxClass.objects.create(
        name="No taxes",
        metadata={
            META_CODE_KEY: TAX_CODE_NON_TAXABLE_PRODUCT,
            META_DESCRIPTION_KEY: "Non-taxable product",
        },
    )

    # Create 0% rates for all countries
    rates = [
        TaxClassCountryRate(tax_class=zero_rate_tax_class, rate=0, country=code)
        for code in countries.countries.keys()
    ]
    TaxClassCountryRate.objects.bulk_create(rates)
    return zero_rate_tax_class
