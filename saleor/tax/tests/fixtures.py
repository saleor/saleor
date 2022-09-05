import pytest

from ..models import TaxClass, TaxClassCountryRate


@pytest.fixture(autouse=True)
def default_tax_class(db):
    tax_class, _ = TaxClass.objects.get_or_create(
        is_default=True,
        name="Default",
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
